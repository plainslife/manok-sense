# src/states/process.py - run inference and save results to gallery

import src.gallery_store as gallery
from src.context import AppContext
from inference_bridge import run_inference

# LED colors per classification result
_LED_COLORS = {
    "edible":      (0,   220, 80),
    "adulterated": (255, 130, 0),
    "spoiled":     (220, 30,  30),
}


def on_enter(ctx: AppContext) -> None:
    """Show the processing screen as soon as we enter this state."""
    ctx.animation.show_processing()


def run(ctx: AppContext, now: float) -> str:
    """
    Run inference on collected frames, save to gallery, store result.
    Returns 'result' when done.
    """
    label, conf, probs = run_inference(ctx.cam, frames=ctx.captured_frames)

    # save all frames under one session timestamp with the label stamped on
    gallery.save_capture(ctx.captured_frames, label, conf)

    # store result in context so the result state can read it
    ctx.result_frames    = list(ctx.captured_frames)
    ctx.result           = (label, conf, probs)
    ctx.result_frame_idx = 0
    ctx.captured_frames  = []

    # set LED color to match classification
    r, g, b = _LED_COLORS.get(label, (255, 255, 255))
    ctx.led.set(r, g, b)

    print(f"[Process] {label} ({conf * 100:.1f}%) | "
          f"adu={probs[0]:.2f} edi={probs[1]:.2f} spo={probs[2]:.2f}")

    return "result"
