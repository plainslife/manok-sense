# config.py - configuration for hardware and UI settings

import board

# model
#MODEL_PATH = "/home/manok/Documents/manoksense/test_models/EfficientNetB0_88.5/chicken_classifier_final.tflite"
MODEL_PATH = "/home/manok/Documents/manoksense/test_models/chicken_efficientnetB2_906pct.tflite"
#MODEL_PATH = "/home/manok/Documents/manoksense/test_models/chicken_classifier_v12_fixed.tflite"
# MODEL_PATH = "/home/manok/Documents/manoksense/test_models/chicken_model_v1.7_float32.tflite"

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

# distance sensor
DISTANCE_MIN_CM = 0
DISTANCE_MAX_CM = 25

# ui layout
PREVIEW_X = 0
PREVIEW_Y = 50
PREVIEW_W = 320
PREVIEW_H = 180

BTN_X = 120
BTN_Y = 280
BTN_RADIUS = 30

# settings icon (top-right of header strip)
SETTINGS_X = 215
SETTINGS_Y = 25
SETTINGS_RADIUS = 20

# gallery icon
GALLERY_X = 25
GALLERY_Y = 25

# gallery ui
GALLERY_RADIUS    = 20
GALLERY_PREV_X    = 30
GALLERY_PREV_Y    = 290
GALLERY_PREV_R    = 22
GALLERY_NEXT_X    = 210
GALLERY_NEXT_Y    = 290
GALLERY_NEXT_R    = 22
GALLERY_DELETE_X      = 120
GALLERY_DELETE_Y      = 265
GALLERY_DELETE_RADIUS = 22

# settings touch zones
# cam reload
CAMERA_RELOAD_X      = 189
CAMERA_RELOAD_Y      = 156
CAMERA_RELOAD_RADIUS = 22

# led reload
LED_RELOAD_X      = 189
LED_RELOAD_Y      = 192 
LED_RELOAD_RADIUS = 22

# poweroff button
POWEROFF_X      = 189
POWEROFF_Y      = 228
POWEROFF_RADIUS = 24

# capture
CAPTURE_DIR = "captures"          # folder where images are saved
CAPTURE_PREFIX = "manokpik"
CAPTURE_QUALITY = 95              # JPEG quality 0-100
DEBOUNCE_SECS = 2.0

# LED
LED_PIN = board.D12
LED_COUNT = 4
LED_BRIGHTNESS = 1.0

# fonts
FONT_REGULAR = "fonts/DejaVuSans.ttf"
FONT_BOLD = "fonts/DejaVuSans-Bold.ttf"
