# src/states/gallery_preview.py - single session image viewer with delete

import os
from PIL import Image, ImageDraw
import src.gallery_store as gallery
from src.context import AppContext
from src.ui.color import ERR_RED, ACCENT, FG, DIM
from src.ui.helpers import load_font, draw_header
from config import DISPLAY_HEIGHT, DISPLAY_WIDTH, FONT_BOLD, FONT_REGULAR

_drawn             = False
_delete_confirm    = False
_delete_confirm_at = 0.0


def on_enter(ctx: AppContext) -> None:
    global _drawn, _delete_confirm
    _drawn          = False
    _delete_confirm = False


def _draw(ctx: AppContext) -> None:
    """Draw the single session preview screen."""
    canvas = ctx.display.blank_canvas()
    draw   = ImageDraw.Draw(canvas)

    font_nav  = load_font(FONT_BOLD,    12)
    font_btn  = load_font(FONT_REGULAR,  9)
    font_hint = load_font(FONT_REGULAR, 10)
    font_idx  = load_font(FONT_REGULAR, 10)

    cx = DISPLAY_HEIGHT // 2
    draw_header(draw, cx)

    session        = ctx.gallery_sessions[ctx.gallery_session_idx]
    total_sessions = len(ctx.gallery_sessions)
    total_frames   = len(session)

    IMG_W = DISPLAY_HEIGHT
    IMG_H = 195
    IMG_Y = 32

    try:
        img = Image.open(session[ctx.gallery_frame_idx]).convert("RGB")
        img.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
        ox = (IMG_W - img.width)  // 2
        oy = IMG_Y + (IMG_H - img.height) // 2
        canvas.paste(img, (ox, oy))
    except Exception:
        draw.rectangle((0, IMG_Y, IMG_W, IMG_Y + IMG_H), fill="#1A1A1A")
        draw.text((cx, IMG_Y + IMG_H // 2), "Error loading image", font=font_hint, fill=DIM, anchor="mm")

    draw.text((cx, 273), f"Scan {ctx.gallery_session_idx + 1} / {total_sessions}", font=font_idx, fill=DIM, anchor="mm")
    draw.text((cx, 285), f"{ctx.gallery_frame_idx + 1} / {total_frames}",           font=font_idx, fill=DIM, anchor="mm")

    if ctx.gallery_frame_idx > 0 or ctx.gallery_session_idx > 0:
        draw.text((14, 285), "< PREV", font=font_nav, fill=ACCENT, anchor="lm")
    if (ctx.gallery_frame_idx < total_frames - 1) or (ctx.gallery_session_idx < total_sessions - 1):
        draw.text((DISPLAY_HEIGHT - 14, 285), "NEXT >", font=font_nav, fill=ACCENT, anchor="rm")

    DEL_CX = 120
    DEL_Y  = 230
    DEL_W  = 44
    DEL_H  = 11

    pill_fill = ERR_RED   if _delete_confirm else "#3A1A1A"
    del_text  = "CONFIRM?" if _delete_confirm else "DELETE"
    del_col   = FG        if _delete_confirm else ERR_RED

    draw.rounded_rectangle(
        (DEL_CX - DEL_W, DEL_Y - DEL_H, DEL_CX + DEL_W, DEL_Y + DEL_H),
        radius=DEL_H, fill=pill_fill, outline=ERR_RED, width=1,
    )
    draw.text((DEL_CX, DEL_Y), del_text, font=font_btn, fill=del_col, anchor="mm")
    draw.text((cx, DISPLAY_WIDTH - 14), "tap \u25cf to go back", font=font_hint, fill=DIM, anchor="mm")

    ctx.display.flush(canvas)


def run(ctx: AppContext, now: float) -> str:
    global _drawn, _delete_confirm, _delete_confirm_at

    if not _drawn:
        _draw(ctx)
        _drawn = True

    if _delete_confirm and (now - _delete_confirm_at) > 3.0:
        _delete_confirm = False
        _drawn          = False

    if not ctx.debounced(now):
        return "gallery_preview"

    session        = ctx.gallery_sessions[ctx.gallery_session_idx]
    total_frames   = len(session)
    total_sessions = len(ctx.gallery_sessions)

    if ctx.touch.shutter_pressed():
        ctx.last_touch  = now
        _delete_confirm = False
        return "gallery"

    elif ctx.touch.gallery_prev_pressed():
        ctx.last_touch  = now
        _delete_confirm = False
        if ctx.gallery_frame_idx > 0:
            ctx.gallery_frame_idx -= 1
        elif ctx.gallery_session_idx > 0:
            ctx.gallery_session_idx -= 1
            ctx.gallery_frame_idx   = len(ctx.gallery_sessions[ctx.gallery_session_idx]) - 1
        _drawn = False

    elif ctx.touch.gallery_next_pressed():
        ctx.last_touch  = now
        _delete_confirm = False
        if ctx.gallery_frame_idx < total_frames - 1:
            ctx.gallery_frame_idx += 1
        elif ctx.gallery_session_idx < total_sessions - 1:
            ctx.gallery_session_idx += 1
            ctx.gallery_frame_idx    = 0
        _drawn = False

    elif ctx.touch.gallery_delete_pressed():
        ctx.last_touch = now
        if _delete_confirm:
            for fp in ctx.gallery_sessions[ctx.gallery_session_idx]:
                try:
                    os.remove(fp)
                except Exception as e:
                    print(f"[Gallery] Delete failed {fp}: {e}")
            ctx.gallery_sessions = gallery.list_sessions()
            _delete_confirm      = False
            if ctx.gallery_session_idx >= len(ctx.gallery_sessions):
                ctx.gallery_session_idx = max(0, len(ctx.gallery_sessions) - 1)
            ctx.gallery_frame_idx = 0
            return "gallery"
        else:
            _delete_confirm    = True
            _delete_confirm_at = now
            _drawn             = False

    return "gallery_preview"
