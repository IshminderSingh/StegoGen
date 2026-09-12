"""Spatial Least Significant Bit (LSB) encoder."""

from pathlib import Path
from PIL import Image
import numpy as np

from stegogen.utils.image_utils import load_image_as_rgb, save_stego_image


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert raw bytes into a list of integer bits (0 or 1)."""
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def encode_message_into_array(pixel_array: np.ndarray, message: str) -> np.ndarray:
    """Embed a UTF-8 message into an RGB numpy array using 1-bit LSB.

    Structure:
      [32 bits: payload length in bytes] + [payload data bits]

    Args:
        pixel_array: Flattenable uint8 numpy array of shape (H, W, 3).
        message: The text string to embed.

    Returns:
        A modified uint8 numpy array containing the embedded payload.

    Raises:
        ValueError: If the message exceeds available carrier capacity.
    """
    payload_bytes = message.encode("utf-8")
    payload_len = len(payload_bytes)

    # 32-bit big-endian length header
    header_bytes = payload_len.to_bytes(4, byteorder="big")
    total_bits = bytes_to_bits(header_bytes + payload_bytes)

    flat_pixels = pixel_array.flatten()
    available_bits = flat_pixels.size

    if len(total_bits) > available_bits:
        raise ValueError(
            f"Message too large: requires {len(total_bits)} bits, "
            f"carrier only has capacity for {available_bits} bits."
        )

    # Substitute least significant bit (LSB)
    # Use unsigned uint8 bitmask 0xFE (254 / 0b11111110) to avoid negative integer overflow
    modified_pixels = flat_pixels.copy()
    for idx, bit in enumerate(total_bits):
        modified_pixels[idx] = (int(modified_pixels[idx]) & 0xFE) | bit

    return modified_pixels.reshape(pixel_array.shape)


def encode_text(
    cover_image_path: str | Path,
    message: str,
    output_image_path: str | Path,
) -> Path:
    """Load cover image, embed message, and save stego PNG without modifying the original.

    Args:
        cover_image_path: Source cover image file.
        message: Text secret to hide.
        output_image_path: Target PNG output path.

    Returns:
        Path of the newly created stego image.
    """
    cover_path = Path(cover_image_path)
    output_path = Path(output_image_path)

    if cover_path.resolve() == output_path.resolve():
        raise ValueError("Cover image and output image paths must not be identical.")

    image = load_image_as_rgb(cover_path)
    pixel_array = np.array(image, dtype=np.uint8)

    stego_array = encode_message_into_array(pixel_array, message)
    stego_image = Image.fromarray(stego_array, mode="RGB")

    return save_stego_image(stego_image, output_path)
