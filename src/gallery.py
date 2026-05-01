# src/gallery.py

import os
import time
from PIL import Image, ImageDraw, ImageFont

GALLERY_DIR    = "captures/gallery"
THUMB_SIZE     = (72, 72)
FONT_BOLD      = "fonts/DejaVuSans-Bold.ttf"
FONT_REGULAR   = "fonts/DejaVuSans.ttf"

LABEL_COLORS = {
    "edible":      "#4AE87A",
    "adulterated": "#E8C84A",
    "spoiled":     "#E84A4A",
    "unknown":     "#555555",
}


def _load_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def ensure_dir() -> None:
    os.makedirs(GALLERY_DIR, exist_ok=True)


def save_capture(image: Image.Image, label: str, conf: float) -> str:
    """Save full capture with label overlay. Returns filepath."""
    ensure_dir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename  = f"{label}_{timestamp}.jpg"
    filepath  = os.path.join(GALLERY_DIR, filename)

    # Save full image with label burned in
    img  = image.copy().convert("RGB")
    draw = ImageDraw.Draw(img)
    font = _load_font(FONT_BOLD, 18)
    hint = _load_font(FONT_REGULAR, 12)

    color = LABEL_COLORS.get(label, "#EEEEEE")
    text  = label.upper()
    pct   = f"{conf * 100:.1f}%"

    # Semi-transparent banner at bottom
    w, h = img.size
    draw.rectangle((0, h - 36, w, h), fill=(0, 0, 0))
    draw.text((8, h - 28), text, font=font, fill=color)
    draw.text((w - 8, h - 16), pct, font=hint, fill="#EEEEEE", anchor="rm")

    img.save(filepath, quality=92)
    print(f"[Gallery] Saved {filepath}")
    return filepath


def list_captures() -> list[str]:
    """Return list of capture filepaths sorted newest first."""
    ensure_dir()
    files = [
        os.path.join(GALLERY_DIR, f)
        for f in os.listdir(GALLERY_DIR)
        if f.lower().endswith(".jpg")
    ]
    return sorted(files, reverse=True)


def make_thumbnail(filepath: str) -> Image.Image:
    """Load and resize image to thumbnail size."""
    try:
        img = Image.open(filepath).convert("RGB")
        img.thumbnail(THUMB_SIZE, Image.LANCZOS)
        # Pad to exact size
        thumb = Image.new("RGB", THUMB_SIZE, (20, 20, 20))
        ox = (THUMB_SIZE[0] - img.width)  // 2
        oy = (THUMB_SIZE[1] - img.height) // 2
        thumb.paste(img, (ox, oy))
        return thumb
    except Exception:
        return Image.new("RGB", THUMB_SIZE, (40, 40, 40))


def get_label_from_filename(filepath: str) -> str:
    """Extract label from filename like 'edible_20260420_120000.jpg'"""
    name = os.path.basename(filepath)
    for label in LABEL_COLORS:
        if name.startswith(label):
            return label
    return "unknown"
