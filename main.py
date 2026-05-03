# main.py

import os
import time
import src.boot as boot
import src.settings as settings
import src.gallery as gallery
from src.camera import Camera
from src.led import StatusLed
from src.touch import TouchInput
from src.display import DisplayUI
from src.animation import Animation
from inference_bridge import run_inference
from src.distance import DistanceSensor
from config import DEBOUNCE_SECS, DISTANCE_MIN_CM, DISTANCE_MAX_CM

# ── States ─────────────────────────────────────────────────────────────────
_PREVIEW         = "preview"
_CAPTURING       = "capturing"
_PROCESSING      = "processing"
_RESULT          = "result"
_SETTINGS        = "settings"
_GALLERY         = "gallery"
_GALLERY_PREVIEW = "gallery_preview"

# ── Capture config ──────────────────────────────────────────────────────────
_N_PHOTOS    = 3    # number of photos to average
_PHOTO_DELAY = 0.8  # seconds between each capture (unused; button-driven)

# ── Settings toggle hit zone (canvas coordinates) ───────────────────────────
_TOGGLE_CX = 189
_TOGGLE_CY = 96

# ── LED colours per classification result ───────────────────────────────────
_LED_COLORS = {
    "edible":      (0,   220, 80),
    "adulterated": (255, 130, 0),
    "spoiled":     (220, 30,  30),
}


def _get_distance_state(cm: int | None) -> str:
    if cm is None:
        return "far"
    if cm < DISTANCE_MIN_CM:
        return "near"
    if cm > DISTANCE_MAX_CM:
        return "far"
    return "ok"


