"""Spatial Least Significant Bit (LSB) encoder."""

from pathlib import Path
from PIL import Image
import numpy as np

from stegogen.core.payload import serialize_payload
from stegogen.utils.image_utils import load_image_as_rgb, save_stego_image


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert raw bytes into a list of integer bits (0 or 1)."""
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def encode_bytes_into_array(pixel_array: np.ndarray, payload_bytes: bytes) -> np.ndarray:
    """Embed serialized payload bytes into an RGB numpy array using 1-bit LSB.

    Args:
        pixel_array: Flattenable uint8 numpy array of shape (H, W, 3).
        payload_bytes: The complete structured payload (header + body).

    Returns:
        A modified uint8 numpy array containing the embedded payload.

    Raises:
        ValueError: If payload exceeds carrier capacity.
    """
    total_bits = bytes_to_bits(payload_bytes)
    flat_pixels = pixel_array.flatten()
    available_bits = flat_pixels.size

    if len(total_bits) > available_bits:
        raise ValueError(
            f"Message too large: requires {len(total_bits)} bits, "
            f"carrier only has capacity for {available_bits} bits."
        )

    modified_pixels = flat_pixels.copy()
    for idx, bit in enumerate(total_bits):
        modified_pixels[idx] = (int(modified_pixels[idx]) & 0xFE) | bit

    return modified_pixels.reshape(pixel_array.shape)


def encode_text(
    cover_image_path: str | Path,
    message: str,
    output_image_path: str | Path,
) -> Path:
    """Embed text using structured framing and save stego PNG."""
    cover_path = Path(cover_image_path)
    output_path = Path(output_image_path)

    if cover_path.resolve() == output_path.resolve():
        raise ValueError("Cover image and output image paths must not be identical.")

    raw_data = message.encode("utf-8")
    structured_payload = serialize_payload(raw_data, is_encrypted=False, is_file=False)

    image = load_image_as_rgb(cover_path)
    pixel_array = np.array(image, dtype=np.uint8)

    stego_array = encode_bytes_into_array(pixel_array, structured_payload)
    stego_image = Image.fromarray(stego_array, mode="RGB")

    return save_stego_image(stego_image, output_path)
