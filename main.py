# main.py -> contains the whole logic and the loop

import time
import src.boot as boot
from src.camera import Camera
from src.led import StatusLed
from src.touch import TouchInput
from src.display import DisplayUI
from src.animation import Animation
from src.capture import generate_filename
from config import DEBOUNCE_SECS

def main() -> None:
    # display first — it clears the white screen immediately
    display = DisplayUI()
    animation = Animation(display)

    animation.show_splash()
    time.sleep(1.2)

    led, cam, touch = boot.run(animation)

    animation.show_ready()
    time.sleep(0.8)

    try:
        while True:
            frame = cam.grab_frame()

            if touch.shutter_pressed():
                filepath = generate_filename()
                display.render(frame, btn_pressed=True)
                cam.save(filepath)
                print(f"Image Saved -> {filepath}")
                time.sleep(DEBOUNCE_SECS)
            else:
                display.render(frame)

    except KeyboardInterrupt:
        print("\nExiting")

    finally:
        led.off()
        cam.stop()


if __name__ == "__main__":
    main()
