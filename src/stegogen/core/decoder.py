"""Spatial Least Significant Bit (LSB) decoder."""

from pathlib import Path
from PIL import Image
import numpy as np

from stegogen.utils.image_utils import load_image_as_rgb


def bits_to_bytes(bits: list[int]) -> bytes:
    """Pack a sequence of 0/1 bits into raw bytes."""
    byte_vals = bytearray()
    for i in range(0, len(bits), 8):
        byte_chunk = bits[i : i + 8]
        val = 0
        for bit in byte_chunk:
            val = (val << 1) | bit
        byte_vals.append(val)
    return bytes(byte_vals)


def decode_message_from_array(pixel_array: np.ndarray) -> str:
    """Extract and parse embedded UTF-8 message from an RGB numpy array.

    Args:
        pixel_array: uint8 numpy array representing image pixels.

    Returns:
        Recovered UTF-8 string.

    Raises:
        ValueError: If carrier is too small, payload length is invalid,
                    or bytes are invalid UTF-8.
    """
    flat_pixels = pixel_array.flatten()
    total_bits = flat_pixels.size

    # Must contain at least a 32-bit header
    if total_bits < 32:
        raise ValueError("Carrier image is too small to contain a valid payload.")

    # 1. Read first 32 bits for the length header
    header_bits = [int(flat_pixels[i] & 1) for i in range(32)]
    header_bytes = bits_to_bytes(header_bits)
    payload_len = int.from_bytes(header_bytes, byteorder="big")

    total_bits_needed = 32 + (payload_len * 8)
    if total_bits_needed > total_bits:
        raise ValueError(
            f"Corrupted or invalid payload: header specifies {payload_len} bytes "
            f"({total_bits_needed} bits), but image only has {total_bits} bits."
        )

    # 2. Extract payload bits
    payload_bits = [int(flat_pixels[i] & 1) for i in range(32, total_bits_needed)]
    payload_bytes = bits_to_bytes(payload_bits)

    try:
        return payload_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Decoded bytes are not valid UTF-8 text.") from exc


def decode_text(stego_image_path: str | Path) -> str:
    """Read a stego image and recover the hidden message."""
    image = load_image_as_rgb(stego_image_path)
    pixel_array = np.array(image, dtype=np.uint8)
    return decode_message_from_array(pixel_array)