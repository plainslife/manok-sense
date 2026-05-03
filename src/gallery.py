# src/gallery.py

import os
import re
import time
from PIL import Image, ImageDraw, ImageFont

GALLERY_DIR  = "captures/gallery"
THUMB_SIZE   = (72, 72)
FONT_BOLD    = "fonts/DejaVuSans-Bold.ttf"
FONT_REGULAR = "fonts/DejaVuSans.ttf"

LABEL_COLORS = {
    "edible":      "#4AE87A",
    "adulterated": "#E8C84A",
    "spoiled":     "#E84A4A",
    "unknown":     "#555555",
}

# Matches: edible_20260420_120000_1of3.jpg
_SESSION_RE = re.compile(
    r'^(edible|spoiled|adulterated)_(\d{8}_\d{6})_(\d+)of(\d+)\.jpg$'
)


def _load_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def ensure_dir() -> None:
    os.makedirs(GALLERY_DIR, exist_ok=True)


def save_capture(images: list, label: str, conf: float) -> list[str]:
    """
    Save all captured frames with a shared session timestamp.
    Filenames: {label}_{timestamp}_1of{n}.jpg … {label}_{timestamp}_{n}of{n}.jpg
    Returns list of saved filepaths.
    """
    ensure_dir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    total     = len(images)
    paths: list[str] = []

    font = _load_font(FONT_BOLD, 18)
    color = LABEL_COLORS.get(label, "#EEEEEE")
    text  = label.upper()

    for i, image in enumerate(images):
        filename = f"{label}_{timestamp}_{i + 1}of{total}.jpg"
        filepath = os.path.join(GALLERY_DIR, filename)

        img  = image.copy().convert("RGB")
        draw = ImageDraw.Draw(img)

        # Label banner at bottom — no percentage text
        w, h = img.size
        draw.rectangle((0, h - 36, w, h), fill=(0, 0, 0))
        draw.text((8, h - 28), text, font=font, fill=color)

        img.save(filepath, quality=92)
        paths.append(filepath)

    print(f"[Gallery] Saved {total} frames → {label}_{timestamp}")
    return paths


def list_sessions() -> list[list[str]]:
    """
    Scan GALLERY_DIR, group files by session (label_timestamp prefix),
    sort sessions newest first.

    Returns list[list[str]] — each inner list holds the ordered filepaths
    for one session (1ofN, 2ofN, 3ofN…).  Sessions with fewer than N files
    are included, sorted by their available frame indices.
    """
    ensure_dir()

    # { "edible_20260420_120000": { 1: path, 2: path, 3: path } }
    buckets: dict[str, dict[int, str]] = {}

    for fname in os.listdir(GALLERY_DIR):
        if not fname.lower().endswith(".jpg"):
            continue
        m = _SESSION_RE.match(fname)
        if not m:
            continue
        label, ts, idx_str, _ = m.groups()
        key   = f"{label}_{ts}"
        idx   = int(idx_str)
        fpath = os.path.join(GALLERY_DIR, fname)
        if key not in buckets:
            buckets[key] = {}
        buckets[key][idx] = fpath

    sessions: list[list[str]] = []
    for frame_map in buckets.values():
        ordered = [frame_map[n] for n in sorted(frame_map)]
        sessions.append(ordered)

    # Sort by timestamp embedded in the first filename (newest first)
    def _session_ts(session: list[str]) -> str:
        m = _SESSION_RE.match(os.path.basename(session[0]))
        return m.group(2) if m else ""

    sessions.sort(key=_session_ts, reverse=True)
    return sessions


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
    """Extract label from filename like 'edible_20260420_120000_1of3.jpg'"""
    name = os.path.basename(filepath)
    for label in LABEL_COLORS:
        if name.startswith(label):
            return label
    return "unknown"
