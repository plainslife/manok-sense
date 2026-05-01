#!/usr/bin/env python3
"""
Chicken Freshness Classifier — Raspberry Pi Zero 2W
Requires: tflite-runtime, opencv-python, numpy
Install : pip install tflite-runtime opencv-python numpy
Usage   : python3 classify.py --image photo.jpg
          python3 classify.py --camera        (live Pi Camera capture)
"""
import argparse
import time
import numpy as np

# Use tflite-runtime (lightweight, no full TensorFlow needed on Pi)
try:
    from tflite_runtime.interpreter import Interpreter
except ImportError:
    from tensorflow.lite.python.interpreter import Interpreter

import cv2

MODEL_PATH  = "chicken_classifier_int8.tflite"
CLASS_NAMES = ["adulterated", "edible", "spoiled"]
IMG_SIZE    = (224, 224)

# Colour coding for terminal output
COLORS = {
    "adulterated": "\033[91m",   # red
    "edible":      "\033[92m",   # green
    "spoiled":     "\033[93m",   # yellow
    "reset":       "\033[0m"
}

def load_model(path):
    interp = Interpreter(model_path=path)
    interp.allocate_tensors()
    return interp, interp.get_input_details(), interp.get_output_details()


def preprocess(image_bgr, input_details):
    """Resize, convert BGR→RGB. Float16/dynamic models take float32 input."""
    img = cv2.resize(image_bgr, IMG_SIZE)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    return np.expand_dims(img.astype(np.float32), axis=0)

def predict(interp, input_details, output_details, image_bgr):
    inp = preprocess(image_bgr, input_details)
    interp.set_tensor(input_details[0]["index"], inp)
    t0  = time.time()
    interp.invoke()
    ms  = (time.time() - t0) * 1000
    out = interp.get_tensor(output_details[0]["index"])[0]

    # Dequantize uint8 → float probabilities
    out_scale = output_details[0]["quantization"][0]
    out_zp    = output_details[0]["quantization"][1]
    probs     = (out.astype(np.float32) - out_zp) * out_scale

    label = CLASS_NAMES[np.argmax(probs)]
    conf  = float(np.max(probs))
    return label, conf, probs, ms

def print_result(label, conf, probs):
    c = COLORS.get(label, "")
    r = COLORS["reset"]
    print(f"\n{'='*35}")
    print(f"  Result : {c}{label.upper()}{r}")
    print(f"  Confidence : {conf:.1%}")
    print(f"{'='*35}")
    for name, p in zip(CLASS_NAMES, probs):
        bar = "█" * int(p * 30)
        print(f"  {name:<12} {p:>5.1%}  {bar}")
    print()

def classify_image(path):
    img = cv2.imread(path)
    if img is None:
        print(f"Error: cannot read {path}"); return
    interp, inp_d, out_d = load_model(MODEL_PATH)
    label, conf, probs, ms = predict(interp, inp_d, out_d, img)
    print_result(label, conf, probs)
    print(f"  Inference time: {ms:.0f} ms")

def classify_camera():
    """Capture one frame from Pi Camera and classify."""
    import subprocess, tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        tmp = f.name
    # Use libcamera-still (Pi OS Bullseye+) for a quick capture
    subprocess.run(
        ["libcamera-still", "-o", tmp, "--width", "224", "--height", "224",
         "--nopreview", "-t", "200"],
        check=True, capture_output=True
    )
    img = cv2.imread(tmp)
    os.unlink(tmp)
    if img is None:
        print("Camera capture failed"); return
    interp, inp_d, out_d = load_model(MODEL_PATH)
    label, conf, probs, ms = predict(interp, inp_d, out_d, img)
    print_result(label, conf, probs)
    print(f"  Inference time: {ms:.0f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Chicken freshness classifier")
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--image",  help="Path to image file")
    group.add_argument("--camera", action="store_true", help="Capture from Pi Camera")
    args = parser.parse_args()
    if args.camera:
        classify_camera()
    else:
        classify_image(args.image)
