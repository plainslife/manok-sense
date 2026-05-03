# src/animation.py

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

    def show_boot_step(self, steps: list, progress: float = 0.0) -> None:
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

        # ── Bottom hint ──────────────────────────────────────────────────────
        draw.text(
            (cx, DISPLAY_WIDTH - 22),
            "capturing sample...",
            font=font_hint, fill=DIM, anchor="mm",
        )

        self._device.flush(canvas)

    def show_result(self, label: str) -> None:
        """
        Simplified result view — big label only, vertically centered.

        Layout (240w × 320h canvas):
          y= 18   MANOKSENSE header
          y= 30   rule
          y=164   big class label (colored, centered in remaining space)
          y=298   "tap to scan again" hint
        """
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_label = _load_font(FONT_BOLD,    34)
        font_hint  = _load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2   # 120

        # ── Header ──────────────────────────────────────────────────────
        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        _LABEL_COLORS = {
            "edible":      OK_GREEN,
            "adulterated": ACCENT,
            "spoiled":     ERR_RED,
        }
        label_color = _LABEL_COLORS.get(label, FG)
        draw.text((cx, 164), label.upper(), font=font_label, fill=label_color, anchor="mm")

        # ── Bottom hint ──────────────────────────────────────────────────
        draw.text(
            (cx, DISPLAY_WIDTH - 22),
            "tap \u25cf to scan again",
            font=font_hint, fill=DIM, anchor="mm",
        )

        self._device.flush(canvas)

    def show_result_with_frame(
        self,
        frames:    list,
        frame_idx: int,
        label:     str,
    ) -> None:
        """
        Result view with the captured frame shown above the label.

        Layout (240w × 320h canvas):
          y= 18   MANOKSENSE header
          y= 30   rule
          y= 32   captured frame image (fitted to 240×190)
          y=240   big class label (colored)
          y=298   "tap ● to scan again" hint
        """
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_label = _load_font(FONT_BOLD,    26)
        font_hint  = _load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2   # 120

        # ── Header ──────────────────────────────────────────────────────
        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        # ── Frame image ──────────────────────────────────────────────────
        IMG_W = DISPLAY_HEIGHT   # 240
        IMG_H = 190
        IMG_Y = 34

        try:
            img = frames[0].copy().convert("RGB")
            img.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
            ox = (IMG_W - img.width)  // 2
            oy = IMG_Y + (IMG_H - img.height) // 2
            canvas.paste(img, (ox, oy))
        except Exception:
            draw.rectangle((0, IMG_Y, IMG_W, IMG_Y + IMG_H), fill="#1A1A1A")

        # ── Label ────────────────────────────────────────────────────────
        _LABEL_COLORS = {
            "edible":      OK_GREEN,
            "adulterated": ACCENT,
            "spoiled":     ERR_RED,
        }
        label_color = _LABEL_COLORS.get(label, FG)
        draw.text((cx, 240), label.upper(), font=font_label, fill=label_color, anchor="mm")

        # ── Bottom hint ──────────────────────────────────────────────────
        draw.text(
            (cx, DISPLAY_WIDTH - 22),
            "tap \u25cf to scan again",
            font=font_hint, fill=DIM, anchor="mm",
        )

        self._device.flush(canvas)

    # ------------------------------------------------------------------ #
    #  Settings UI                                                         #
    # ------------------------------------------------------------------ #

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
          y= 138  "SYSTEM" section label
          y= 156  Camera reload   (button label swaps on cam_ok / cam_err)
          y= 172  divider
          y= 192  LED reload      (button label swaps on led_ok / led_err)
          y= 208  divider
          y= 228  Power off
          y= 248  divider

          y= 298  "tap ● to go back" hint

        `status` values:
          None          — idle
          "connecting"  — amber  "Connecting..."      (distance row)
          "connected"   — green  "Connected"          (distance row)
          "no_sensor"   — red    "No sensor detected" (distance row)
          "cam_ok"      — green  Camera button → "DONE"
          "cam_err"     — red    Camera button → "FAILED"
          "led_ok"      — green  LED button    → "DONE"
          "led_err"     — red    LED button    → "FAILED"
        """
        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title   = _load_font(FONT_BOLD,    14)
        font_sub     = _load_font(FONT_BOLD,    13)
        font_section = _load_font(FONT_BOLD,     9)
        font_label   = _load_font(FONT_REGULAR, 12)
        font_btn     = _load_font(FONT_REGULAR,  9)
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

        # Distance status message
        if status in ("connecting", "connected", "no_sensor"):
            msg, msg_color = {
                "connecting": ("Connecting...",       ACCENT),
                "connected":  ("Connected",           OK_GREEN),
                "no_sensor":  ("No sensor detected",  ERR_RED),
            }[status]
            draw.text((cx, 128), msg,
                      font=font_status, fill=msg_color, anchor="mm")

        # ════════════════════════════════════════════════════════════════
        #  SYSTEM section
        # ════════════════════════════════════════════════════════════════
        draw.text((20, 136), "SYSTEM", font=font_section, fill=DIM, anchor="lm")

        BTN_CX = 189
        BTN_W  = 40
        BTN_H  = 12

        # ── Camera reload ────────────────────────────────────────────────
        CAM_Y = 156
        if status == "cam_ok":
            cam_fill, cam_outline, cam_text, cam_col = "#0A0A2A", "#4A6AE8", "DONE",   OK_GREEN
        elif status == "cam_err":
            cam_fill, cam_outline, cam_text, cam_col = "#2A0A0A", ERR_RED,  "FAILED", ERR_RED
        else:
            cam_fill, cam_outline, cam_text, cam_col = "#1A1A2A", "#4A6AE8", "RELOAD", "#4A6AE8"

        draw.text((20, CAM_Y), "Camera", font=font_label, fill=FG, anchor="lm")
        draw.rounded_rectangle(
            (BTN_CX - BTN_W, CAM_Y - BTN_H,
             BTN_CX + BTN_W, CAM_Y + BTN_H),
            radius=BTN_H, fill=cam_fill, outline=cam_outline, width=1,
        )
        draw.text((BTN_CX, CAM_Y), cam_text, font=font_btn, fill=cam_col, anchor="mm")
        draw.line((20, 172, DISPLAY_HEIGHT - 20, 172), fill="#1E1E1E", width=1)

        # ── LED reload ───────────────────────────────────────────────────
        LED_Y = 192
        if status == "led_ok":
            led_fill, led_outline, led_text, led_col = "#0A2A0A", OK_GREEN, "DONE",   OK_GREEN
        elif status == "led_err":
            led_fill, led_outline, led_text, led_col = "#2A0A0A", ERR_RED,  "FAILED", ERR_RED
        else:
            led_fill, led_outline, led_text, led_col = "#1A2A1A", OK_GREEN,  "RELOAD", OK_GREEN

        draw.text((20, LED_Y), "LED strip", font=font_label, fill=FG, anchor="lm")
        draw.rounded_rectangle(
            (BTN_CX - BTN_W, LED_Y - BTN_H,
             BTN_CX + BTN_W, LED_Y + BTN_H),
            radius=BTN_H, fill=led_fill, outline=led_outline, width=1,
        )
        draw.text((BTN_CX, LED_Y), led_text, font=font_btn, fill=led_col, anchor="mm")
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

    # ------------------------------------------------------------------ #
    #  Gallery UI                                                          #
    # ------------------------------------------------------------------ #

    def show_gallery(self, sessions: list[list[str]], page: int) -> None:
        """
        Layout (240w × 320h canvas):
          y=18   header
          y=30   rule
          y=48   "Gallery" + session count
          y=62   separator
          y=56   3×3 thumbnail grid  (72×72 each, 4px gap)
          y=290  prev ←   N/M   next →
          y=306  hint
        """
        import src.gallery as gallery

        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_sub   = _load_font(FONT_BOLD,    11)
        font_hint  = _load_font(FONT_REGULAR, 10)
        font_nav   = _load_font(FONT_BOLD,    12)

        cx = DISPLAY_HEIGHT // 2   # 120

        draw.text((cx, 16), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 26, DISPLAY_HEIGHT - 30, 26), fill=DIM, width=1)

        total = len(sessions)
        draw.text((cx, 38), f"Gallery  ({total})",
                  font=font_sub, fill=FG, anchor="mm")
        draw.line((20, 50, DISPLAY_HEIGHT - 20, 50), fill=DIM, width=1)

        if total == 0:
            draw.text((cx, 160), "No captures yet",
                      font=font_sub, fill=DIM, anchor="mm")
            draw.text((cx, DISPLAY_WIDTH - 22), "tap \u25cf to go back",
                      font=font_hint, fill=DIM, anchor="mm")
            self._device.flush(canvas)
            return

        PER_PAGE = 9
        COLS     = 3
        THUMB_W  = 72
        THUMB_H  = 72
        GAP_X    = 4
        GAP_Y    = 4
        START_X  = 4
        START_Y  = 56

        start_idx     = page * PER_PAGE
        page_sessions = sessions[start_idx : start_idx + PER_PAGE]

        for i, session in enumerate(page_sessions):
            col = i % COLS
            row = i // COLS
            x   = START_X + col * (THUMB_W + GAP_X)
            y   = START_Y + row * (THUMB_H + GAP_Y)

            thumb = gallery.make_thumbnail(session[0])
            canvas.paste(thumb, (x, y))

            label = gallery.get_label_from_filename(session[0])
            color = gallery.LABEL_COLORS.get(label, "#555555")
            dot_r = 5
            draw.ellipse(
                (x + 4, y + THUMB_H - dot_r * 2 - 4,
                 x + 4 + dot_r * 2, y + THUMB_H - 4),
                fill=color,
            )

        total_pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
        NAV_Y = 290

        if page > 0:
            draw.text((30, NAV_Y), "< PREV", font=font_nav, fill=ACCENT, anchor="mm")
        draw.text((cx, NAV_Y), f"{page + 1} / {total_pages}",
                  font=font_nav, fill=DIM, anchor="mm")
        if (page + 1) < total_pages:
            draw.text((210, NAV_Y), "NEXT >", font=font_nav, fill=ACCENT, anchor="mm")

        draw.text((cx, DISPLAY_WIDTH - 14), "tap \u25cf to go back",
                  font=font_hint, fill=DIM, anchor="mm")

        self._device.flush(canvas)

    def show_gallery_preview(
        self,
        sessions:       list[list[str]],
        session_idx:    int,
        frame_idx:      int,
        delete_confirm: bool = False,
    ) -> None:
        """
        Layout (240w × 320h canvas):
          y= 18   header
          y= 30   rule
          y= 32   full image (fitted to 240×195)
          y=273   "Scan N / M"  session indicator
          y=285   "1 / 3"       frame indicator with < > arrows
          y=230   DELETE button
          y=306   "tap ● to go back" hint
        """
        import src.gallery as gallery

        canvas = self._device.blank_canvas()
        draw   = ImageDraw.Draw(canvas)

        font_title = _load_font(FONT_BOLD,    14)
        font_nav   = _load_font(FONT_BOLD,    12)
        font_btn   = _load_font(FONT_REGULAR,  9)
        font_hint  = _load_font(FONT_REGULAR, 10)
        font_idx   = _load_font(FONT_REGULAR, 10)

        cx = DISPLAY_HEIGHT // 2   # 120

        session        = sessions[session_idx]
        total_sessions = len(sessions)
        total_frames   = len(session)

        draw.text((cx, 18), "MANOKSENSE", font=font_title, fill=ACCENT, anchor="mm")
        draw.line((30, 30, DISPLAY_HEIGHT - 30, 30), fill=DIM, width=1)

        IMG_W = DISPLAY_HEIGHT   # 240
        IMG_H = 195
        IMG_Y = 32

        try:
            img = Image.open(session[frame_idx]).convert("RGB")
            img.thumbnail((IMG_W, IMG_H), Image.LANCZOS)
            ox = (IMG_W - img.width)  // 2
            oy = IMG_Y + (IMG_H - img.height) // 2
            canvas.paste(img, (ox, oy))
        except Exception:
            draw.rectangle((0, IMG_Y, IMG_W, IMG_Y + IMG_H), fill="#1A1A1A")
            draw.text((cx, IMG_Y + IMG_H // 2), "Error loading image",
                      font=font_hint, fill=DIM, anchor="mm")

        draw.text((cx, 273), f"Scan {session_idx + 1} / {total_sessions}",
                  font=font_idx, fill=DIM, anchor="mm")
        draw.text((cx, 285), f"{frame_idx + 1} / {total_frames}",
                  font=font_idx, fill=DIM, anchor="mm")

        _has_prev = frame_idx > 0 or session_idx > 0
        _has_next = (frame_idx < total_frames - 1) or (session_idx < total_sessions - 1)

        if _has_prev:
            draw.text((14, 285), "< PREV", font=font_nav, fill=ACCENT, anchor="lm")
        if _has_next:
            draw.text((DISPLAY_HEIGHT - 14, 285), "NEXT >", font=font_nav, fill=ACCENT, anchor="rm")

        DEL_CX = 120
        DEL_Y  = 230
        DEL_W  = 44
        DEL_H  = 11

        pill_fill = ERR_RED   if delete_confirm else "#3A1A1A"
        del_text  = "CONFIRM?" if delete_confirm else "DELETE"
        del_col   = FG        if delete_confirm else ERR_RED

        draw.rounded_rectangle(
            (DEL_CX - DEL_W, DEL_Y - DEL_H,
             DEL_CX + DEL_W, DEL_Y + DEL_H),
            radius=DEL_H, fill=pill_fill, outline=ERR_RED, width=1,
        )
        draw.text((DEL_CX, DEL_Y), del_text, font=font_btn, fill=del_col, anchor="mm")

        draw.text((cx, DISPLAY_WIDTH - 14), "tap \u25cf to go back",
                  font=font_hint, fill=DIM, anchor="mm")

        self._device.flush(canvas)

    # ------------------------------------------------------------------ #
    #  Power-off screen                                                    #
    # ------------------------------------------------------------------ #

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
