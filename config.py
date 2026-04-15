# config.py - configuration for hardware and UI settings

import board

# camera 
CAMERA_CAPTURE_SIZE = (1280, 720)
CAMERA_FORMAT = "RGB888"
CAMERA_QUALITY = 100

# display (ili9341 via SPI)
DISPLAY_SPI_PORT = 0
DISPLAY_SPI_DEVICE = 0
DISPLAY_GPIO_DC = 24
DISPLAY_GPIO_RST = 25
# DISPLAY_BUS_SPEED_HZ = 32_000_000
DISPLAY_BUS_SPEED_HZ = 52_000_000
DISPLAY_WIDTH = 320
DISPLAY_HEIGHT = 240

# touch (xpt2046 via SPI)
TOUCH_BUS = 1
TOUCH_DEVICE = 0

# ui layout
PREVIEW_X = 0
PREVIEW_Y = 50
PREVIEW_W = 320
PREVIEW_H = 180
 
BTN_X = 120
BTN_Y = 280
BTN_RADIUS = 30

# capture
CAPTURE_DIR = "captures" # folder where images are saved
CAPTURE_PREFIX = "manokpik"
CAPTURE_QUALITY = 95 # JPEG quality 0-100
DEBOUNCE_SECS = 2.0

# LED 
LED_PIN = board.D12
LED_COUNT = 4 
LED_BRIGHTNESS = 1.0

# fonts
FONT_REGULAR = "fonts/DejaVuSans.ttf"
FONT_BOLD = "fonts/DejaVuSans-Bold.ttf"
