# src/states/gallery.py - 3x3 thumbnail grid navigation

from PIL import ImageDraw
import src.gallery_store as gallery
from src.context import AppContext
from src.ui.color import ACCENT, DIM, FG
from src.ui.helpers import load_font, draw_header
from config import DISPLAY_HEIGHT, DISPLAY_WIDTH, FONT_BOLD, FONT_REGULAR

_PER_PAGE = 9
_drawn    = False


def on_enter(ctx: AppContext) -> None:
    global _drawn
    ctx.gallery_sessions = gallery.list_sessions()
    ctx.gallery_page     = 0
    _drawn               = False


def _draw(ctx: AppContext) -> None:
    """Draw the gallery thumbnail grid."""
    canvas = ctx.display.blank_canvas()
    draw   = ImageDraw.Draw(canvas)

    font_sub  = load_font(FONT_BOLD,    11)
    font_hint = load_font(FONT_REGULAR, 10)
    font_nav  = load_font(FONT_BOLD,    12)

    cx    = DISPLAY_HEIGHT // 2
    total = len(ctx.gallery_sessions)

    draw_header(draw, cx)
    draw.text((cx, 38), f"Gallery  ({total})", font=font_sub, fill=FG, anchor="mm")
    draw.line((20, 50, DISPLAY_HEIGHT - 20, 50), fill=DIM, width=1)

    if total == 0:
        draw.text((cx, 160), "No captures yet", font=font_sub, fill=DIM, anchor="mm")
        draw.text((cx, DISPLAY_WIDTH - 22), "tap \u25cf to go back", font=font_hint, fill=DIM, anchor="mm")
        ctx.display.flush(canvas)
        return

    COLS   = 3
    THUMB_W = 72
    THUMB_H = 72
    GAP_X   = 4
    GAP_Y   = 4
    START_X = 4
    START_Y = 56

    page_sessions = ctx.gallery_sessions[ctx.gallery_page * _PER_PAGE : (ctx.gallery_page + 1) * _PER_PAGE]

    for i, session in enumerate(page_sessions):
        col = i % COLS
        row = i // COLS
        x   = START_X + col * (THUMB_W + GAP_X)
        y   = START_Y + row * (THUMB_H + GAP_Y)

        thumb = gallery.make_thumbnail(session[0])
        canvas.paste(thumb, (x, y))

        label = gallery.get_label_from_filename(session[0])
        color = gallery.LABEL_COLORS.get(label, DIM)
        dot_r = 5
        draw.ellipse(
            (x + 4, y + THUMB_H - dot_r * 2 - 4,
             x + 4 + dot_r * 2, y + THUMB_H - 4),
            fill=color,
        )

    total_pages = max(1, (total + _PER_PAGE - 1) // _PER_PAGE)
    NAV_Y = 290

    if ctx.gallery_page > 0:
        draw.text((30, NAV_Y), "< PREV", font=font_nav, fill=ACCENT, anchor="mm")
    draw.text((cx, NAV_Y), f"{ctx.gallery_page + 1} / {total_pages}", font=font_nav, fill=DIM, anchor="mm")
    if (ctx.gallery_page + 1) < total_pages:
        draw.text((210, NAV_Y), "NEXT >", font=font_nav, fill=ACCENT, anchor="mm")

    draw.text((cx, DISPLAY_WIDTH - 14), "tap \u25cf to go back", font=font_hint, fill=DIM, anchor="mm")

    ctx.display.flush(canvas)


def run(ctx: AppContext, now: float) -> str:
    global _drawn

    if not _drawn:
        _draw(ctx)
        _drawn = True

    if not ctx.debounced(now):
        return "gallery"

    total_pages = max(1, (len(ctx.gallery_sessions) + _PER_PAGE - 1) // _PER_PAGE)

    if ctx.touch.shutter_pressed():
        ctx.last_touch = now
        return "preview"

    elif ctx.touch.gallery_prev_pressed() and ctx.gallery_page > 0:
        ctx.last_touch   = now
        ctx.gallery_page -= 1
        _drawn           = False

    elif ctx.touch.gallery_next_pressed() and ctx.gallery_page + 1 < total_pages:
        ctx.last_touch   = now
        ctx.gallery_page += 1
        _drawn           = False

    else:
        idx = ctx.touch.thumbnail_tapped(ctx.gallery_page, ctx.gallery_sessions)
        if idx is not None:
            ctx.last_touch          = now
            ctx.gallery_session_idx = idx
            ctx.gallery_frame_idx   = 0
            return "gallery_preview"

    return "gallery"
