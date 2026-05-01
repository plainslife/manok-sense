# src/led.py

import neopixel
from config import LED_PIN, LED_COUNT, LED_BRIGHTNESS

class StatusLed:
    
    def __init__(self):
        self._pixels = neopixel.NeoPixel(
            LED_PIN,
            LED_COUNT,
            brightness=LED_BRIGHTNESS,
            auto_write=False,
        )

    # not sure if this will be used 
    def set(self, r: int, g: int, b: int) -> None: 
        self._pixels.fill((r, g, b))
        self._pixels.show()

    def on(self) -> None:
        self.set(255, 200, 150)

    def off(self) -> None:
        self.set(0, 0, 0)

    # just in case led stops working
    def reload(self) -> None:
        print("[LED] Reloading...")
        try:
            self._pixels.deinit()
        except Exception:
            pass
        self._pixels = neopixel.NeoPixel(
            LED_PIN,
            LED_COUNT,
            brightness=LED_BRIGHTNESS,
            auto_write=False,
        )
        self.on()
        print("[LED] Reload complete")
