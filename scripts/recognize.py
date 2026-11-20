import json
import sys
from pathlib import Path

import cv2

ROOT = Path(__file__).resolve().parent.parent
MODEL_DIR = ROOT / "models" / "fisherface"
SIZE = (100, 100)


def latest_version():
    versions = sorted(p for p in MODEL_DIR.iterdir() if p.is_dir())
    if not versions:
        sys.exit("No trained model. Run train_fisherface.py first.")
    return versions[-1]


def main():
    folder = latest_version()
    meta = json.loads((folder / "metadata.json").read_text())
    names, threshold = meta["people"], meta["threshold"]

    model = cv2.face.FisherFaceRecognizer_create()
    model.read(str(folder / "fisherface.xml"))
    print("Model:", meta["version"], "| threshold:", round(threshold, 1))

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        sys.exit("Webcam could not be opened.")
    print("Press Q to quit.")

    while True:
        ok, frame = cap.read()
        if not ok:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
        )
        for (x, y, w, h) in faces:
            face = cv2.resize(gray[y:y + h, x:x + w], SIZE)
            face = cv2.equalizeHist(face)
            label, dist = model.predict(face)
            if dist <= threshold:
                text, color = f"{names[label]} d={dist:.0f}", (0, 255, 0)
            else:
                text, color = f"UNKNOWN d={dist:.0f}", (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            cv2.putText(frame, text, (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        cv2.imshow("FORTRESS recognize", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()