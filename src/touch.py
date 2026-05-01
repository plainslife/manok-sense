# src/touch.py

from src.drivers.xpt2046_driver import Touch
from config import (
    TOUCH_BUS, TOUCH_DEVICE,
    BTN_X, BTN_Y, BTN_RADIUS,
    SETTINGS_X, SETTINGS_Y, SETTINGS_RADIUS,
    CAMERA_RELOAD_X, CAMERA_RELOAD_Y, CAMERA_RELOAD_RADIUS,
    LED_RELOAD_X, LED_RELOAD_Y, LED_RELOAD_RADIUS,
    POWEROFF_X, POWEROFF_Y, POWEROFF_RADIUS,
    GALLERY_X, GALLERY_Y, GALLERY_RADIUS,
    GALLERY_PREV_X, GALLERY_PREV_Y, GALLERY_PREV_R,
    GALLERY_NEXT_X, GALLERY_NEXT_Y, GALLERY_NEXT_R,
    DISPLAY_HEIGHT, 
)

class TouchInput:
    def __init__(self) -> None:
        self._ts = Touch(bus=TOUCH_BUS, device=TOUCH_DEVICE)

    # raw pos
    def get_position(self) -> tuple[int, int] | None:
        return self._ts.get_touch()

    # check if raw pos is within radius of canvas
    def _hit(self, tx: int, ty: int, canvas_x: int, canvas_y: int, radius: int) -> bool:
        mirrored_x = DISPLAY_HEIGHT - 1 - canvas_x
        return ((tx - canvas_y) ** 2 + (ty - mirrored_x) ** 2) ** 0.5 < radius

    # possible area to hit
    # shutter
    def shutter_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, BTN_X, BTN_Y, BTN_RADIUS)

    # settings
    def settings_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, SETTINGS_X, SETTINGS_Y, SETTINGS_RADIUS)
   
    # gallery
    def gallery_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_X, GALLERY_Y, GALLERY_RADIUS)
    
    # preview previous image
    def gallery_prev_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_PREV_X, GALLERY_PREV_Y, GALLERY_PREV_R)

    # preview next image
    def gallery_next_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_NEXT_X, GALLERY_NEXT_Y, GALLERY_NEXT_R)

    # settings touch zone
    # cam reload button
    def camera_reload_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, CAMERA_RELOAD_X, CAMERA_RELOAD_Y, CAMERA_RELOAD_RADIUS)

    # led reload button
    def led_reload_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, LED_RELOAD_X, LED_RELOAD_Y, LED_RELOAD_RADIUS)

    # poweriff
    def poweroff_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, POWEROFF_X, POWEROFF_Y, POWEROFF_RADIUS)

    # any
    def touched_at(self, canvas_x: int, canvas_y: int, radius: int = 22) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, canvas_x, canvas_y, radius)
