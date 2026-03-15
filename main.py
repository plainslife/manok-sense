# main.py -> contains the whole logic the loop

import time
from src.camera import Camera
from src.display import DisplayUI
from src.touch import TouchInput
from src.capture import generate_filename
from config import DEBOUNCE_SECS
from src.led import StatusLed

def main() -> None:
    led = StatusLed() 
    cam = Camera()
    display = DisplayUI()
    touch = TouchInput()

    cam.start()
    led.on()

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



