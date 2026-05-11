# src/states/settings.py - sensor toggle, hardware reload, and power off

import time
import subprocess
from PIL import ImageDraw
import src.settings_store as settings
from src.context import AppContext
from src.ui.color import OK_GREEN, ERR_RED, ACCENT, FG, DIM
from src.ui.helpers import load_font, draw_header
from config import DISPLAY_HEIGHT, DISPLAY_WIDTH, FONT_BOLD, FONT_REGULAR

_drawn               = False
_status: str | None  = None
_status_at           = 0.0
_poweroff_confirm    = False
_poweroff_confirm_at = 0.0

_TOGGLE_CX = 189
_TOGGLE_CY = 96


def on_enter(ctx: AppContext) -> None:
    global _drawn, _status, _poweroff_confirm
    _drawn            = False
    _status           = None
    _poweroff_confirm = False


def _draw(ctx: AppContext) -> None:
    """Draw the settings screen."""
    canvas = ctx.display.blank_canvas()
    draw   = ImageDraw.Draw(canvas)

    font_sub     = load_font(FONT_BOLD,    13)
    font_section = load_font(FONT_BOLD,     9)
    font_label   = load_font(FONT_REGULAR, 12)
    font_btn     = load_font(FONT_REGULAR,  9)
    font_status  = load_font(FONT_REGULAR, 10)
    font_hint    = load_font(FONT_REGULAR, 10)

    cx = DISPLAY_HEIGHT // 2
    draw_header(draw, cx)

    draw.text((cx, 50), "Settings", font=font_sub, fill=FG, anchor="mm")
    draw.line((20, 63, DISPLAY_HEIGHT - 20, 63), fill=DIM, width=1)

    # config section
    draw.text((20, 76), "CONFIG", font=font_section, fill=DIM, anchor="lm")

    ROW_Y     = _TOGGLE_CY
    TOGGLE_CX = _TOGGLE_CX
    PILL_W    = 40
    PILL_H    = 11
    KNOB_R    = 9

    distance_enabled = ctx.cfg["distance_enabled"]
    draw.text((20, ROW_Y), "Distance sensor", font=font_label, fill=FG, anchor="lm")

    pill_color = OK_GREEN if distance_enabled else DIM
    draw.rounded_rectangle(
        (TOGGLE_CX - PILL_W, ROW_Y - PILL_H,
         TOGGLE_CX + PILL_W, ROW_Y + PILL_H),
        radius=PILL_H, fill=pill_color,
    )
    knob_x = (TOGGLE_CX + PILL_W - KNOB_R - 2) if distance_enabled \
         else (TOGGLE_CX - PILL_W + KNOB_R + 2)
    draw.ellipse(
        (knob_x - KNOB_R, ROW_Y - KNOB_R, knob_x + KNOB_R, ROW_Y + KNOB_R),
        fill=FG,
    )
    draw.line((20, 116, DISPLAY_HEIGHT - 20, 116), fill="#1E1E1E", width=1)

    if _status in ("connecting", "connected", "no_sensor"):
        msg, msg_color = {
            "connecting": ("Connecting...",      ACCENT),
            "connected":  ("Connected",          OK_GREEN),
            "no_sensor":  ("No sensor detected", ERR_RED),
        }[_status]
        draw.text((cx, 128), msg, font=font_status, fill=msg_color, anchor="mm")

    # system section
    draw.text((20, 136), "SYSTEM", font=font_section, fill=DIM, anchor="lm")

    BTN_CX = 189
    BTN_W  = 40
    BTN_H  = 12

    CAM_Y = 156
    if _status == "cam_ok":
        cam_fill, cam_outline, cam_text, cam_col = "#0A0A2A", "#4A6AE8", "DONE",   OK_GREEN
    elif _status == "cam_err":
        cam_fill, cam_outline, cam_text, cam_col = "#2A0A0A", ERR_RED,   "FAILED", ERR_RED
    else:
        cam_fill, cam_outline, cam_text, cam_col = "#1A1A2A", "#4A6AE8", "RELOAD", "#4A6AE8"

    draw.text((20, CAM_Y), "Camera", font=font_label, fill=FG, anchor="lm")
    draw.rounded_rectangle(
        (BTN_CX - BTN_W, CAM_Y - BTN_H, BTN_CX + BTN_W, CAM_Y + BTN_H),
        radius=BTN_H, fill=cam_fill, outline=cam_outline, width=1,
    )
    draw.text((BTN_CX, CAM_Y), cam_text, font=font_btn, fill=cam_col, anchor="mm")
    draw.line((20, 172, DISPLAY_HEIGHT - 20, 172), fill="#1E1E1E", width=1)

    LED_Y = 192
    if _status == "led_ok":
        led_fill, led_outline, led_text, led_col = "#0A2A0A", OK_GREEN, "DONE",   OK_GREEN
    elif _status == "led_err":
        led_fill, led_outline, led_text, led_col = "#2A0A0A", ERR_RED,  "FAILED", ERR_RED
    else:
        led_fill, led_outline, led_text, led_col = "#1A2A1A", OK_GREEN, "RELOAD", OK_GREEN

    draw.text((20, LED_Y), "LED strip", font=font_label, fill=FG, anchor="lm")
    draw.rounded_rectangle(
        (BTN_CX - BTN_W, LED_Y - BTN_H, BTN_CX + BTN_W, LED_Y + BTN_H),
        radius=BTN_H, fill=led_fill, outline=led_outline, width=1,
    )
    draw.text((BTN_CX, LED_Y), led_text, font=font_btn, fill=led_col, anchor="mm")
    draw.line((20, 208, DISPLAY_HEIGHT - 20, 208), fill="#1E1E1E", width=1)

    POFF_Y    = 228
    pill_fill = ERR_RED   if _poweroff_confirm else "#3A1A1A"
    poff_text = "CONFIRM?" if _poweroff_confirm else "SHUT DOWN"
    poff_col  = FG        if _poweroff_confirm else ERR_RED

    draw.text((20, POFF_Y), "Power off", font=font_label, fill=FG, anchor="lm")
    draw.rounded_rectangle(
        (BTN_CX - BTN_W, POFF_Y - BTN_H, BTN_CX + BTN_W, POFF_Y + BTN_H),
        radius=BTN_H, fill=pill_fill, outline=ERR_RED, width=1,
    )
    draw.text((BTN_CX, POFF_Y), poff_text, font=font_btn, fill=poff_col, anchor="mm")
    draw.line((20, 244, DISPLAY_HEIGHT - 20, 244), fill="#1E1E1E", width=1)

    draw.text((cx, DISPLAY_WIDTH - 22), "tap \u25cf to go back", font=font_hint, fill=DIM, anchor="mm")

    ctx.display.flush(canvas)


