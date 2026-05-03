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
    GALLERY_DELETE_X, GALLERY_DELETE_Y, GALLERY_DELETE_RADIUS,
    DISPLAY_HEIGHT,
)


class TouchInput:
    def __init__(self) -> None:
        self._ts = Touch(bus=TOUCH_BUS, device=TOUCH_DEVICE)

    # ── Raw position ─────────────────────────────────────────────────────

    def get_position(self) -> tuple[int, int] | None:
        return self._ts.get_touch()

    # ── Hit helpers ──────────────────────────────────────────────────────

    def _hit(self, tx: int, ty: int, canvas_x: int, canvas_y: int, radius: int) -> bool:
        mirrored_x = DISPLAY_HEIGHT - 1 - canvas_x
        return ((tx - canvas_y) ** 2 + (ty - mirrored_x) ** 2) ** 0.5 < radius

    def _hit_rect(self, tx: int, ty: int, cx1: int, cy1: int, cx2: int, cy2: int) -> bool:
        # Mirrors the same axis swap as _hit(): tx→canvas_y, ty→canvas_x (mirrored)
        ty_min = DISPLAY_HEIGHT - 1 - cx2
        ty_max = DISPLAY_HEIGHT - 1 - cx1
        return cy1 <= tx <= cy2 and ty_min <= ty <= ty_max

    # ── Named hit zones ──────────────────────────────────────────────────

    def shutter_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, BTN_X, BTN_Y, BTN_RADIUS)

    def settings_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, SETTINGS_X, SETTINGS_Y, SETTINGS_RADIUS)

    def gallery_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_X, GALLERY_Y, GALLERY_RADIUS)

    def gallery_prev_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_PREV_X, GALLERY_PREV_Y, GALLERY_PREV_R)

    def gallery_next_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_NEXT_X, GALLERY_NEXT_Y, GALLERY_NEXT_R)

    def thumbnail_tapped(self, page: int, sessions: list) -> int | None:
        """
        Returns the session index (into sessions) that the tap hit,
        or None if no thumbnail was hit.  One thumbnail per session.
        """
        pos = self.get_position()
        if pos is None:
            return None
        tx, ty = pos

        PER_PAGE = 9
        COLS     = 3
        CELL     = 76      # 72px thumb + 4px gap
        START_X  = 4
        START_Y  = 56
        THUMB_W  = 72
        THUMB_H  = 72

        start_idx = page * PER_PAGE
        count     = min(PER_PAGE, len(sessions) - start_idx)

        for i in range(count):
            col = i % COLS
            row = i // COLS
            x1  = START_X + col * CELL
            y1  = START_Y + row * CELL
            if self._hit_rect(tx, ty, x1, y1, x1 + THUMB_W, y1 + THUMB_H):
                return start_idx + i

        return None

    def gallery_delete_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, GALLERY_DELETE_X, GALLERY_DELETE_Y, GALLERY_DELETE_RADIUS)

    def camera_reload_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, CAMERA_RELOAD_X, CAMERA_RELOAD_Y, CAMERA_RELOAD_RADIUS)

    def led_reload_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, LED_RELOAD_X, LED_RELOAD_Y, LED_RELOAD_RADIUS)

    def poweroff_pressed(self) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, POWEROFF_X, POWEROFF_Y, POWEROFF_RADIUS)

    def touched_at(self, canvas_x: int, canvas_y: int, radius: int = 22) -> bool:
        pos = self.get_position()
        if pos is None:
            return False
        tx, ty = pos
        return self._hit(tx, ty, canvas_x, canvas_y, radius)
