# inference_bridge.py
import subprocess
import socket
import os
import time
import numpy as np

# Absolute paths — works regardless of where the file lives
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
WORKER_PYTHON = os.path.join(BASE_DIR, "venv311/bin/python")
WORKER_SCRIPT = os.path.join(BASE_DIR, "inference_worker.py")
SOCKET_PATH   = "/tmp/manok.sock"
TEMP_FRAME    = "/tmp/manok_frame.jpg"
EDIBLE_IDX    = 1        # index of "edible" in CLASS_NAMES
EDIBLE_THRESHOLD = 0.55  # must be this confident to call it edible

_worker_proc = None

def start_worker() -> None:
    global _worker_proc
    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    _worker_proc = subprocess.Popen(
        [WORKER_PYTHON, WORKER_SCRIPT],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=BASE_DIR
    )

    line = _worker_proc.stdout.readline().decode().strip()
    print(f"[Bridge] {line}")

    for _ in range(20):
        if os.path.exists(SOCKET_PATH):
            break
        time.sleep(0.2)
    else:
        stderr = _worker_proc.stderr.read().decode()
        raise RuntimeError(f"[Bridge] Worker failed to start:\n{stderr}")


def _infer_single(frame) -> list[float]:
    """
    Send one frame to the worker and return raw probs [adu, edi, spo].
    """
    frame.save(TEMP_FRAME, quality=95)

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(30)
        client.connect(SOCKET_PATH)
        client.sendall(f"{TEMP_FRAME}\n".encode())
        result = client.recv(256).decode().strip()
        client.close()
    except Exception as e:
        print(f"[Bridge] Inference error: {e}")
        return [0.0, 0.0, 0.0]

    parts = result.split(",")
    if len(parts) != 5 or parts[0] == "error":
        print(f"[Bridge] Bad result: {result}")
        return [0.0, 0.0, 0.0]

    _, _, a, e, s = parts
    return [float(a), float(e), float(s)]


def _apply_threshold(avg_probs: list[float]) -> tuple[str, float]:
    """
    Apply conservative edible threshold then return label + confidence.
    """
    CLASS_NAMES = ["adulterated", "edible", "spoiled"]

    if avg_probs[EDIBLE_IDX] >= EDIBLE_THRESHOLD:
        idx = EDIBLE_IDX
    else:
        probs_copy = avg_probs.copy()
        probs_copy[EDIBLE_IDX] = 0.0
        idx = int(np.argmax(probs_copy))

    return CLASS_NAMES[idx], float(avg_probs[idx])


def run_inference(cam, frames=None) -> tuple[str, float, list[float]]:
    """
    If frames provided (list of PIL Images) — average all predictions.
    If no frames — single shot from camera.
    """
    if frames and len(frames) > 1:
        print(f"[Bridge] Multi-photo inference: {len(frames)} frames")
        all_probs = []

        for i, frame in enumerate(frames):
            probs = _infer_single(frame)
            all_probs.append(probs)
            print(f"[Bridge] Frame {i+1}: "
                  f"adu={probs[0]:.2f} edi={probs[1]:.2f} spo={probs[2]:.2f}")

        avg_probs = list(np.mean(all_probs, axis=0))
        print(f"[Bridge] Averaged: "
              f"adu={avg_probs[0]:.2f} edi={avg_probs[1]:.2f} spo={avg_probs[2]:.2f}")

    else:
        # Single shot fallback
        frame = frames[0] if frames else cam.grab_inference_frame()
        avg_probs = _infer_single(frame)

    label, conf = _apply_threshold(avg_probs)
    return label, conf, avg_probs
