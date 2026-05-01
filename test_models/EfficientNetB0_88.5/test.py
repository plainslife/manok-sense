#!/usr/bin/env python3

import argparse
import time
import numpy as np
import cv2
import onnxruntime as ort

# ── config ────────────────────────────────────────────────────────────────────
MODEL_PATH  = "chicken_classifier2.onnx"
CLASS_NAMES = ["adulterated", "edible", "spoiled"]
IMG_SIZE    = (224, 224)

COLORS = {
    "adulterated": "\033[91m",
    "edible":      "\033[92m",
    "spoiled":     "\033[93m",
    "reset":       "\033[0m",
}

# ── load model ────────────────────────────────────────────────────────────────
session = ort.InferenceSession(MODEL_PATH)
input_name = session.get_inputs()[0].name


# ── inference ────────────────────────────────────────────────────────────────
def predict(image):
    start = time.time()

    if isinstance(image, str):
        img = cv2.imread(image)
    else:
        img = image

    img = cv2.resize(img, IMG_SIZE)
    img = img.astype(np.float32) / 255.0

    # HWC → CHW
    img = np.transpose(img, (2, 0, 1))
    img = np.expand_dims(img, axis=0)

    output = session.run(None, {input_name: img})[0][0]

    probs = softmax(output)
    idx = int(np.argmax(probs))

    label = CLASS_NAMES[idx]
    conf = float(probs[idx])

    ms = (time.time() - start) * 1000

    return label, conf, probs, ms


# ── softmax ───────────────────────────────────────────────────────────────────
def softmax(x):
    e = np.exp(x - np.max(x))
    return e / e.sum()


# ── print result ──────────────────────────────────────────────────────────────
def print_result(label, confidence, probs, ms):
    c = COLORS.get(label, "")
    r = COLORS["reset"]

    print(f"\n{'='*38}")
    print(f"  Result     : {c}{label.upper()}{r}")
    print(f"  Confidence : {confidence:.1%}")
    print(f"  Inference  : {ms:.1f} ms")
    print(f"{'='*38}")

    for name, p in zip(CLASS_NAMES, probs):
        bar = "█" * int(p * 25)
        clr = COLORS.get(name, "")
        print(f"  {clr}{name:<12} {p:>5.1%}  {bar}{r}")
    print()


# ── image test ────────────────────────────────────────────────────────────────
def test_image(path):
    print(f"Image: {path}")
    label, conf, probs, ms = predict(path)
    print_result(label, conf, probs, ms)


# ── camera test ───────────────────────────────────────────────────────────────
def test_camera():
    print("Capturing from Pi Camera...")

    from picamera2 import Picamera2

    cam = Picamera2()
    cam.configure(cam.create_preview_configuration(
        main={"size": (640, 480), "format": "RGB888"}
    ))
    cam.start()
    time.sleep(1.5)

    frame = cam.capture_array("main")
    cam.stop()
    cam.close()

    label, conf, probs, ms = predict(frame)
    print_result(label, conf, probs, ms)

    cv2.imwrite("test_capture.jpg", cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
    print("Capture saved -> test_capture.jpg")


# ── main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Path to image")
    args = parser.parse_args()

    if args.image:
        test_image(args.image)
    else:
        test_camera()
