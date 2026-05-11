# src/classifier.py

from __future__ import annotations

import numpy as np
from PIL import Image

import tflite_runtime.interpreter as tflite

from config import MODEL_PATH

CLASS_NAMES = ["adulterated", "edible", "spoiled"]
# INPUT_SIZE  = (224, 224)        # MobileNET native resolution
INPUT_SIZE  = (260, 260)        # MobileNET native resolution
EDIBLE_THRESHOLD = 0.55         # Conservative threshold for food safety


class Classifier:
    """
    Runs float16 TFLite inference for chicken quality classification.
    Uses EfficientNetB2 at 260x260 with float32 input/output.
    """

    def __init__(self, model_path: str = MODEL_PATH) -> None:
        self._interpreter = tflite.Interpreter(model_path=model_path)
        self._interpreter.allocate_tensors()
        self._input  = self._interpreter.get_input_details()[0]
        self._output = self._interpreter.get_output_details()[0]

        dtype = self._input["dtype"]
        print(f"[Classifier] input dtype={dtype}, shape={self._input['shape']}")
        print(f"[Classifier] input quantization={self._input['quantization']}")
        print(f"[Classifier] output dtype={self._output['dtype']}")
        print(f"[Classifier] output quantization={self._output['quantization']}")

    def _preprocess(self, image: Image.Image) -> np.ndarray:
        """
        Center-crop to square, resize to 260x260.
        EfficientNetB2 expects raw float32 pixel values in [0, 255].
        Do NOT normalize — EfficientNet has its own internal preprocessing.
        """
        # Center-crop to square
        w, h = image.size
        side = min(w, h)
        left = (w - side) // 2
        top  = (h - side) // 2
        image = image.crop((left, top, left + side, top + side))

        # Resize to EfficientNetB2 input size
        image = image.resize(INPUT_SIZE, Image.LANCZOS)

        # Raw float32 — no normalization, EfficientNet handles it internally
        arr = np.array(image, dtype=np.float32)     # (260, 260, 3)
        
        # # FOR MOBILE NET
        # dtype = self._input["dtype"]
        # if dtype == np.float32:
        #     arr = (arr / 127.5) - 1.0    # ← MobileNet expects [-1, 1]
        #
        # elif dtype == np.uint8:
        #     arr = arr.astype(np.uint8)
        #
        # elif dtype == np.int8:
        #     scale, zero_point = self._input["quantization"]
        #     if scale == 0.0:
        #         scale      = 1.0 / 127.5
        #         zero_point = -1
        #     arr = np.clip(
        #         np.round(arr / scale + zero_point), -128, 127
        #     ).astype(np.int8)    
        # #FOR MOBILENET

        return np.expand_dims(arr, axis=0)           # (1, 260, 260, 3)

    def _dequantize_output(self, raw: np.ndarray) -> np.ndarray:
        dtype = self._output["dtype"]
        if dtype in (np.int8, np.uint8, np.int16):
            scale, zero_point = self._output["quantization"]
            return (raw.astype(np.float32) - zero_point) * scale
        return raw.astype(np.float32)

    # ------------------------------------------------------------------ #
    #  Public API                                                          #
    # ------------------------------------------------------------------ #
    def predict(self, image: Image.Image) -> tuple[str, float, list[float]]:
        tensor = self._preprocess(image)

        # Debug — save preprocessed image
        debug_arr = np.clip(tensor[0], 0, 255).astype(np.uint8)
        Image.fromarray(debug_arr).save("/tmp/manok_preprocessed.jpg")

        self._interpreter.set_tensor(self._input["index"], tensor)
        self._interpreter.invoke()

        raw_out = self._interpreter.get_tensor(self._output["index"])
        probs   = self._dequantize_output(raw_out)[0]

        # Apply conservative edible threshold for food safety
        edible_idx = CLASS_NAMES.index("edible")
        if probs[edible_idx] >= EDIBLE_THRESHOLD:
            idx = edible_idx
        else:
            prob_copy = probs.copy()
            prob_copy[edible_idx] = 0
            idx = int(np.argmax(prob_copy))

        return CLASS_NAMES[idx], float(probs[idx]), probs.tolist()

    def predict_multi(
        self,
        images: list[Image.Image],
    ) -> tuple[str, float, list[float]]:
        """
        Average predictions across multiple photos of the same sample.
        Recommended: pass 3 photos for more reliable results.
        """
        all_probs = []
        for img in images:
            _, _, probs = self.predict(img)
            all_probs.append(probs)

        avg_probs  = np.mean(all_probs, axis=0)
        edible_idx = CLASS_NAMES.index("edible")

        if avg_probs[edible_idx] >= EDIBLE_THRESHOLD:
            idx = edible_idx
        else:
            prob_copy = avg_probs.copy()
            prob_copy[edible_idx] = 0
            idx = int(np.argmax(prob_copy))

        return CLASS_NAMES[idx], float(avg_probs[idx]), avg_probs.tolist()
