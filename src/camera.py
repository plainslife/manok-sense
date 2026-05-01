# src/camera.py

import numpy as np
from libcamera import Transform
from PIL import Image
from picamera2 import Picamera2
from config import (
    CAMERA_CAPTURE_SIZE, 
    CAMERA_FORMAT, 
    PREVIEW_W,
    PREVIEW_H,
    CAMERA_QUALITY
)

class Camera:

    def __init__(self):
        self._cam = Picamera2()
        config = self._cam.create_preview_configuration(main={"size": CAMERA_CAPTURE_SIZE, "format": CAMERA_FORMAT},
                                                        lores={"size": (PREVIEW_W, PREVIEW_H)},
                                                        transform=Transform(rotation=180))
        self._cam.configure(config)

    def start(self) -> None:
        self._cam.start()

    def stop(self) -> None:
        self._cam.stop()
        self._cam.close()

    def reload(self) -> None:
        print("[Camera] Reloading...")
        try:
            self._cam.stop()
        except Exception:
            pass
        try:
            self._cam.close()
        except Exception:
            pass

        self._cam = Picamera2()
        config = self._cam.create_preview_configuration(
            main={"size": CAMERA_CAPTURE_SIZE, "format": CAMERA_FORMAT},
            lores={"size": (PREVIEW_W, PREVIEW_H)},
            transform=Transform(rotation=180),
        )
        self._cam.configure(config)
        self._cam.start()
        print("[Camera] Reload complete")

    def grab_frame(self) -> Image.Image:
        frame = self._cam.capture_array("lores")  # shape: (H*3//2, W)
        h, w  = PREVIEW_H, PREVIEW_W

        yuv = frame.flatten()
        y   = yuv[:h * w].reshape(h, w).astype(np.float32)
        u   = yuv[h * w : h * w + h * w // 4].reshape(h // 2, w // 2).astype(np.float32) - 128
        v   = yuv[h * w + h * w // 4 : h * w + h * w // 2].reshape(h // 2, w // 2).astype(np.float32) - 128

        # Upsample U and V from half resolution to full
        u = np.repeat(np.repeat(u, 2, axis=0), 2, axis=1)
        v = np.repeat(np.repeat(v, 2, axis=0), 2, axis=1)

        r = np.clip(y + 1.402 * v,                    0, 255).astype(np.uint8)
        g = np.clip(y - 0.344136 * u - 0.714136 * v,  0, 255).astype(np.uint8)
        b = np.clip(y + 1.772 * u,                    0, 255).astype(np.uint8)

        return Image.fromarray(np.stack([r, g, b], axis=2))

    # save + grab_inference_frame — BGR to RGB
    def save(self, filepath: str) -> None:
        frame = self._cam.capture_array("main")
        image = Image.fromarray(frame[:, :, ::-1])  # BGR→RGB by reversing channels
        image = image.crop((0, 0, 960, 720))
        image.save(filepath)

    def grab_inference_frame(self) -> Image.Image:
        CROP_W = 960
        frame  = self._cam.capture_array("main")
        image  = Image.fromarray(frame[:, :, ::-1])
        image  = image.crop((0, 0, CROP_W, 720))   # 960×720 — stop here
        return image

    def save(self, filepath: str) -> None:
        CROP_W = 960
        self._cam.options["quality"] = CAMERA_QUALITY
        # self._cam.capture_file(filepath)

        # Grab the full frame and crop right side to match lores FOV
        frame_bgr = self._cam.capture_array("main")
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(frame_rgb)
        image = image.crop((0, 0, CROP_W, 720))  # trim right side
        image.save(filepath)

