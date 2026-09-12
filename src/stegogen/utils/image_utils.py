"""Image loading, saving, and validation utilities."""

from pathlib import Path
from PIL import Image
import numpy as np


def load_image_as_rgb(image_path: str | Path) -> Image.Image:
    """Load an image file and ensure it is in RGB mode.

    Args:
        image_path: Path to the image file.

    Returns:
        A PIL Image instance in RGB mode.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is unsupported or unreadable.
    """
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f"Image not found at: {path}")

    try:
        img = Image.open(path)
        img.load()
    except Exception as exc:
        raise ValueError(f"Failed to load image: {exc}") from exc

    # Force RGB mode to standardize pixel channel array
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGB")
    elif img.mode == "RGBA":
        # Keep RGB channels for embedding; drop alpha or blend
        img = img.convert("RGB")

    return img


def save_stego_image(image: Image.Image, output_path: str | Path) -> Path:
    """Save an image losslessly as PNG.

    Args:
        image: PIL Image to save.
        output_path: Destination path.

    Returns:
        The resolved Path object where the image was saved.
    """
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest, format="PNG")
    return dest