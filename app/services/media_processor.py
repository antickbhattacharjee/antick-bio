"""
Media Processing Service for Antick Website CMS.
Handles standard image normalization with Pillow:
- EXIF orientation correction
- Clean WebP conversion & compression
- Canonical collision-safe naming (e.g., antick-bhattacharjee-photo-001.webp)
- Clean, non-stuffed alt-text suggestions
"""

import io
import re
from typing import Optional, Tuple
from PIL import Image, ImageOps


CANONICAL_NAME = "Antick Bhattacharjee"


def normalize_and_convert_image(
    image_bytes: bytes,
    max_dimension: int = 2400,
    quality: int = 85,
) -> Tuple[bytes, int, int, str]:
    """
    Process image using Pillow:
    1. Corrects EXIF orientation.
    2. Converts RGBA/P to RGB if saving as WebP (or preserves RGBA transparency).
    3. Downscales if exceeding max_dimension without upscaling.
    4. Compresses to optimized WebP.
    Returns: (processed_webp_bytes, width, height, mime_type)
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Transpose according to EXIF orientation tag
    img = ImageOps.exif_transpose(img)

    # Convert mode for WebP compatibility
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA" if "transparency" in img.info else "RGB")

    width, height = img.size

    # Only downscale if image is larger than max_dimension, never upscale
    if width > max_dimension or height > max_dimension:
        img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
        width, height = img.size

    out_io = io.BytesIO()
    img.save(out_io, format="WEBP", quality=quality, method=6)
    return out_io.getvalue(), width, height, "image/webp"


def generate_canonical_photo_filename(index: int) -> str:
    """Generate canonical collision-safe photo filename."""
    return f"antick-bhattacharjee-photo-{index:03d}.webp"


def slugify(text: str) -> str:
    """Convert arbitrary string into a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


def suggest_alt_text(title: str, category: str = "", context: str = "") -> str:
    """
    Generate clean, descriptive, natural alt text without keyword stuffing.
    """
    cat_lower = category.lower()
    title_clean = title.strip()

    if "portrait" in cat_lower or "profile" in cat_lower:
        return f"Portrait of {CANONICAL_NAME}"
    elif "train" in cat_lower or "workshop" in cat_lower:
        if title_clean:
            return f"{CANONICAL_NAME} conducting {title_clean}"
        return f"{CANONICAL_NAME} conducting a corporate technical training session"
    elif "speak" in cat_lower or "presentation" in cat_lower:
        if title_clean:
            return f"{CANONICAL_NAME} presenting on {title_clean}"
        return f"{CANONICAL_NAME} speaking during a presentation"
    elif "project" in cat_lower or "code" in cat_lower or "dev" in cat_lower:
        if title_clean:
            return f"{CANONICAL_NAME} working on {title_clean}"
        return f"{CANONICAL_NAME} working on software development and automation systems"
    elif title_clean:
        if CANONICAL_NAME.lower() in title_clean.lower():
            return title_clean
        return f"{CANONICAL_NAME} - {title_clean}"
    else:
        return f"{CANONICAL_NAME}"
