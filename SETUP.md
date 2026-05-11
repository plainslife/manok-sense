# Manoksense — Setup Guide

Complete installation guide for setting up the Manoksense device on a Raspberry Pi
running Debian Trixie (32-bit).

---

## System Requirements

- Raspberry Pi 4 or 5
- Raspberry Pi OS based on Debian **Trixie** (32-bit, armv7l)
- Python 3.13 — default system Python, used for the main app
- Python 3.11 — required separately for TFLite inference
- At least 2GB of free storage

### Why Two Python Versions?

`tflite-runtime` is a compiled native extension — its internal binary code is built
specifically for Python 3.11's memory layout. Loading it inside a Python 3.13 process
causes a crash because 3.13's internals are structured differently. The solution is to
run the inference code in its own separate process under Python 3.11, which communicates
back to the main 3.13 app via a Unix socket. This is exactly what `inference_bridge.py`
and `inference_worker.py` do — the main app never touches TFLite directly.

---

## Step 1 — Enable Required Interfaces

```bash
sudo raspi-config
```

Navigate to **Interface Options** and enable each of the following:

- **Camera** — for Picamera2
- **SPI** — for the ILI9341 display and XPT2046 touch screen
- **I2C** — for the VL53L1X distance sensor

Reboot after enabling:

```bash
sudo reboot
```

---

## Step 2 — Install System-Level Dependencies

These packages must be installed at the system level because they require
low-level hardware access that cannot be pip-installed inside a venv on
Raspberry Pi OS. They will be accessible inside both venvs via
`--system-site-packages`.

```bash
sudo apt update && sudo apt upgrade -y

# Camera support
sudo apt install -y python3-picamera2 libcamera-dev

# GPIO and hardware interfaces
sudo apt install -y python3-rpi.gpio python3-spidev python3-smbus2

# Core libraries
sudo apt install -y python3-pil python3-numpy python3-venv

# Python 3.11 alongside the default 3.13
sudo apt install -y python3.11 python3.11-venv
```

---

## Step 3 — Set I2C Speed for VL53L1X Distance Sensor

```bash
sudo nano /boot/firmware/config.txt
```

Add these two lines — each on its own line:

```
dtparam=i2c_arm=on
dtparam=i2c_arm_baudrate=50000
```

Reboot to apply:

```bash
sudo reboot
```

---

## Step 4 — Create the Main App Virtual Environment (Python 3.13)

The main app runs under Python 3.13. The `--system-site-packages` flag allows
the venv to access system-installed packages like Picamera2 and RPi.GPIO which
cannot be pip-installed on Raspberry Pi OS.

```bash
cd ~/Documents/manoksense

python3 -m venv venv --system-site-packages
```

Verify the Python version inside the venv — it should show 3.13.x:

```bash
venv/bin/python --version
```

Activate and install the main app dependencies:

```bash
source venv/bin/activate

pip install \
    adafruit-blinka \
    adafruit-circuitpython-neopixel \
    adafruit-circuitpython-vl53l1x \
    adafruit-extended-bus \
    adafruit-circuitpython-busdevice \
    "cbor2<6.0" \
    luma.lcd \
    luma.core \
    spidev \
    Pillow

deactivate
```

---

## Step 5 — Create the Inference Virtual Environment (Python 3.11)

The inference worker runs under Python 3.11 because `tflite-runtime` is only
available for Python up to 3.11. This venv is kept completely separate so the
two Python versions never conflict. The main app launches the inference worker
as a subprocess and communicates with it over a Unix socket.

```bash
python3.11 -m venv venv311 --system-site-packages
```

Verify the Python version inside this venv — it should show 3.11.x:

```bash
venv311/bin/python --version
```

Activate and install the inference dependencies:

```bash
source venv311/bin/activate

# numpy must stay below 2.0 — tflite-runtime was compiled against numpy 1.x
# Installing it here ensures the venv uses 1.x even if the system has 2.x
pip install "numpy<2"

pip install tflite-runtime Pillow

deactivate
```

Make sure `inference_bridge.py` points to this venv's Python binary:

```python
# inference_bridge.py
WORKER_PYTHON = "venv311/bin/python"
```

---

## Step 6 — Install Fonts

```bash
mkdir -p fonts

cp /usr/share/fonts/truetype/dejavu/DejaVuSans.ttf fonts/
cp /usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf fonts/
```

---

## Step 7 — Add Your TFLite Model

Place your trained `.tflite` model inside `test_models/` and update `MODEL_PATH`
in `config.py` to point to it:

```python
# config.py
MODEL_PATH = "/home/manok/Documents/manoksense/test_models/your_model.tflite"
```

---

## Running the Application

`sudo` is required because NeoPixel LED control needs direct GPIO access:

```bash
sudo venv/bin/python main.py
```

---

## Verifying the Setup

Confirm each piece of hardware is detected before running the full app:

```bash
# Distance sensor — should show 0x29 in the grid
sudo i2cdetect -y 1

# Camera — should list your camera module (e.g. ov5647)
libcamera-hello --list-cameras

# Standalone distance sensor test
sudo venv/bin/python tools/test_sensor.py

# Confirm tflite loads correctly in the inference venv
venv311/bin/python -c "import tflite_runtime; print('TFLite OK:', tflite_runtime.__version__)"
```

---

## Full Library Reference

### Main App — Python 3.13 venv

| Library | Purpose | Install via |
|---------|---------|-------------|
| `picamera2` | Camera capture and streaming | System (`apt`) |
| `libcamera` | Low-level camera pipeline | System (`apt`) |
| `RPi.GPIO` | GPIO hardware access | System (`apt`) |
| `numpy` | Array operations for YUV frame conversion | System (`apt`) |
| `adafruit-blinka` | CircuitPython hardware layer (`board`, `busio`) | `pip` |
| `adafruit-circuitpython-neopixel` | NeoPixel LED control | `pip` |
| `adafruit-circuitpython-vl53l1x` | VL53L1X distance sensor | `pip` |
| `adafruit-circuitpython-extended-bus` | Explicit I2C bus selection | `pip` |
| `adafruit-circuitpython-busdevice` | I2C/SPI device abstraction | `pip` |
| `luma.lcd` | ILI9341 display driver | `pip` |
| `luma.core` | Luma rendering core | `pip` |
| `spidev` | SPI communication for XPT2046 touch driver | `pip` |
| `Pillow` | Image creation, drawing, and compositing | `pip` |

### Inference Worker — Python 3.11 venv

| Library | Purpose | Install via |
|---------|---------|-------------|
| `tflite-runtime` | Lightweight TFLite inference engine | `pip` |
| `numpy` (<2.0) | Array operations for preprocessing | `pip` |
| `Pillow` | Image loading and preprocessing | `pip` |

### Standard Library (no install needed)

`socket`, `subprocess`, `os`, `time`, `json`, `re`, `math`, `signal`, `sys`
