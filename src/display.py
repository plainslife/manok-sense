# src/display.py — Luma ILI9341 device and UI drawing helpers

from PIL import Image, ImageDraw, ImageFont, ImageOps
from luma.core.interface.serial import spi
from luma.lcd.device import ili9341
from config import (
    DISPLAY_SPI_PORT,
    DISPLAY_SPI_DEVICE,
    DISPLAY_GPIO_DC,
    DISPLAY_GPIO_RST,
    DISPLAY_BUS_SPEED_HZ,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    PREVIEW_W,
    PREVIEW_H,
    PREVIEW_X,
    PREVIEW_Y,
    BTN_X,
    BTN_Y,
    BTN_RADIUS,
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

class DisplayUI:

    def __init__(self):
        self._device = _make_device()

    # create a blank canvas to be displayed and rotated to match the device orientation
    def blank_canvas(self) -> Image.Image:
        return Image.new("RGB", (self._device.width, self._device.height), "black")

    def draw_frame(self, canvas: Image.Image, frame: Image.Image) -> None:
        canvas.paste(frame, (PREVIEW_X, PREVIEW_Y))

    def draw_overlay(self, canvas: Image.Image, btn_pressed: bool = False) -> None:
        draw = ImageDraw.Draw(canvas)

        btn_fill    = "red" if btn_pressed else None
        btn_outline = "red" if btn_pressed else "white"
        draw.ellipse(
            (BTN_X - BTN_RADIUS, BTN_Y - BTN_RADIUS,
             BTN_X + BTN_RADIUS, BTN_Y + BTN_RADIUS),
            fill=btn_fill, outline=btn_outline, width=3,
        )

        cx = PREVIEW_X + 240 // 2
        cy = PREVIEW_Y + PREVIEW_H // 2

        rect_w = 144
        rect_h = 144

        x0 = cx - rect_w // 2
        y0 = cy - rect_h // 2
        x1 = cx + rect_w // 2
        y1 = cy + rect_h // 2
        draw.rectangle([(x0, y0), (x1, y1)], outline="green", width=3)

    def flush(self, canvas: Image.Image) -> None:
        self._device.display(canvas)

    def render(self, frame: Image.Image, btn_pressed: bool = False) -> None:
        canvas = self.blank_canvas()
        self.draw_frame(canvas, frame)
        self.draw_overlay(canvas, btn_pressed)
        # self.flush(canvas.rotate(90, expand=True))
        self.flush(canvas)
