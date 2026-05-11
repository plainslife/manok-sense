# src/boot.py

import time
from src.hardware.camera import Camera
from src.hardware.touch import TouchInput
from src.hardware.led import StatusLed
from src.hardware.distance import DistanceSensor
from src.ui.animation import Animation
from inference_bridge import start_worker

_STEPS = ["LED", "Camera", "Touch", "Model", "Preview"]

def run(animation: Animation) -> tuple[StatusLed, Camera, TouchInput]:
    steps: list[tuple[str, str | None]] = [(s, None) for s in _STEPS]

    def _render(active: int, ok_up_to: int, progress: float) -> None:
        for i in range(len(steps)):
            if i < ok_up_to:
                steps[i] = (_STEPS[i], "OK")
            elif i == active:
                steps[i] = (_STEPS[i], "...")
            else:
                steps[i] = (_STEPS[i], None)
        animation.show_boot_step(steps, progress)

    # --- LED ---
    _render(active=0, ok_up_to=0, progress=0.05)
    led = StatusLed()
    led.on()
    _render(active=1, ok_up_to=1, progress=0.16)
    time.sleep(1)

    # --- Camera ---
    cam = Camera()
    _render(active=2, ok_up_to=2, progress=0.33)
    time.sleep(2)

    # --- Touch ---
    touch = TouchInput()
    _render(active=3, ok_up_to=3, progress=0.50)
    time.sleep(1)
    
    # --- Model ---
    start_worker()
    _render(active=4, ok_up_to=4, progress=0.66)
    time.sleep(0.5)

    # --- Sensor ---
    # sensor = DistanceSensor()
    # _render(active=5, ok_up_to=5, progress=0.83)
    # time.sleep(0.5)
    
    # --- Preview ---
    cam.start()
    _render(active=5, ok_up_to=6, progress=1.0)
    time.sleep(1)

    return led, cam, touch
