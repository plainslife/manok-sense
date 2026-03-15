# Manoksense

A portable image vision device that captures a photo of chicken meat and classifies it as **edible**, **spoiled**, or **adulterated** using a MobileNetV2-based model running on a Raspberry Pi.

> 📸 Currently in **dataset collection stage**.


## File Structure

```
manoksense/
├── config.py           # All hardware and UI constants
├── main.py             # Entry point, wires all modules together
├── STYLE.md            # Coding conventions and style rules
└── src/
    ├── __init__.py
    ├── camera.py       # Frame grabbing and still capture via Picamera2
    ├── capture.py      # Filename generation for image capturing
    ├── display.py      # Screen rendering and UI drawing
    ├── led.py          # NeoPixel LED status control
    ├── touch.py        # Touch input detection 
    └── drivers/
        ├── __init__.py
        └── xpt2046_driver.py   # Self-written XPT2046 touch driver (by ivan)
```

## Contributing

Please read [STYLE.md](STYLE.md) before contributing to keep the codebase consistent.
