# src/animation.py

# TODO cleanup animation.py

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

        self._device.flush(canvas)  

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

        self._device.flush(canvas)  

    def show_ready(self) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_big = _load_font(FONT_BOLD, 22)
        font_sub = _load_font(FONT_REGULAR, 11)

        cx, cy = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2  # 120, 160

        draw.text((cx, cy - 8),  "Ready.", font=font_big, fill=OK_GREEN, anchor="mm")
        draw.text((cx, cy + 20), "starting preview...", font=font_sub, fill=DIM, anchor="mm")

        self._device.flush(canvas)

    # ------------------------------------------------------------------ #
    #  Inference screens                                                   #
    # ------------------------------------------------------------------ #

    def show_processing(self) -> None:
        """Shown while the classifier is running."""
        canvas = self._device.blank_canvas()          # 240 × 320
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_big   = _load_font(FONT_BOLD,    22)
        font_sub   = _load_font(FONT_REGULAR, 11)

        cx = DISPLAY_HEIGHT // 2   # 120

        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        draw.text((cx, 145), "Analyzing...", font=font_big,  fill=FG,  anchor="mm")
        draw.text((cx, 172), "please wait", font=font_sub, fill=DIM, anchor="mm")

        self._device.flush(canvas)
    
    def show_capture_progress(self, current: int, total: int) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_big   = _load_font(FONT_BOLD,    28)
        font_sub   = _load_font(FONT_REGULAR, 11)
        font_hint  = _load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2   # 120

        # ── Header ──────────────────────────────────────────────────────────
        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        # ── Photo counter ────────────────────────────────────────────────────
        draw.text((cx, 120), f"Photo {current} / {total}",
                  font=font_big, fill=FG, anchor="mm")
        draw.text((cx, 155), "hold steady...",
                  font=font_sub, fill=DIM, anchor="mm")

        # ── Dot indicators ───────────────────────────────────────────────────
        dot_r    = 7
        dot_gap  = 28
        dot_y    = 195
        dot_x0   = cx - ((total - 1) * dot_gap) // 2

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

        # ── Bottom hint ──────────────────────────────────────────────────────
        draw.text(
            (cx, DISPLAY_WIDTH - 22),
            "capturing sample...",
            font=font_hint, fill=DIM, anchor="mm",
        )

        self._device.flush(canvas)

    def show_result(
        self,
        label:      str,
        confidence: float,
        probs:      list[float],
    ) -> None:
        """
        Full-screen result view.

        Layout (240 wide × 320 tall canvas):
          y= 18  MANOKSENSE header
          y= 30  rule
          y= 88  big class label  (colored)
          y=122  confidence %
          y=148  separator rule
          y=165  probability bars  (3 × 28 px rows)
          y=298  "tap to scan again" hint
        """
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_label = _load_font(FONT_BOLD,    30)
        font_pct   = _load_font(FONT_BOLD,    18)
        font_bar   = _load_font(FONT_REGULAR, 10)
        font_hint  = _load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2   # 120

        # ── Header ──────────────────────────────────────────────────────
        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        # ── Result colour ────────────────────────────────────────────────
        color_map = {
            "edible":      OK_GREEN,
            "adulterated": ACCENT,    # amber = caution
            "spoiled":     ERR_RED,
        }
        label_color = color_map.get(label, FG)

        # ── Big label + confidence ───────────────────────────────────────
        draw.text((cx,  88), label.upper(), font=font_label, fill=label_color, anchor="mm")
        draw.text((cx, 122), f"{confidence * 100:.1f}%", font=font_pct, fill=FG, anchor="mm")

        # ── Separator ────────────────────────────────────────────────────
        draw.line((20, 148, DISPLAY_HEIGHT - 20, 148), fill=DIM, width=1)

        # ── Probability bars ─────────────────────────────────────────────
        #   columns:  [label]  [bar──────────────]  [pct]
        #   x:         30       36 ────────── 196    200
        BAR_X0   = 36
        BAR_X1   = 196          # 160 px wide at 100 %
        BAR_MAX  = BAR_X1 - BAR_X0
        BAR_H    = 9
        BAR_BG   = "#252525"

        CLASS_NAMES = ["adulterated", "edible", "spoiled"]
        bar_colors  = [ACCENT, OK_GREEN, ERR_RED]

        for i, (name, prob, bar_color) in enumerate(
            zip(CLASS_NAMES, probs, bar_colors)
        ):
            row_y      = 165 + i * 28
            label_text = name[:3].upper()            # ADU / EDI / SPO
            pct_text   = f"{prob * 100:.0f}%"
            fill_w     = int(BAR_MAX * prob)

            # Short label, right-aligned into the label column
            draw.text((30, row_y + BAR_H // 2), label_text,
                      font=font_bar, fill=DIM, anchor="rm")

            # Background track
            draw.rounded_rectangle(
                (BAR_X0, row_y, BAR_X1, row_y + BAR_H),
                radius=3, fill=BAR_BG,
            )

            # Filled portion
            if fill_w > 2:
                draw.rounded_rectangle(
                    (BAR_X0, row_y, BAR_X0 + fill_w, row_y + BAR_H),
                    radius=3, fill=bar_color,
                )

            # Percentage, left-aligned after bar
            draw.text((BAR_X1 + 4, row_y + BAR_H // 2), pct_text,
                      font=font_bar, fill=FG, anchor="lm")

        # ── Bottom hint ──────────────────────────────────────────────────
        draw.text(
            (cx, DISPLAY_WIDTH - 22),
            "tap to scan again",
            font=font_hint, fill=DIM, anchor="mm",
        )

        self._device.flush(canvas)

    # settings ui
    def show_settings(
        self,
        distance_enabled: bool,
        status: str | None = None,
        poweroff_confirm: bool = False,
    ) -> None:
        """
        Layout (240w × 320h canvas):
          y= 18   MANOKSENSE header
          y= 30   rule
          y= 50   "Settings" subtitle
          y= 63   separator

          ── CONFIG ──────────────────────────────
          y= 76   "CONFIG" section label
          y= 96   Distance sensor toggle
          y= 116  divider
          y= 128  status message (connecting / connected / no_sensor)

          ── SYSTEM ──────────────────────────────
          y= 138  "SYSTEM" section bar (filled)
          y= 156  Camera reload
          y= 172  divider
          y= 192  LED reload
          y= 208  divider
          y= 228  Power off
          y= 248  divider

          y= 298  "tap ● to go back" hint
        """
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title   = _load_font(FONT_BOLD,    14)
        font_sub     = _load_font(FONT_BOLD,    13)
        font_section = _load_font(FONT_BOLD,    9)
        font_label   = _load_font(FONT_REGULAR, 12)
        font_btn     = _load_font(FONT_REGULAR, 9)
        font_status  = _load_font(FONT_REGULAR, 10)
        font_hint    = _load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2   # 120

        # ── Header ──────────────────────────────────────────────────────
        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        draw.text((cx, 50), "Settings", font=font_sub, fill=FG, anchor="mm")
        draw.line((20, 63, DISPLAY_HEIGHT - 20, 63), fill=DIM, width=1)

        # ════════════════════════════════════════════════════════════════
        #  CONFIG section
        # ════════════════════════════════════════════════════════════════
        draw.text((20, 76), "CONFIG", font=font_section, fill=DIM, anchor="lm")

        # Distance sensor toggle
        ROW_Y     = 96
        TOGGLE_CX = 189
        PILL_W    = 40
        PILL_H    = 11
        KNOB_R    = 9

        draw.text((20, ROW_Y), "Distance sensor",
                  font=font_label, fill=FG, anchor="lm")

        pill_color = OK_GREEN if distance_enabled else DIM
        draw.rounded_rectangle(
            (TOGGLE_CX - PILL_W, ROW_Y - PILL_H,
             TOGGLE_CX + PILL_W, ROW_Y + PILL_H),
            radius=PILL_H, fill=pill_color,
        )
        knob_x = (TOGGLE_CX + PILL_W - KNOB_R - 2) if distance_enabled \
             else (TOGGLE_CX - PILL_W + KNOB_R + 2)
        draw.ellipse(
            (knob_x - KNOB_R, ROW_Y - KNOB_R,
             knob_x + KNOB_R, ROW_Y + KNOB_R),
            fill=FG,
        )

        draw.line((20, 116, DISPLAY_HEIGHT - 20, 116), fill="#1E1E1E", width=1)

        if status is not None:
            msg, msg_color = {
                "connecting": ("Connecting...",      ACCENT),
                "connected":  ("Connected",          OK_GREEN),
                "no_sensor":  ("No sensor detected", ERR_RED),
            }.get(status, (status, DIM))
            draw.text((cx, 128), msg,
                      font=font_status, fill=msg_color, anchor="mm")

        # ════════════════════════════════════════════════════════════════
        #  SYSTEM section
        # ════════════════════════════════════════════════════════════════
        draw.rectangle((0, 136, DISPLAY_HEIGHT, 152), fill="#151515")
        draw.text((20, 144), "SYSTEM", font=font_section, fill=DIM, anchor="lm")

        BTN_CX = 189
        BTN_W  = 40
        BTN_H  = 12

        # ── Camera reload ────────────────────────────────────────────────
        CAM_Y = 156
        draw.text((20, CAM_Y), "Camera", font=font_label, fill=FG, anchor="lm")
        draw.rounded_rectangle(
            (BTN_CX - BTN_W, CAM_Y - BTN_H,
             BTN_CX + BTN_W, CAM_Y + BTN_H),
            radius=BTN_H, fill="#1A1A2A", outline="#4A6AE8", width=1,
        )
        draw.text((BTN_CX, CAM_Y), "RELOAD",
                  font=font_btn, fill="#4A6AE8", anchor="mm")
        draw.line((20, 172, DISPLAY_HEIGHT - 20, 172), fill="#1E1E1E", width=1)

        # ── LED reload ───────────────────────────────────────────────────
        LED_Y = 192
        draw.text((20, LED_Y), "LED strip", font=font_label, fill=FG, anchor="lm")
        draw.rounded_rectangle(
            (BTN_CX - BTN_W, LED_Y - BTN_H,
             BTN_CX + BTN_W, LED_Y + BTN_H),
            radius=BTN_H, fill="#1A2A1A", outline=OK_GREEN, width=1,
        )
        draw.text((BTN_CX, LED_Y), "RELOAD",
                  font=font_btn, fill=OK_GREEN, anchor="mm")
        draw.line((20, 208, DISPLAY_HEIGHT - 20, 208), fill="#1E1E1E", width=1)

        # ── Power off ────────────────────────────────────────────────────
        POFF_Y     = 228
        pill_fill  = ERR_RED  if poweroff_confirm else "#3A1A1A"
        label_text = "CONFIRM?" if poweroff_confirm else "SHUT DOWN"
        label_col  = FG       if poweroff_confirm else ERR_RED

        draw.text((20, POFF_Y), "Power off", font=font_label, fill=FG, anchor="lm")
        draw.rounded_rectangle(
            (BTN_CX - BTN_W, POFF_Y - BTN_H,
             BTN_CX + BTN_W, POFF_Y + BTN_H),
            radius=BTN_H, fill=pill_fill, outline=ERR_RED, width=1,
        )
        draw.text((BTN_CX, POFF_Y), label_text,
                  font=font_btn, fill=label_col, anchor="mm")
        draw.line((20, 244, DISPLAY_HEIGHT - 20, 244), fill="#1E1E1E", width=1)

        # ── Bottom hint ──────────────────────────────────────────────────
        draw.text((cx, DISPLAY_WIDTH - 22), "tap \u25cf to go back",
                  font=font_hint, fill=DIM, anchor="mm")

        self._device.flush(canvas)

    # gallery ui
    def show_gallery(self, files: list[str], page: int) -> None:
        """
        Layout (240w × 320h canvas):
          y=18   header
          y=30   rule
          y=48   "Gallery" + count
          y=62   separator
          y=68   3×3 thumbnail grid  (72×72 each, 2px gap)
          y=285  prev ←   N/M   next →
          y=298  hint
        """
        import src.gallery as gallery

        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_sub   = _load_font(FONT_BOLD,    11)
        font_hint  = _load_font(FONT_REGULAR, 10)
        font_nav   = _load_font(FONT_BOLD,    12)

        cx = DISPLAY_HEIGHT // 2   # 120

        # ── Header ──────────────────────────────────────────────────────
        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        total = len(files)
        draw.text((cx, 48), f"Gallery  ({total})",
                  font=font_sub, fill=FG, anchor="mm")
        draw.line((20, 62, DISPLAY_HEIGHT - 20, 62), fill=DIM, width=1)

        # ── Empty state ──────────────────────────────────────────────────
        if total == 0:
            draw.text((cx, 160), "No captures yet",
                      font=font_sub, fill=DIM, anchor="mm")
            draw.text((cx, DISPLAY_WIDTH - 22), "tap ● to go back",
                      font=font_hint, fill=DIM, anchor="mm")
            self._device.flush(canvas)
            return

        # ── Grid ─────────────────────────────────────────────────────────
        PER_PAGE  = 9
        COLS      = 3
        THUMB_W   = 72
        THUMB_H   = 72
        GAP_X     = 4
        GAP_Y     = 4
        START_X   = (DISPLAY_HEIGHT - COLS * THUMB_W - (COLS - 1) * GAP_X) // 2   # 4
        START_Y   = 68

        start_idx = page * PER_PAGE
        page_files = files[start_idx : start_idx + PER_PAGE]

        for i, filepath in enumerate(page_files):
            col = i % COLS
            row = i // COLS
            x   = START_X + col * (THUMB_W + GAP_X)
            y   = START_Y + row * (THUMB_H + GAP_Y)

            thumb = gallery.make_thumbnail(filepath)
            canvas.paste(thumb, (x, y))

            # Label color dot — bottom-left corner
            label  = gallery.get_label_from_filename(filepath)
            color  = gallery.LABEL_COLORS.get(label, "#555555")
            dot_r  = 5
            draw.ellipse(
                (x + 4, y + THUMB_H - dot_r * 2 - 4,
                 x + 4 + dot_r * 2, y + THUMB_H - 4),
                fill=color,
            )

        # ── Pagination ────────────────────────────────────────────────────
        total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        NAV_Y = 285

        if page > 0:
            draw.text((30, NAV_Y), "< PREV",
                      font=font_nav, fill=ACCENT, anchor="mm")

        draw.text((cx, NAV_Y), f"{page + 1} / {total_pages}",
                  font=font_nav, fill=DIM, anchor="mm")

        if (page + 1) < total_pages:
            draw.text((210, NAV_Y), "NEXT >",
                      font=font_nav, fill=ACCENT, anchor="mm")

        draw.text((cx, DISPLAY_WIDTH - 22), "tap ● to go back",
                  font=font_hint, fill=DIM, anchor="mm")

        self._device.flush(canvas)

    # poweroff screen
    def show_poweroff(self) -> None:
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_big   = _load_font(FONT_BOLD,    20)
        font_sub   = _load_font(FONT_REGULAR, 11)

        cx, cy = DISPLAY_HEIGHT // 2, DISPLAY_WIDTH // 2

        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)
        draw.text((cx, cy - 10), "Shutting down...", font=font_big, fill=FG,   anchor="mm")
        draw.text((cx, cy + 18), "safe to unplug",   font=font_sub, fill=DIM, anchor="mm")

        self._device.flush(canvas)
