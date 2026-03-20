from PIL import Image, ImageDraw, ImageFont
from .display import DisplayUI
from .color import ACCENT, DIM, OK_GREEN, ERR_RED, FG
from config import (
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    FONT_REGULAR,
    FONT_BOLD,
)

def _load_font(font: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(font, size)
    except OSError:
        return ImageFont.load_default()

class Animation:
    def __init__(self, device: DisplayUI):
        self._device = device

    # ------------------------------------------------------------------ #
    #  Boot sequence helpers                                               #
    # ------------------------------------------------------------------ #

    def show_splash(self) -> None:
        canvas = self._device.blank_canvas()          # ← 240×320
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD, 28)
        font_sub   = _load_font(FONT_REGULAR, 11)

        cx, cy = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2  # 120, 160

        rule_y1 = cy - 24
        rule_y2 = cy + 22
        draw.line((30, rule_y1, DISPLAY_HEIGHT - 30, rule_y1), fill=ACCENT, width=1)
        draw.line((30, rule_y2, DISPLAY_HEIGHT - 30, rule_y2), fill=ACCENT, width=1)

        draw.text((cx, cy - 4), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.text((cx, cy + 36), "chicken quality classifier", font=font_sub, fill=DIM, anchor="mm")

        self._device.flush(canvas.rotate(90, expand=True))  

    def show_boot_step(self, steps, progress=0.0) -> None:
        canvas = self._device.blank_canvas()          
        draw   = ImageDraw.Draw(canvas)

        font_title  = _load_font(FONT_BOLD, 14)
        font_step   = _load_font(FONT_REGULAR, 12)
        font_status = _load_font(FONT_BOLD, 12)

        cx = DISPLAY_HEIGHT // 2  # 120

        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        row_start  = 58
        row_gap    = 28
        col_label  = 32
        col_status = DISPLAY_HEIGHT - 32  # 208

        for i, (label, status) in enumerate(steps):
            y = row_start + i * row_gap

            if status is None:
                label_color, status_text, status_color = DIM, "", DIM
            elif status == "...":
                label_color, status_text, status_color = FG, "...", ACCENT
            elif status == "OK":
                label_color, status_text, status_color = FG, "OK", OK_GREEN
            elif status == "ERR":
                label_color, status_text, status_color = ERR_RED, "ERR", ERR_RED
            else:
                label_color, status_text, status_color = FG, status, FG

            draw.text((col_label, y), label, font=font_step, fill=label_color, anchor="lm")
            if status_text:
                draw.text((col_status, y), status_text, font=font_status, fill=status_color, anchor="rm")

        bar_x1 = 20
        bar_x2 = DISPLAY_HEIGHT - 20   # 220
        bar_y  = DISPLAY_WIDTH - 24    # 296
        bar_h  = 6

        draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + bar_h), radius=3, fill=DIM)
        if progress > 0:
            fill_x2 = bar_x1 + int((bar_x2 - bar_x1) * min(progress, 1.0))
            if fill_x2 > bar_x1:
                draw.rounded_rectangle((bar_x1, bar_y, fill_x2, bar_y + bar_h), radius=3, fill=ACCENT)

        self._device.flush(canvas.rotate(90, expand=True))  # back to 320×240 ✓

    def show_ready(self) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_big = _load_font(FONT_BOLD, 22)
        font_sub = _load_font(FONT_REGULAR, 11)

        cx, cy = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2  # 120, 160

        draw.text((cx, cy - 8),  "Ready.", font=font_big, fill=OK_GREEN, anchor="mm")
        draw.text((cx, cy + 20), "starting preview...", font=font_sub, fill=DIM, anchor="mm")

        self._device.flush(canvas.rotate(90, expand=True))  # back to 320×240 


