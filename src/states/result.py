# src/states/result.py - show classification result with captured frame navigation

from PIL import Image, ImageDraw
from src.context import AppContext
from src.ui.color import OK_GREEN, ACCENT, ERR_RED, FG, DIM
from src.ui.helpers import load_font, draw_header
from config import DISPLAY_HEIGHT, DISPLAY_WIDTH, FONT_BOLD, FONT_REGULAR

_LABEL_COLORS = {
    "edible":      OK_GREEN,
    "adulterated": ACCENT,
    "spoiled":     ERR_RED,
}

_drawn = False


def on_enter(ctx: AppContext) -> None:
    global _drawn
    _drawn = False


def _draw(ctx: AppContext, label: str) -> None:
    """Draw the result screen with the captured frame and classification label."""
    canvas = ctx.display.blank_canvas()
    draw   = ImageDraw.Draw(canvas)

    font_label = load_font(FONT_BOLD,    26)
    font_hint  = load_font(FONT_REGULAR, 10)

    cx = DISPLAY_HEIGHT // 2
    draw_header(draw, cx)

    IMG_W = DISPLAY_HEIGHT
    IMG_H = 190
    IMG_Y = 34

    try:
        img = ctx.result_frames[ctx.result_frame_idx].copy().convert("RGB")
        img.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
        ox = (IMG_W - img.width)  // 2
        oy = IMG_Y + (IMG_H - img.height) // 2
        canvas.paste(img, (ox, oy))
    except Exception:
        draw.rectangle((0, IMG_Y, IMG_W, IMG_Y + IMG_H), fill="#1A1A1A")

    label_color = _LABEL_COLORS.get(label, FG)
    draw.text((cx, 240), label.upper(), font=font_label, fill=label_color, anchor="mm")
    draw.text((cx, DISPLAY_WIDTH - 22), "tap \u25cf to scan again", font=font_hint, fill=DIM, anchor="mm")

    ctx.display.flush(canvas)


def run(ctx: AppContext, now: float) -> str:
    global _drawn

    label, conf, probs = ctx.result

    if not _drawn:
        _draw(ctx, label)
        _drawn = True

    if not ctx.debounced(now):
        return "result"

    if ctx.touch.gallery_prev_pressed() and ctx.result_frame_idx > 0:
        ctx.last_touch       = now
        ctx.result_frame_idx -= 1
        _drawn               = False

    elif ctx.touch.gallery_next_pressed() and ctx.result_frame_idx < len(ctx.result_frames) - 1:
        ctx.last_touch       = now
        ctx.result_frame_idx += 1
        _drawn               = False

    elif ctx.touch.shutter_pressed():
        ctx.last_touch    = now
        ctx.result        = None
        ctx.result_frames = []
        ctx.led.on()
        return "preview"

    return "result"