def _draw_poweroff(ctx: AppContext) -> None:
    """Draw the shutdown confirmation screen."""
    canvas = ctx.display.blank_canvas()
    draw   = ImageDraw.Draw(canvas)

    font_big = load_font(FONT_BOLD,    20)
    font_sub = load_font(FONT_REGULAR, 11)

    cx, cy = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2
    draw_header(draw, cx)

    draw.text((cx, cy - 10), "Shutting down...", font=font_big, fill=FG,  anchor="mm")
    draw.text((cx, cy + 18), "safe to unplug",   font=font_sub, fill=DIM, anchor="mm")

    ctx.display.flush(canvas)


def run(ctx: AppContext, now: float) -> str:
    global _drawn, _status, _status_at, _poweroff_confirm, _poweroff_confirm_at

    if not _drawn:
        _draw(ctx)
        _drawn = True

    if _status in ("cam_ok", "cam_err", "led_ok", "led_err"):
        if (now - _status_at) > 2.0:
            _status = None
            _drawn  = False

    if _poweroff_confirm and (now - _poweroff_confirm_at) > 5.0:
        _poweroff_confirm = False
        _drawn            = False

    if not ctx.debounced(now):
        return "settings"

    if ctx.touch.shutter_pressed():
        ctx.last_touch = now
        return "preview"

    elif ctx.touch.touched_at(_TOGGLE_CX, _TOGGLE_CY):
        ctx.last_touch = now
        if ctx.cfg["distance_enabled"]:
            ctx.sensor.shutdown()
            ctx.sensor_active           = False
            ctx.cfg["distance_enabled"] = False
            settings.save(ctx.cfg)
            _status = None
            _drawn  = False
        else:
            _status = "connecting"
            _draw(ctx)
            ok = ctx.sensor.try_init(3.0)
            if ok:
                ctx.sensor_active           = True
                ctx.cfg["distance_enabled"] = True
                settings.save(ctx.cfg)
                _status = "connected"
            else:
                ctx.sensor_active           = False
                ctx.cfg["distance_enabled"] = False
                _status                     = "no_sensor"
            _drawn = False

    elif ctx.touch.camera_reload_pressed():
        ctx.last_touch = now
        try:
            ctx.cam.reload()
            _status = "cam_ok"
        except Exception as e:
            _status = "cam_err"
            print(f"[Settings] Camera reload failed: {e}")
        _status_at = now
        _drawn     = False

    elif ctx.touch.led_reload_pressed():
        ctx.last_touch = now
        try:
            ctx.led.reload()
            _status = "led_ok"
        except Exception as e:
            _status = "led_err"
            print(f"[Settings] LED reload failed: {e}")
        _status_at = now
        _drawn     = False

    elif ctx.touch.poweroff_pressed():
        ctx.last_touch = now
        if _poweroff_confirm:
            _draw_poweroff(ctx)
            ctx.sensor.shutdown()
            ctx.led.off()
            ctx.cam.stop()
            ctx.display.shutdown()
            subprocess.run(["sudo", "shutdown", "-h", "now"])
        else:
            _poweroff_confirm    = True
            _poweroff_confirm_at = now
            _drawn               = False

    return "settings"
