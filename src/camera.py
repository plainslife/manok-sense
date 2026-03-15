# picamera2

import cv2 
from PIL import Image
from picamera2 import Picamera2
from config import (
    CAMERA_CAPTURE_SIZE, 
    CAMERA_FORMAT, 
    CAMERA_ROTATE_DEG,
    CAMERA_QUALITY
)

class Camera:

    def __init__(self):
        self._cam = Picamera2()
        config = self._cam.create_preview_configuration(main={"size": CAMERA_CAPTURE_SIZE, "format": CAMERA_FORMAT})
        self._cam.configure(config)

    def start(self) -> None:
        self._cam.start()

    def stop(self) -> None:
        self._cam.stop()
        self._cam.close()

    def grab_frame(self) -> Image.Image:
        frame_bgr = self._cam.capture_array()
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)

        if CAMERA_ROTATE_DEG:
            image = image.rotate(CAMERA_ROTATE_DEG, expand=True)

        return image

    def save(self, filepath: str) -> None:
        self._cam.options["quality"] = CAMERA_QUALITY
        self._cam.capture_file(filepath)

