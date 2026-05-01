# src/display.py — Luma ILI9341 device and UI drawing helpers

import math
from PIL import Image, ImageDraw, ImageFont, ImageOps
from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from config import (
    DISPLAY_SPI_PORT,DISPLAY_SPI_DEVICE,
    DISPLAY_GPIO_DC,DISPLAY_GPIO_RST,
    DISPLAY_BUS_SPEED_HZ,
    DISPLAY_WIDTH,DISPLAY_HEIGHT,
    PREVIEW_W,PREVIEW_H,PREVIEW_X,PREVIEW_Y,
    BTN_X,BTN_Y,BTN_RADIUS,
    SETTINGS_X,SETTINGS_Y,
    GALLERY_X, GALLERY_Y,
)


def _make_device() -> ili9341:
    serial = spi(
        port=DISPLAY_SPI_PORT,
        device=DISPLAY_SPI_DEVICE,
        gpio_DC=DISPLAY_GPIO_DC,
        gpio_RST=DISPLAY_GPIO_RST,
        bus_speed_hz=DISPLAY_BUS_SPEED_HZ,
    )
    return ili9341(serial, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT, rotate=3)


# TODO move icons and others to another file (or any other ideas to declutter)
# for settings
def _draw_gear_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str) -> None:
    R_OUT  = 9    # tooth-tip radius
    R_BODY = 7    # body radius
    R_HOLE = 4    # inner hole radius
    TEETH  = 8
    HALF_T = math.radians(13)   # half angular width of each tooth

    pts: list[tuple[float, float]] = []
    for i in range(TEETH):
        base = math.radians(i * 360 / TEETH)
        for da, r in [
            (-HALF_T,       R_BODY),
            (-HALF_T / 2,   R_OUT),
            ( HALF_T / 2,   R_OUT),
            ( HALF_T,       R_BODY),
        ]:
            a = base + da
            pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))

    draw.polygon(pts, fill=color)
    draw.ellipse(
        (cx - R_HOLE, cy - R_HOLE, cx + R_HOLE, cy + R_HOLE),
        fill="black",
    )

# for gallery
def _draw_gallery_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, color: str) -> None:
    """2×2 grid of small rounded squares — classic gallery icon."""
    S    = 5   # square half-size
    GAP  = 2   # gap between squares
    R    = 2   # corner radius

    for dx in (-1, 1):
        for dy in (-1, 1):
            ox = cx + dx * (S + GAP // 2)
            oy = cy + dy * (S + GAP // 2)
            draw.rounded_rectangle(
                (ox - S, oy - S, ox + S, oy + S),
                radius=R, fill=color,
            )

class DisplayUI:

    def __init__(self) -> None:
        self._device = _make_device()

    def blank_canvas(self) -> Image.Image:
        return Image.new("RGB", (self._device.width, self._device.height), "black")

    def draw_frame(self, canvas: Image.Image, frame: Image.Image) -> None:
        canvas.paste(frame, (PREVIEW_X, PREVIEW_Y))

    def draw_overlay(
        self,
        canvas: Image.Image,
        btn_pressed: bool = False,
        distance_state: str = "ok",   # "ok" | "near" | "far"
        distance_cm: int | None = None,
        sensor_enabled: bool = False,
    ) -> None:
        from src.color import OK_GREEN, ERR_RED, ACCENT, DIM, FG

        draw = ImageDraw.Draw(canvas)

        try:
            font_dist = ImageFont.truetype("fonts/DejaVuSans-Bold.ttf", 13)
            font_hint = ImageFont.truetype("fonts/DejaVuSans.ttf", 10)
        except OSError:
            font_dist = ImageFont.load_default()
            font_hint = font_dist

        # ── Header strip ─────────────────────────────────────────────────
        draw.rectangle((0, 0, 320, PREVIEW_Y - 1), fill="#111111")

        # ── Settings gear icon (always visible top-right) ─────────────────
        _draw_gear_icon(draw, SETTINGS_X, SETTINGS_Y, color=DIM)
        
        # ── Gallery icon (always visible top-left) ────────────────────────
        _draw_gallery_icon(draw, GALLERY_X, GALLERY_Y, color=DIM)

        # ── Distance info (only when sensor is active) ────────────────────
        if sensor_enabled:
            status_text, status_color = {
                "ok":   ("IN RANGE", OK_GREEN),
                "near": ("TOO NEAR", ERR_RED),
                "far":  ("TOO FAR",  ACCENT),
            }.get(distance_state, ("--", FG))

            dist_text = f"{distance_cm}cm" if distance_cm is not None else "--cm"

            cx_header = DISPLAY_HEIGHT // 2   # 120 — between gallery and gear
            draw.text(
                (cx_header, 19),
                dist_text,
                font=font_dist, fill=status_color, anchor="mm",
            )
            draw.text(
                (cx_header, 36),
                status_text,
                font=font_hint, fill=status_color, anchor="mm",
            )

        # ── Shutter button ───────────────────────────────────────────────
        # Button is locked while distance is out of range (sensor only)
        btn_available = (not sensor_enabled) or (distance_state == "ok")

        if btn_pressed and btn_available:
            btn_fill, btn_outline = "red", "red"
        elif btn_available:
            btn_fill, btn_outline = None, "white"
        else:
            btn_fill, btn_outline = None, "#444444"

        draw.ellipse(
            (BTN_X - BTN_RADIUS, BTN_Y - BTN_RADIUS,
             BTN_X + BTN_RADIUS, BTN_Y + BTN_RADIUS),
            fill=btn_fill, outline=btn_outline, width=3,
        )

        # ── Viewfinder box ───────────────────────────────────────────────
        effective_state = distance_state if sensor_enabled else "ok"
        box_color = {
            "ok":   OK_GREEN,
            "near": ERR_RED,
            "far":  ACCENT,
        }.get(effective_state, OK_GREEN)

        cx = PREVIEW_X + DISPLAY_HEIGHT // 2
        cy = PREVIEW_Y + PREVIEW_H // 2
        draw.rectangle(
            [(cx - 72, cy - 72), (cx + 72, cy + 72)],
            outline=box_color, width=3,
        )

        # ── Out-of-range hint over button ─────────────────────────────────
        if sensor_enabled and not btn_available:
            msg = "move closer" if distance_state == "far" else "move back"
            draw.text(
                (BTN_X, BTN_Y), msg,
                font=font_hint, fill=status_color, anchor="mm",
            )

    def flush(self, canvas: Image.Image) -> None:
        self._device.display(canvas)

    def render(
        self,
        frame: Image.Image,
        btn_pressed: bool = False,
        distance_state: str = "ok",
        distance_cm: int | None = None,
        sensor_enabled: bool = False,
    ) -> None:
        canvas = self.blank_canvas()
        self.draw_frame(canvas, frame)
        self.draw_overlay(canvas, btn_pressed, distance_state, distance_cm, sensor_enabled)
        self.flush(canvas)

    def shutdown(self) -> None:
        self._device.cleanup()
