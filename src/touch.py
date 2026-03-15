# src/touch.py 

from src.drivers.xpt2046_driver import Touch 
from config import TOUCH_BUS, TOUCH_DEVICE, BTN_X, BTN_Y, BTN_RADIUS

class TouchInput:
    
    def __init__(self):
        self._ts = Touch(bus=TOUCH_BUS, device=TOUCH_DEVICE)

    # get the touch position 
    def get_position(self) -> tuple[int, int] | None:
        return self._ts.get_touch()

    def shutter_pressed(self) -> bool:
        pos = self.get_position()
        print(f"{pos}")

        if pos is None:
            return False 
        
        tx, ty = pos
        distance = ((tx - BTN_X) ** 2 + (ty - BTN_Y) ** 2) ** 0.5
        print(distance < BTN_RADIUS)
        return distance < BTN_RADIUS
