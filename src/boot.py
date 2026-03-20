import time
from src.camera import Camera
from src.display import DisplayUI
from src.touch import TouchInput
from src.led import StatusLed
from src.animation import Animation

# labels shown in the boot checklist
_STEPS = ["LED", "Camera", "Touch", "Preview"]

def run(animation: Animation) -> tuple[StatusLed, Camera, TouchInput]:
    """
    Initialize each hardware component one by one,
    updating the boot screen after each step.
    """
    steps: list[tuple[str, str | None]] = [
        (s, None) for s in _STEPS
    ]

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
    _render(active=1, ok_up_to=1, progress=0.25)
    time.sleep(1)

    # --- Camera ---
    cam = Camera()
    _render(active=2, ok_up_to=2, progress=0.50)

    time.sleep(1)
    # --- Touch ---
    touch = TouchInput()
    _render(active=3, ok_up_to=3, progress=0.75)

    time.sleep(1)
    # --- Preview (cam.start is the slow bit) ---
    cam.start()
    _render(active=3, ok_up_to=4, progress=1.0)

    time.sleep(1)

    return led, cam, touch