def main() -> None:
    display   = DisplayUI()
    animation = Animation(display)
    animation.show_splash()
    time.sleep(1.2)

    led, cam, touch = boot.run(animation)

    # ── Load persisted settings ─────────────────────────────────────────
    cfg = settings.load()

    # ── Distance sensor — try to init on boot if previously enabled ─────
    sensor        = DistanceSensor()
    sensor_active = False

    if cfg["distance_enabled"]:
        print("[Main] Distance sensor enabled in settings — attempting boot init")
        sensor_active = sensor.try_init(3.0)
        if not sensor_active:
            print("[Main] Sensor not found at boot — disabling for this session")

    animation.show_ready()
    time.sleep(0.8)

    # ── Main loop state ─────────────────────────────────────────────────
    state      = _PREVIEW
    last_touch = 0.0

    # Result state
    result: tuple | None = None
    result_drawn          = False
    result_frames: list   = []
    result_frame_idx      = 0

    # Capture state
    captured_frames: list = []

    # Settings state
    settings_drawn              = False
    settings_status: str | None = None
    settings_status_at          = 0.0   # monotonic time of last cam/led action
    _poweroff_confirm           = False
    _poweroff_confirm_at        = 0.0

    # Gallery grid state
    gallery_sessions: list[list[str]] = []
    gallery_page                       = 0
    gallery_drawn                      = False

    # Gallery preview state
    gallery_session_idx   = 0
    gallery_frame_idx     = 0
    gallery_preview_drawn = False
    _delete_confirm       = False
    _delete_confirm_at    = 0.0

    _cam_fail_count = 0

    try:
        while True:
            now       = time.monotonic()
            debounced = (now - last_touch) > DEBOUNCE_SECS

            # ── Live distance reading (no-op when sensor is off/crashed) ─
            if sensor_active:
                distance_cm = sensor.get_cm()
                if not sensor.is_ok:
                    sensor_active = False
                    print("[Main] Distance sensor disconnected — running without it")
                dist_state = _get_distance_state(distance_cm)
            else:
                distance_cm = None
                dist_state  = "ok"

            # ── PREVIEW ────────────────────────────────────────────────
            if state == _PREVIEW:
                try:
                    frame = cam.grab_frame()
                    _cam_fail_count = 0
                except Exception as e:
                    _cam_fail_count += 1
                    print(f"[Camera] grab_frame failed ({_cam_fail_count}): {e}")
                    if _cam_fail_count >= 3:
                        print("[Camera] Too many failures — reloading")
                        try:
                            cam.reload()
                        except Exception as re:
                            print(f"[Camera] Reload failed: {re}")
                        _cam_fail_count = 0
                    continue
                display.render(
                    frame,
                    distance_state = dist_state,
                    distance_cm    = distance_cm,
                    sensor_enabled = sensor_active,
                )

                if touch.settings_pressed() and debounced:
                    last_touch      = now
                    settings_drawn  = False
                    settings_status = None
                    state           = _SETTINGS

                elif touch.gallery_pressed() and debounced:
                    last_touch       = now
                    gallery_sessions = gallery.list_sessions()
                    gallery_page     = 0
                    gallery_drawn    = False
                    state            = _GALLERY

                elif touch.shutter_pressed() and debounced:
                    if sensor_active and dist_state != "ok":
                        pass   # button locked — out of range
                    else:
                        last_touch      = now
                        captured_frames = []
                        result_drawn    = False
                        state           = _CAPTURING

            # ── CAPTURING ──────────────────────────────────────────────
            elif state == _CAPTURING:
                photos_taken = len(captured_frames)

                if touch.shutter_pressed() and debounced:
                    last_touch   = now
                    capture      = cam.grab_inference_frame()
                    captured_frames.append(capture)
                    photos_taken = len(captured_frames)

                    print(f"[Capture] Photo {photos_taken}/{_N_PHOTOS} taken")
                    animation.show_capture_progress(photos_taken, _N_PHOTOS)
                    time.sleep(0.6)

                    if photos_taken >= _N_PHOTOS:
                        state = _PROCESSING

                else:
                    try:
                        frame = cam.grab_frame()
                        _cam_fail_count = 0
                    except Exception as e:
                        _cam_fail_count += 1
                        print(f"[Camera] grab_frame failed ({_cam_fail_count}): {e}")
                        if _cam_fail_count >= 3:
                            print("[Camera] Too many failures — reloading")
                            try:
                                cam.reload()
                            except Exception as re:
                                print(f"[Camera] Reload failed: {re}")
                            _cam_fail_count = 0
                        continue
                    display.render(
                        frame,
                        distance_state = dist_state,
                        distance_cm    = distance_cm,
                        sensor_enabled = sensor_active,
                    )

            # ── PROCESSING ─────────────────────────────────────────────
            elif state == _PROCESSING:
                animation.show_processing()

                label, conf, probs = run_inference(cam, frames=captured_frames)

                # Save all frames under one session timestamp
                gallery.save_capture(captured_frames, label, conf)

                # Keep frames for result navigation before clearing
                result_frames    = list(captured_frames)
                result           = (label, conf, probs)
                result_drawn     = False
                result_frame_idx = 0
                captured_frames  = []
                state            = _RESULT

                r, g, b = _LED_COLORS.get(label, (255, 255, 255))
                led.set(r, g, b)
                print(f"[Classifier] {label} ({conf * 100:.1f}%) | "
                      f"adu={probs[0]:.2f} edi={probs[1]:.2f} spo={probs[2]:.2f}")

            # ── RESULT ─────────────────────────────────────────────────
            elif state == _RESULT:
                if not result_drawn:
                    label, conf, probs = result
                    animation.show_result_with_frame(result_frames, result_frame_idx, label)
                    result_drawn = True

                if touch.gallery_prev_pressed() and debounced:
                    if result_frame_idx > 0:
                        last_touch       = now
                        result_frame_idx -= 1
                        result_drawn     = False

                elif touch.gallery_next_pressed() and debounced:
                    if result_frame_idx < len(result_frames) - 1:
                        last_touch       = now
                        result_frame_idx += 1
                        result_drawn     = False

                elif touch.shutter_pressed() and debounced:
                    last_touch    = now
                    state         = _PREVIEW
                    result        = None
                    result_frames = []
                    led.on()

            # ── SETTINGS ───────────────────────────────────────────────
            elif state == _SETTINGS:
                if not settings_drawn:
                    animation.show_settings(
                        cfg["distance_enabled"],
                        settings_status,
                        poweroff_confirm=_poweroff_confirm,
                    )
                    settings_drawn = True

                # Auto-clear cam/led feedback after 2 seconds
                if settings_status in ("cam_ok", "cam_err", "led_ok", "led_err"):
                    if (now - settings_status_at) > 2.0:
                        settings_status = None
                        settings_drawn  = False

                # Back to preview
                if touch.shutter_pressed() and debounced:
                    last_touch        = now
                    settings_status   = None
                    settings_drawn    = False
                    _poweroff_confirm = False
                    state             = _PREVIEW

                # Toggle the distance sensor
                elif touch.touched_at(_TOGGLE_CX, _TOGGLE_CY) and debounced:
                    last_touch = now

                    if cfg["distance_enabled"]:
                        # ── Turn OFF ─────────────────────────────────
                        sensor.shutdown()
                        sensor_active           = False
                        cfg["distance_enabled"] = False
                        settings.save(cfg)
                        settings_status = None
                        settings_drawn  = False
                        print("[Settings] Distance sensor disabled")

                    else:
                        # ── Turn ON — attempt connection ──────────────
                        settings_status = "connecting"
                        animation.show_settings(False, "connecting")

                        ok = sensor.try_init(3.0)

                        if ok:
                            sensor_active           = True
                            cfg["distance_enabled"] = True
                            settings.save(cfg)
                            settings_status = "connected"
                            print("[Settings] Distance sensor enabled")
                        else:
                            sensor_active           = False
                            cfg["distance_enabled"] = False
                            settings_status         = "no_sensor"
                            print("[Settings] No sensor found")

                        settings_drawn = False

                elif touch.camera_reload_pressed() and debounced:
                    last_touch = now
                    try:
                        cam.reload()
                        settings_status = "cam_ok"
                        print("[Settings] Camera reloaded")
                    except Exception as e:
                        settings_status = "cam_err"
                        print(f"[Settings] Camera reload failed: {e}")
                    settings_status_at = now
                    settings_drawn     = False

                elif touch.led_reload_pressed() and debounced:
                    last_touch = now
                    try:
                        led.reload()
                        settings_status = "led_ok"
                        print("[Settings] LED reloaded")
                    except Exception as e:
                        settings_status = "led_err"
                        print(f"[Settings] LED reload failed: {e}")
                    settings_status_at = now
                    settings_drawn     = False

                # ── Power off — two-tap confirm ──────────────────────────────
                elif touch.poweroff_pressed() and debounced:
                    last_touch = now

                    if _poweroff_confirm:
                        animation.show_poweroff()
                        sensor.shutdown()
                        led.off()
                        cam.stop()
                        display.shutdown()
                        import subprocess
                        subprocess.run(["sudo", "shutdown", "-h", "now"])
                    else:
                        _poweroff_confirm    = True
                        _poweroff_confirm_at = now
                        settings_drawn       = False

                if _poweroff_confirm and (now - _poweroff_confirm_at) > 5.0:
                    _poweroff_confirm = False
                    settings_drawn    = False

            # ── GALLERY ────────────────────────────────────────────────────
            elif state == _GALLERY:
                if not gallery_drawn:
                    animation.show_gallery(gallery_sessions, gallery_page)
                    gallery_drawn = True

                if touch.shutter_pressed() and debounced:
                    last_touch = now
                    state      = _PREVIEW

                elif touch.gallery_prev_pressed() and debounced and gallery_page > 0:
                    last_touch    = now
                    gallery_page -= 1
                    gallery_drawn = False

                elif touch.gallery_next_pressed() and debounced:
                    per_page    = 9
                    total_pages = max(1, (len(gallery_sessions) + per_page - 1) // per_page)
                    if gallery_page + 1 < total_pages:
                        last_touch    = now
                        gallery_page += 1
                        gallery_drawn = False

                else:
                    idx = touch.thumbnail_tapped(gallery_page, gallery_sessions)
                    if idx is not None and debounced:
                        last_touch            = now
                        gallery_session_idx   = idx
                        gallery_frame_idx     = 0
                        _delete_confirm       = False
                        gallery_preview_drawn = False
                        state                 = _GALLERY_PREVIEW

            # ── GALLERY PREVIEW ────────────────────────────────────────────
            elif state == _GALLERY_PREVIEW:
                if not gallery_preview_drawn:
                    animation.show_gallery_preview(
                        gallery_sessions,
                        gallery_session_idx,
                        gallery_frame_idx,
                        _delete_confirm,
                    )
                    gallery_preview_drawn = True

                if touch.shutter_pressed() and debounced:
                    last_touch            = now
                    _delete_confirm       = False
                    gallery_drawn         = False
                    state                 = _GALLERY

                elif touch.gallery_prev_pressed() and debounced:
                    if gallery_frame_idx > 0:
                        last_touch            = now
                        gallery_frame_idx    -= 1
                        _delete_confirm       = False
                        gallery_preview_drawn = False
                    elif gallery_session_idx > 0:
                        last_touch            = now
                        gallery_session_idx  -= 1
                        gallery_frame_idx     = len(gallery_sessions[gallery_session_idx]) - 1
                        _delete_confirm       = False
                        gallery_preview_drawn = False

                elif touch.gallery_next_pressed() and debounced:
                    current_session = gallery_sessions[gallery_session_idx]
                    if gallery_frame_idx < len(current_session) - 1:
                        last_touch            = now
                        gallery_frame_idx    += 1
                        _delete_confirm       = False
                        gallery_preview_drawn = False
                    elif gallery_session_idx < len(gallery_sessions) - 1:
                        last_touch            = now
                        gallery_session_idx  += 1
                        gallery_frame_idx     = 0
                        _delete_confirm       = False
                        gallery_preview_drawn = False

                elif touch.gallery_delete_pressed() and debounced:
                    last_touch = now

                    if _delete_confirm:
                        session_files = gallery_sessions[gallery_session_idx]
                        for fp in session_files:
                            try:
                                os.remove(fp)
                                print(f"[Gallery] Deleted {fp}")
                            except Exception as e:
                                print(f"[Gallery] Delete failed {fp}: {e}")

                        gallery_sessions = gallery.list_sessions()
                        _delete_confirm  = False
                        gallery_drawn    = False

                        if gallery_session_idx >= len(gallery_sessions):
                            gallery_session_idx = max(0, len(gallery_sessions) - 1)
                        gallery_frame_idx     = 0
                        gallery_preview_drawn = False
                        state                 = _GALLERY
                    else:
                        _delete_confirm    = True
                        _delete_confirm_at = now
                        gallery_preview_drawn = False

                if _delete_confirm and (now - _delete_confirm_at) > 3.0:
                    _delete_confirm       = False
                    gallery_preview_drawn = False

    except KeyboardInterrupt:
        print("\nExiting")
    finally:
        sensor.shutdown()
        led.off()
        cam.stop()
        display.shutdown()


if __name__ == "__main__":
    main()
