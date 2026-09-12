"""Spatial Least Significant Bit (LSB) decoder."""

from pathlib import Path
from PIL import Image
import numpy as np

from stegogen.core.payload import HEADER_SIZE, parse_payload, StegoPayload
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


def extract_payload_from_array(pixel_array: np.ndarray) -> StegoPayload:
    """Extract and validate a structured StegoGen payload from an RGB numpy array.

    Args:
        pixel_array: uint8 numpy array representing image pixels.

    Returns:
        StegoPayload with validated integrity and metadata.

    Raises:
        ValueError: If header is invalid, magic mismatches, or checksum fails.
    """
    flat_pixels = pixel_array.flatten()
    total_bits = flat_pixels.size

    header_bits_needed = HEADER_SIZE * 8
    if total_bits < header_bits_needed:
        raise ValueError("Carrier image is too small to contain a valid StegoGen header.")

    # 1. Read first 14 bytes (header)
    header_bits = [int(flat_pixels[i] & 1) for i in range(header_bits_needed)]
    header_bytes = bits_to_bytes(header_bits)

    # Validate magic bytes before extracting further
    if header_bytes[:4] != b"STGO":
        raise ValueError("No StegoGen secret found in image (magic header mismatch).")

    # Read data length from header bytes (offset 6 to 10)
    payload_len = int.from_bytes(header_bytes[6:10], byteorder="big")
    total_payload_bytes = HEADER_SIZE + payload_len
    total_bits_needed = total_payload_bytes * 8

    if total_bits_needed > total_bits:
        raise ValueError(
            f"Incomplete payload: header expects {payload_len} data bytes, "
            f"but carrier only contains {total_bits // 8 - HEADER_SIZE} available bytes."
        )

    # 2. Extract remaining payload bits
    data_bits = [int(flat_pixels[i] & 1) for i in range(header_bits_needed, total_bits_needed)]
    all_bytes = header_bytes + bits_to_bytes(data_bits)

    return parse_payload(all_bytes)


def decode_text(stego_image_path: str | Path) -> str:
    """Read a stego image and recover the hidden text message."""
    image = load_image_as_rgb(stego_image_path)
    pixel_array = np.array(image, dtype=np.uint8)
    payload = extract_payload_from_array(pixel_array)

    if payload.is_encrypted:
        raise ValueError("Payload is encrypted. Decryption password required.")

    if payload.is_file:
        raise ValueError("Payload contains a file, not a plain text message.")

    try:
        return payload.data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Decoded bytes are not valid UTF-8 text.") from exc
