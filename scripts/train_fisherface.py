
import argparse
import hashlib
import json
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "datasets" / "development"
MODEL_DIR = ROOT / "models" / "fisherface"
SIZE = (100, 100)
SEED = 42


def load_folder(folder):
    images = []
    for path in sorted(folder.glob("*.png")):
        img = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if img is None:
            print("Skipping unreadable:", path.name)
            continue
        if img.shape != (SIZE[1], SIZE[0]):
            img = cv2.resize(img, SIZE)
        images.append(img)
    return images


def split_three(images):
    """60% train, 20% validation, 20% test. Split per person."""
    train, rest = train_test_split(images, test_size=0.4, random_state=SEED)
    val, test = train_test_split(rest, test_size=0.5, random_state=SEED)
    return train, val, test


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unknown", default=None,
                        help="folder name of a person NOT used in training, "
                             "used as impostor to measure FAR")
    args = parser.parse_args()

    if not hasattr(cv2, "face"):
        raise SystemExit("cv2.face missing. Install opencv-contrib-python only.")

    folders = sorted(p for p in DATA.iterdir() if p.is_dir())
    known = [f for f in folders if f.name != args.unknown]
    if len(known) < 2:
        raise SystemExit("Need at least 2 known people to train Fisherface.")

    names = [f.name for f in known]
    X_train, y_train = [], []
    val, test = [], []  # lists of (image, label)

    for label, folder in enumerate(known):
        imgs = load_folder(folder)
        if len(imgs) < 15:
            raise SystemExit(f"{folder.name} has only {len(imgs)} images. Need 15+.")
        tr, va, te = split_three(imgs)
        X_train += tr
        y_train += [label] * len(tr)
        val += [(i, label) for i in va]
        test += [(i, label) for i in te]
        print(f"{folder.name}: train={len(tr)} val={len(va)} test={len(te)}")

    imp_val, imp_test = [], []
    if args.unknown:
        imps = load_folder(DATA / args.unknown)
        half = len(imps) // 2
        imp_val, imp_test = imps[:half], imps[half:]
        print(f"unknown '{args.unknown}': val={len(imp_val)} test={len(imp_test)}")

    model = cv2.face.FisherFaceRecognizer_create()
    t0 = time.time()
    model.train(X_train, np.array(y_train, dtype=np.int32))
    print(f"Trained in {time.time() - t0:.2f}s")

    # Threshold calibration on VALIDATION genuine samples only
    genuine = []
    for img, label in val:
        pred, dist = model.predict(img)
        if pred == label:
            genuine.append(dist)
    if not genuine:
        raise SystemExit("No correct validation predictions. Capture better images.")
    threshold = float(np.percentile(genuine, 95))
    print(f"Threshold (95th percentile of genuine val distances): {threshold:.1f}")

    # Final evaluation on TEST set (never used for training or threshold)
    y_true, y_pred, latencies = [], [], []
    for img, label in test:
        t1 = time.perf_counter()
        pred, dist = model.predict(img)
        latencies.append((time.perf_counter() - t1) * 1000)
        y_true.append(label)
        y_pred.append(pred if dist <= threshold else -1)

    impostor_accepted = 0
    for img in imp_test:
        pred, dist = model.predict(img)
        y_true.append(-1)
        y_pred.append(pred if dist <= threshold else -1)
        if dist <= threshold:
            impostor_accepted += 1

    genuine_total = len(test)
    genuine_ok = sum(1 for t, p in zip(y_true[:genuine_total], y_pred[:genuine_total]) if t == p)
    frr = 1 - genuine_ok / genuine_total
    far = (impostor_accepted / len(imp_test)) if imp_test else None
    labels_order = list(range(len(names))) + ([-1] if imp_test else [])
    cm = confusion_matrix(y_true, y_pred, labels=labels_order)

    print("\n--- TEST RESULTS ---")
    print("Accuracy:", round(accuracy_score(y_true, y_pred), 3))
    print("FRR (genuine not accepted correctly):", round(frr, 3))
    print("FAR (impostor accepted):", "n/a (no --unknown given)" if far is None else round(far, 3))
    print("Mean latency per prediction (ms):", round(float(np.mean(latencies)), 2))
    print("Confusion matrix rows=true, cols=pred, order =", labels_order, "(-1 = unknown)")
    print(cm)

    # Save versioned model + metadata
    version = datetime.now().strftime("v_%Y%m%d_%H%M%S")
    out = MODEL_DIR / version
    out.mkdir(parents=True, exist_ok=True)
    model_path = out / "fisherface.xml"
    model.write(str(model_path))
    sha = hashlib.sha256(model_path.read_bytes()).hexdigest()
    meta = {
        "version": version, "people": names, "image_size": SIZE,
        "threshold": threshold, "model_sha256": sha,
        "test_accuracy": float(accuracy_score(y_true, y_pred)),
        "frr": frr, "far": far, "seed": SEED,
        "note": "Distances are not probabilities.",
    }
    (out / "metadata.json").write_text(json.dumps(meta, indent=2))
    print("\nSaved:", out)


if __name__ == "__main__":
    main()