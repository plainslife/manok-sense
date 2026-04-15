# src/capture.py -> filepath(filename?) generation for saving to image

import time 
import os
from .camera import Camera
from config import CAPTURE_DIR, CAPTURE_PREFIX, DEBOUNCE_SECS


# create a folder if it doesn't exist
def _ensure_dir() -> None:
    os.makedirs(CAPTURE_DIR, exist_ok=True)

# create unique filename -> returns full filepath of the created filename
def generate_filename(save_dir: str) -> str:
    os.makedirs(f"{CAPTURE_DIR}/{save_dir}/", exist_ok=True)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{CAPTURE_PREFIX}_{timestamp}.jpg"
    filepath = os.path.join(f"{CAPTURE_DIR}/{save_dir}/", filename)

    return filepath

# continuous capture
def continuous(cam: Camera, save_dir: str, capture_count: int = 5) -> None:
    for i in range(capture_count):
        filepath = generate_filename(save_dir)
        cam.save(filepath)
        print(f"Image Saved -> {filepath}")

        # give time for the capture and ensure unique filename
        time.sleep(1)

# single capture
def single(cam: Camera, save_dir: str) -> None:
    filepath = generate_filename(save_dir)
    cam.save(filepath)
    print(f"Image Saved -> {filepath}")

    # give time for the camear and ensure unique filename
    time.sleep(1)
