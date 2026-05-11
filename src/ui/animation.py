# src/animation.py — Multi-frame visual sequences
#
# This module contains only genuine animations — screens that involve
# timing, sequencing, or multiple draws over time. Static single-frame
# screen renders belong in their respective state files.

from PIL import ImageDraw
from src.ui.display import DisplayUI
from src.ui.color import ACCENT, DIM, OK_GREEN, ERR_RED, FG
from src.ui.helpers import load_font, draw_header
from config import DISPLAY_WIDTH, DISPLAY_HEIGHT, FONT_REGULAR, FONT_BOLD


class Animation:

    def __init__(self, device: DisplayUI) -> None:
        self._device = device


    # boot sequence
    def show_splash(self) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = load_font(FONT_BOLD,    28)
        font_sub   = load_font(FONT_REGULAR, 11)

        cx, cy  = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2
        rule_y1 = cy - 24
        rule_y2 = cy + 22

        draw.line((30, rule_y1, DISPLAY_HEIGHT - 30, rule_y1), fill=ACCENT, width=1)
        draw.line((30, rule_y2, DISPLAY_HEIGHT - 30, rule_y2), fill=ACCENT, width=1)
        draw.text((cx, cy - 4),  "MANOKSENSE",                font=font_title, fill=ACCENT, anchor="mm")
        draw.text((cx, cy + 36), "chicken quality classifier", font=font_sub,   fill=DIM,    anchor="mm")

        self._device.flush(canvas)

    def show_boot_step(self, steps: list, progress: float = 0.0) -> None:
        """
        Re-drawn after each hardware init step — the progress bar
        and status labels advance over time, making this a genuine animation.
        """
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_step   = load_font(FONT_REGULAR, 12)
        font_status = load_font(FONT_BOLD,    12)

        cx = DISPLAY_HEIGHT // 2
        draw_header(draw, cx)

        row_start  = 58
        row_gap    = 28
        col_label  = 32
        col_status = DISPLAY_HEIGHT - 32

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

            draw.text((col_label,  y), label,       font=font_step,   fill=label_color,  anchor="lm")
            if status_text:
                draw.text((col_status, y), status_text, font=font_status, fill=status_color, anchor="rm")

        bar_x1 = 20
        bar_x2 = DISPLAY_HEIGHT - 20
        bar_y  = DISPLAY_WIDTH - 24
        bar_h  = 6

        draw.rounded_rectangle((bar_x1, bar_y, bar_x2, bar_y + bar_h), radius=3, fill=DIM)
        if progress > 0:
            fill_x2 = bar_x1 + int((bar_x2 - bar_x1) * min(progress, 1.0))
            if fill_x2 > bar_x1:
                draw.rounded_rectangle((bar_x1, bar_y, fill_x2, bar_y + bar_h), radius=3, fill=ACCENT)

        self._device.flush(canvas)

    def show_ready(self) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_big = load_font(FONT_BOLD,    22)
        font_sub = load_font(FONT_REGULAR, 11)

        cx, cy = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2

        draw.text((cx, cy - 8),  "Ready.",              font=font_big, fill=OK_GREEN, anchor="mm")
        draw.text((cx, cy + 20), "starting preview...", font=font_sub, fill=DIM,      anchor="mm")

        self._device.flush(canvas)

    # capture progress
    def show_capture_progress(self, current: int, total: int) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_big  = load_font(FONT_BOLD,    28)
        font_sub  = load_font(FONT_REGULAR, 11)
        font_hint = load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2
        draw_header(draw, cx)

        draw.text((cx, 120), f"Photo {current} / {total}", font=font_big, fill=FG,  anchor="mm")
        draw.text((cx, 155), "hold steady...",              font=font_sub, fill=DIM, anchor="mm")

        dot_r   = 7
        dot_gap = 28
        dot_y   = 195
        dot_x0  = cx - ((total - 1) * dot_gap) // 2

        for i in range(total):
            dot_x  = dot_x0 + i * dot_gap
            filled = i < current
            color  = ACCENT if filled else DIM
            draw.ellipse(
                (dot_x - dot_r, dot_y - dot_r, dot_x + dot_r, dot_y + dot_r),
                fill=color if filled else None,
                outline=color,
                width=2,
            )

        draw.text((cx, DISPLAY_WIDTH - 22), "capturing sample...", font=font_hint, fill=DIM, anchor="mm")
        self._device.flush(canvas)

    # processing
    def show_processing(self) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_big = load_font(FONT_BOLD,    22)
        font_sub = load_font(FONT_REGULAR, 11)

        cx = DISPLAY_HEIGHT // 2
        draw_header(draw, cx)

        draw.text((cx, 145), "Analyzing...", font=font_big, fill=FG,  anchor="mm")
        draw.text((cx, 172), "please wait",  font=font_sub, fill=DIM, anchor="mm")

        self._device.flush(canvas)
