# src/states/capture.py - multi-photo collection flow

import time
from src.context import AppContext

_N_PHOTOS       = 3     # number of photos to collect before processing
_cam_fail_count = 0


def on_enter(ctx: AppContext) -> None:
    """Reset failure counter when entering capture."""
    global _cam_fail_count
    _cam_fail_count = 0


def run(ctx: AppContext, now: float) -> str:
    """
    Wait for the user to press the shutter N times to collect photos.
    Returns 'processing' once enough frames are collected.
    """
    global _cam_fail_count

    distance_cm, dist_state = ctx.read_distance()
    photos_taken = len(ctx.captured_frames)

    # shutter pressed - grab a frame
    if ctx.touch.shutter_pressed() and ctx.debounced(now):
        ctx.last_touch = now
        frame          = ctx.cam.grab_inference_frame()
        ctx.captured_frames.append(frame)
        photos_taken = len(ctx.captured_frames)

        print(f"[Capture] Photo {photos_taken}/{_N_PHOTOS} taken")
        ctx.animation.show_capture_progress(photos_taken, _N_PHOTOS)
        time.sleep(0.6)

        if photos_taken >= _N_PHOTOS:
            return "processing"

        return "capturing"

    # no press - show live preview while waiting
    try:
        frame = ctx.cam.grab_frame()
        _cam_fail_count = 0
    except Exception as e:
        _cam_fail_count += 1
        print(f"[Capture] grab_frame failed ({_cam_fail_count}): {e}")
        if _cam_fail_count >= 3:
            try:
                ctx.cam.reload()
            except Exception as re:
                print(f"[Capture] Reload failed: {re}")
            _cam_fail_count = 0
        return "capturing"

    ctx.display.render(
        frame,
        distance_state = dist_state,
        distance_cm    = distance_cm,
        sensor_enabled = ctx.sensor_active,
    )

    return "capturing"
