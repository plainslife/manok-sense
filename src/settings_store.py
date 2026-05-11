# src/settings.py — load/save user settings to settings.json

import json
import os

_SETTINGS_FILE = "settings.json"

_DEFAULTS: dict = {
    "distance_enabled": False,
}

# remember klast settings (if distance sensor is turned on/off)
def load() -> dict:
    try:
        with open(_SETTINGS_FILE) as f:
            data = json.load(f)
        return {**_DEFAULTS, **data}
    except (FileNotFoundError, json.JSONDecodeError):
        return _DEFAULTS.copy()

def save(data: dict) -> None:
    try:
        with open(_SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except OSError as e:
        print(f"[Settings] Failed to save: {e}")
