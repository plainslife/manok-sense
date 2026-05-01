# main.py
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
_PREVIEW    = "preview"
_CAPTURING  = "capturing"
_PROCESSING = "processing"
_RESULT     = "result"
_SETTINGS   = "settings"
_GALLERY = "gallery"

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
    state        = _PREVIEW
    last_touch   = 0.0

    result          = None
    result_drawn    = False
    captured_frames: list = []

    settings_drawn  = False
    settings_status: str | None = None

    gallery_page  = 0
    gallery_files: list = []
    gallery_drawn = False

    _poweroff_confirm    = False
    _poweroff_confirm_at = 0.0
    _cam_fail_count = 0

    try:
        while True:
            now       = time.monotonic()
            debounced = (now - last_touch) > DEBOUNCE_SECS

            # ── Live distance reading (no-op when sensor is off/crashed) ─
            if sensor_active:
                distance_cm = sensor.get_cm()
                if not sensor.is_ok:
                    # Sensor dropped out mid-session — degrade gracefully
                    sensor_active = False
                    print("[Main] Distance sensor disconnected — running without it")
                dist_state = _get_distance_state(distance_cm)
            else:
                distance_cm = None
                dist_state  = "ok"   # treat as in-range when sensor is off

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
                    continue   # skip this loop tick, try again next iteration
                display.render(
                    frame,
                    distance_state  = dist_state,
                    distance_cm     = distance_cm,
                    sensor_enabled  = sensor_active,
                )

                if touch.settings_pressed() and debounced:
                    last_touch      = now
                    settings_drawn  = False
                    settings_status = None
                    state           = _SETTINGS
                
                elif touch.gallery_pressed() and debounced:
                    last_touch    = now
                    gallery_files = gallery.list_captures()
                    gallery_page  = 0
                    gallery_drawn = False
                    state         = _GALLERY

                elif touch.shutter_pressed() and debounced:
                    # Respect distance gate only when sensor is active
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
                    # Live feed while waiting for next button press
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
                        continue   # skip this loop tick, try again next iteration
                    display.render(
                        frame,
                        distance_state  = dist_state,
                        distance_cm     = distance_cm,
                        sensor_enabled  = sensor_active,
                    )

            # ── PROCESSING ─────────────────────────────────────────────
            elif state == _PROCESSING:
                animation.show_processing()

                label, conf, probs = run_inference(cam, frames=captured_frames)
                
                gallery.save_capture(captured_frames[len(captured_frames) // 2], label, conf)

                result          = (label, conf, probs)
                result_drawn    = False
                captured_frames = []
                state           = _RESULT

                r, g, b = _LED_COLORS.get(label, (255, 255, 255))
                led.set(r, g, b)
                print(f"[Classifier] {label} ({conf * 100:.1f}%) | "
                      f"adu={probs[0]:.2f} edi={probs[1]:.2f} spo={probs[2]:.2f}")

            # ── RESULT ─────────────────────────────────────────────────
            elif state == _RESULT:
                if not result_drawn:
                    label, conf, probs = result
                    animation.show_result(label, conf, probs)
                    result_drawn = True

                if touch.shutter_pressed() and debounced:
                    last_touch = now
                    state      = _PREVIEW
                    result     = None
                    led.on()

            # ── SETTINGS ───────────────────────────────────────────────
            elif state == _SETTINGS:
                if not settings_drawn:
                    animation.show_settings(cfg["distance_enabled"], settings_status,
                         poweroff_confirm=_poweroff_confirm)
                    settings_drawn = True

                # Back to preview
                if touch.shutter_pressed() and debounced:
                    last_touch      = now
                    settings_status = None
                    settings_drawn  = False
                    state           = _PREVIEW
                    _poweroff_confirm = False

                # Toggle the distance sensor
                elif touch.touched_at(_TOGGLE_CX, _TOGGLE_CY) and debounced:
                    last_touch = now

                    if cfg["distance_enabled"]:
                        # ── Turn OFF ─────────────────────────────────
                        sensor.shutdown()
                        sensor_active              = False
                        cfg["distance_enabled"]    = False
                        settings.save(cfg)
                        settings_status            = None
                        settings_drawn             = False
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

                        settings_drawn = False   # re-draw with new status
                
                elif touch.camera_reload_pressed() and debounced:
                    last_touch = now
                    try:
                        cam.reload()
                        print("[Settings] Camera reloaded")
                    except Exception as e:
                        print(f"[Settings] Camera reload failed: {e}")
                    settings_drawn = False

                elif touch.led_reload_pressed() and debounced:
                    last_touch     = now
                    led.reload()
                    settings_drawn = False   # redraw to confirm tap registered
            
                # ── Power off — two-tap confirm ──────────────────────────────
                elif touch.poweroff_pressed() and debounced:
                    last_touch = now

                    if _poweroff_confirm:
                        # Second tap → clean shutdown
                        animation.show_poweroff()
                        sensor.shutdown()
                        led.off()
                        cam.stop()
                        display.shutdown()
                        import subprocess
                        subprocess.run(["sudo", "shutdown", "-h", "now"])
                    else:
                        # First tap → arm confirm
                        _poweroff_confirm    = True
                        _poweroff_confirm_at = now
                        settings_drawn       = False

                # Reset confirm if user didn't tap again within 5 s
                if _poweroff_confirm and (now - _poweroff_confirm_at) > 5.0:
                    _poweroff_confirm = False
                    settings_drawn    = False
            
            # ── GALLERY ────────────────────────────────────────────────────
            elif state == _GALLERY:
                if not gallery_drawn:
                    animation.show_gallery(gallery_files, gallery_page)
                    gallery_drawn = True

                if touch.shutter_pressed() and debounced:
                    last_touch = now
                    state      = _PREVIEW

                elif touch.gallery_prev_pressed() and debounced and gallery_page > 0:
                    last_touch    = now
                    gallery_page -= 1
                    gallery_drawn = False

                elif touch.gallery_next_pressed() and debounced:
                    per_page     = 9
                    total_pages  = max(1, (len(gallery_files) + per_page - 1) // per_page)
                    if gallery_page + 1 < total_pages:
                        last_touch    = now
                        gallery_page += 1
                        gallery_drawn = False

    except KeyboardInterrupt:
        print("\nExiting")
    finally:
        sensor.shutdown()
        led.off()
        cam.stop()
        display.shutdown()


if __name__ == "__main__":
    main()
