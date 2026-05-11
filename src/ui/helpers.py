# src/ui.py - shared drawing helpers used across state files
#
# this module exists to avoid duplicating font loading and the standard
# MANOKSENSE header across every state that needs to draw a screen.

from PIL import ImageDraw, ImageFont
from src.ui.color import ACCENT, DIM
from config import DISPLAY_HEIGHT, FONT_BOLD


def load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a TTF font, falling back to PIL default if the file is missing."""
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def draw_header(draw: ImageDraw.ImageDraw, cx: int) -> None:
    """
    Draw the standard MANOKSENSE title and divider line.
    Called at the top of every full-screen state render.
    """
    font = load_font(FONT_BOLD, 14)
    draw.text((cx, 18), "MANOKSENSE", font=font, fill=ACCENT, anchor="mm")
    draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)
