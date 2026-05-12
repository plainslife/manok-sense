# Manoksense

A portable image vision device that captures photos of raw chicken meat and
classifies them as **edible**, **spoiled**, or **adulterated** using a
MobileNetV2/EfficientNet TFLite model running directly on a Raspberry Pi.
The device features a live camera preview on a touchscreen display, a
multi-photo capture flow, a gallery for reviewing past results, and an
optional distance sensor to guide the user to the correct capture distance.

---

## Hardware

- Raspberry Pi (32-bit, Debian Trixie)
- ILI9341 SPI Touchscreen Display (320×240)
- XPT2046 Touch Controller
- OV5647 Camera Module (via Picamera2)
- NeoPixel LED Strip (×4)
- VL53L1X Time-of-Flight Distance Sensor (optional)

## Tech Stack

- Python 3.13 — main application
- Python 3.11 (separate venv) — TFLite inference worker
- Picamera2 + libcamera — camera capture and streaming
- Luma LCD — ILI9341 display driver
- Adafruit CircuitPython — LED and distance sensor libraries
- Pillow — image drawing and compositing
- TFLite Runtime — on-device model inference
- EfficientNetB2 / MobileNetV2 — classification model backbone

---

## File Structure

```
manoksense/
├── config.py               # All hardware pins, UI layout, and app constants
├── main.py                 # Entry point — boots hardware and runs the state machine
├── inference_bridge.py     # Sends frames to the inference worker via Unix socket
├── inference_worker.py     # Runs TFLite inference in a separate Python 3.11 process
├── settings.json           # Auto-generated — persists user preferences between sessions
├── STYLE.md                # Coding conventions and style rules
├── SETUP.md                # Full installation and setup guide
├── fonts/
│   ├── DejaVuSans.ttf
│   └── DejaVuSans-Bold.ttf
├── models/                 # TFLite model files (.tflite)
├── captures/               # Saved classified images (label_timestamp_NofTotal.jpg)
└── src/
    ├── __init__.py
    ├── boot.py             # Hardware initialisation sequence with animated progress screen
    ├── capture.py          # Image save orchestration and filename generation
    ├── classifier.py       # TFLite model wrapper — preprocessing, inference, dequantization
    ├── context.py          # AppContext — shared hardware refs and mutable state for all states
    ├── gallery_store.py    # Gallery file management — save, list sessions, make thumbnails
    ├── settings_store.py   # Load and save user preferences to settings.json
    ├── hardware/           # Thin wrappers around physical hardware
    │   ├── __init__.py
    │   ├── camera.py       # Picamera2 — frame grab, lores preview, full-res capture
    │   ├── distance.py     # VL53L1X — time-of-flight distance measurement
    │   ├── led.py          # NeoPixel — status and result indicator LED
    │   └── touch.py        # XPT2046 — touch input reading and hit-testing
    ├── ui/                 # Everything rendered on screen
    │   ├── __init__.py
    │   ├── animation.py    # Multi-frame sequences — boot steps, capture progress
    │   ├── color.py        # UI color palette — single source of truth for all colors
    │   ├── display.py      # ILI9341 device, canvas drawing, live preview overlay
    │   └── helpers.py      # Shared drawing utilities — font loading, standard header
    ├── states/             # One file per app state — each owns its own screen and logic
    │   ├── __init__.py
    │   ├── preview.py      # Live camera feed — shutter, settings, gallery navigation
    │   ├── capture.py      # Multi-photo collection — tap shutter N times to collect
    │   ├── process.py      # Runs inference, saves to gallery, transitions to result
    │   ├── result.py       # Shows classification result with frame navigation
    │   ├── settings.py     # Sensor toggle, camera/LED reload, power off
    │   ├── gallery.py      # 3×3 thumbnail grid with page navigation
    │   └── gallery_preview.py  # Single session viewer with delete confirmation
    └── drivers/            # Self-written hardware drivers
        ├── __init__.py
        └── xpt2046_driver.py   # XPT2046 SPI touch driver with calibration and scaling
```

---

## How It Works

The app runs as a **state machine** — at any moment it is in exactly one state
(preview, capturing, processing, result, settings, or gallery), and each state
owns its own screen rendering and touch handling logic. Transitions between
states are driven by user input and hardware events. All shared hardware
references and mutable data flow through a single `AppContext` object so no
state ever needs more than one parameter.

Model inference runs in a **separate Python 3.11 process** via `inference_worker.py`
because `tflite-runtime` is not yet available for Python 3.13. The main app
sends captured frames to the worker over a Unix socket through `inference_bridge.py`
and receives the classification result back, keeping the main UI loop responsive
while inference runs in the background.

---

## Getting Started

See [SETUP.md](SETUP.md) for the full installation guide including system
dependencies, virtual environment setup, font installation, and hardware
verification steps.

To run the application (sudo is required for NeoPixel LED hardware access):

```bash
sudo venv/bin/python main.py
```

---

## Contributing

Please read [STYLE.md](STYLE.md) before contributing to keep the codebase
consistent. Key conventions: one responsibility per file, hardware in
`src/hardware/`, screen rendering in `src/states/` alongside the state logic
that uses it, and all constants in `config.py`.
