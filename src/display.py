# src/display.py — Luma ILI9341 device and UI drawing helpers
 
from PIL import Image, ImageDraw
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
    PREVIEW_X,
    PREVIEW_Y,
    PREVIEW_W,
    PREVIEW_H,
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
    return ili9341(serial, width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)

class DisplayUI:

    def __init__(self):
        self._device = _make_device()

    # draw a frame into a canvas
    def draw_frame(self, canvas: Image.Image, frame: Image.Image) -> None:
        preview = frame.resize((PREVIEW_W, PREVIEW_H))
        canvas.paste(preview, (PREVIEW_X, PREVIEW_Y))

    # draw overlays in the camera preview display
    def draw_overlay(self, canvas: Image.Image, btn_pressed: bool = False) -> None:
        draw = ImageDraw.Draw(canvas)

        # border around the preview
        draw.rectangle((PREVIEW_X - 2, PREVIEW_Y - 2, PREVIEW_X + PREVIEW_W + 1, PREVIEW_Y + PREVIEW_H + 1), outline="white")

        # live preview text
        draw.text((PREVIEW_X, PREVIEW_Y + PREVIEW_H + 4), "Live Feed", fill="white")

        # shutter button animation kinda 
        btn_fill = "red" if btn_pressed else None
        btn_outline = "white" if not btn_pressed else "red"
        draw.ellipse(
            (BTN_X - BTN_RADIUS, BTN_Y - BTN_RADIUS, BTN_X + BTN_RADIUS, BTN_Y + BTN_RADIUS),
            fill=btn_fill,
            outline=btn_outline,
            width=3,
        )

    # flush(display) canvas to the screen
    def flush(self, canvas: Image.Image) -> None:
        self._device.display(canvas)

    # by default will be used to render the camera preview and its overlays
    def render(self, frame: Image.Image, btn_pressed: bool = False) -> None:
        canvas = Image.new("RGB", (self._device.width, self._device.height), "black")

        #  preview frame
        self.draw_frame(canvas, frame)

        # overlay
        self.draw_overlay(canvas, btn_pressed)

        # flush(display) the canvas to the screen
        self.flush(canvas)
        

