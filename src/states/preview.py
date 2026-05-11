# src/states/preview.py - live camera feed with touch navigation

import time
from src.context import AppContext
import src.gallery_store as gallery

# module-level variable — persists between loop iterations since Python
# keeps modules in memory for the lifetime of the program
_cam_fail_count = 0


def on_enter(ctx: AppContext) -> None:
    """Reset local state when entering preview."""
    global _cam_fail_count
    _cam_fail_count = 0


def run(ctx: AppContext, now: float) -> str:
    """
    Render the live camera preview and handle touch navigation.
    Returns the name of the next state.
    """
    global _cam_fail_count

    distance_cm, dist_state = ctx.read_distance()

    # gram and render the live frame
    try:
        frame = ctx.cam.grab_frame()
        _cam_fail_count = 0
    except Exception as e:
        _cam_fail_count += 1
        print(f"[Preview] grab_frame failed ({_cam_fail_count}): {e}")
        if _cam_fail_count >= 3:
            print("[Preview] Too many failures — reloading camera")
            try:
                ctx.cam.reload()
            except Exception as re:
                print(f"[Preview] Reload failed: {re}")
            _cam_fail_count = 0
        return "preview"   # stay in preview while recovering

    ctx.display.render(
        frame,
        distance_state = dist_state,
        distance_cm    = distance_cm,
        sensor_enabled = ctx.sensor_active,
    )

    # touch handling
    if not ctx.debounced(now):
        return "preview"

    if ctx.touch.settings_pressed():
        ctx.last_touch = now
        return "settings"

    if ctx.touch.gallery_pressed():
        ctx.last_touch       = now
        ctx.gallery_sessions = gallery.list_sessions()
        ctx.gallery_page     = 0
        return "gallery"

    if ctx.touch.shutter_pressed():
        # Button is locked when sensor is active and distance is out of range
        if ctx.sensor_active and dist_state != "ok":
            return "preview"
        ctx.last_touch      = now
        ctx.captured_frames = []
        return "capturing"

    return "preview"
