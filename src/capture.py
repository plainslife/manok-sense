# src/capture.py -> filepath(filename?) generation for saving to image

import time 
import os
from config import CAPTURE_DIR, CAPTURE_PREFIX

# create a folder if it doesn't exist
def _ensure_dir() -> None:
    os.makedirs(CAPTURE_DIR, exist_ok=True)

# create unique filename 
def generate_filename() -> str:
    _ensure_dir()

    timestap = time.strftime("%Y%m%d_%H%M%S")
    base = os.path.join(CAPTURE_DIR, f"{CAPTURE_PREFIX}_{timestap}")
    filepath = f"{base}.jpg"

    while os.path.exists(filepath):
        filepath = "f{base}_{counter}.jpg"

    return filepath

