import argparse
import sys
from pathlib import Path

import cv2

SIZE = (100, 100)  # Fisherface needs every image the same size
ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Capture face images")
    parser.add_argument("--name", required=True, help="person's name")
    parser.add_argument("--count", type=int, default=30)
    args = parser.parse_args()

    name = args.name.strip().lower().replace(" ", "_")
    out_dir = ROOT / "datasets" / "development" / name
    out_dir.mkdir(parents=True, exist_ok=True)

    cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    if cascade.empty():
        sys.exit("Could not load the face detector file.")

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap.isOpened():
        sys.exit("Webcam could not be opened. Close other apps using it.")

    saved = len(list(out_dir.glob("*.png")))
    target = saved + args.count
    print("Click the video window. SPACE = save, Q = quit.")

    while saved < target:
        ok, frame = cap.read()
        if not ok:
            print("Failed to read from webcam.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = cascade.detectMultiScale(
            gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80)
        )

        shown = frame.copy()
        for (x, y, w, h) in faces:
            cv2.rectangle(shown, (x, y), (x + w, y + h), (0, 255, 0), 2)
        status = f"{name}: {saved}/{target} faces={len(faces)}"
        cv2.putText(shown, status, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        cv2.imshow("FORTRESS capture", shown)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        if key == ord(" "):
            if len(faces) != 1:
                print("Need exactly one face in view. Not saved.")
                continue
            x, y, w, h = faces[0]
            face = cv2.resize(gray[y:y + h, x:x + w], SIZE)
            face = cv2.equalizeHist(face)
            path = out_dir / f"{name}_{saved:03d}.png"
            cv2.imwrite(str(path), face)
            saved += 1
            print("Saved", path.name)

    cap.release()
    cv2.destroyAllWindows()
    print(f"Done. {saved} images in {out_dir}")


if __name__ == "__main__":
    main()