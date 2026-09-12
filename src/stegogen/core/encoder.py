"""Spatial Least Significant Bit (LSB) encoder."""

from pathlib import Path
from PIL import Image
import numpy as np

from stegogen.core.payload import serialize_payload, pack_file_data
from stegogen.core.capacity import assess_capacity
from stegogen.crypto.encryption import encrypt_bytes
from stegogen.utils.image_utils import load_image_as_rgb, save_stego_image


def bytes_to_bits(data: bytes) -> list[int]:
    """Convert raw bytes into a list of integer bits (0 or 1)."""
    bits: list[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def encode_bytes_into_array(pixel_array: np.ndarray, payload_bytes: bytes) -> np.ndarray:
    """Embed serialized payload bytes into an RGB numpy array using 1-bit LSB."""
    total_bits = bytes_to_bits(payload_bytes)
    flat_pixels = pixel_array.flatten()
    available_bits = flat_pixels.size

    if len(total_bits) > available_bits:
        raise ValueError(
            f"Payload exceeds carrier capacity: requires {len(total_bits)} bits, "
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
    password: str | None = None,
) -> Path:
    """Embed text (optionally encrypted) into a cover image and save stego PNG."""
    cover_path = Path(cover_image_path)
    output_path = Path(output_image_path)

    if cover_path.resolve() == output_path.resolve():
        raise ValueError("Cover image and output image paths must not be identical.")

    is_encrypted = bool(password)
    report = assess_capacity(cover_path, message, is_encrypted=is_encrypted, is_file=False)
    if not report.fits:
        raise ValueError(
            f"Carrier capacity exceeded: Image holds {report.total_carrier_bytes:,} bytes, "
            f"but payload + metadata requires {report.total_required_bytes:,} bytes."
        )

    raw_data = message.encode("utf-8")
    if is_encrypted and password:
        raw_data = encrypt_bytes(raw_data, password)

    structured_payload = serialize_payload(raw_data, is_encrypted=is_encrypted, is_file=False)

    image = load_image_as_rgb(cover_path)
    pixel_array = np.array(image, dtype=np.uint8)

    stego_array = encode_bytes_into_array(pixel_array, structured_payload)
    stego_image = Image.fromarray(stego_array, mode="RGB")

    return save_stego_image(stego_image, output_path)


def encode_file(
    cover_image_path: str | Path,
    file_to_hide_path: str | Path,
    output_image_path: str | Path,
    password: str | None = None,
) -> Path:
    """Embed an arbitrary binary file into a cover image and save stego PNG."""
    cover_path = Path(cover_image_path)
    secret_file_path = Path(file_to_hide_path)
    output_path = Path(output_image_path)

    if not secret_file_path.is_file():
        raise FileNotFoundError(f"File to hide not found: {secret_file_path}")

    if cover_path.resolve() == output_path.resolve():
        raise ValueError("Cover image and output image paths must not be identical.")

    is_encrypted = bool(password)
    report = assess_capacity(cover_path, secret_file_path, is_encrypted=is_encrypted, is_file=True)
    if not report.fits:
        raise ValueError(
            f"Carrier capacity exceeded: Image holds {report.total_carrier_bytes:,} bytes, "
            f"but file + metadata requires {report.total_required_bytes:,} bytes."
        )

    file_bytes = secret_file_path.read_bytes()
    packaged_data = pack_file_data(secret_file_path.name, file_bytes)

    if is_encrypted and password:
        packaged_data = encrypt_bytes(packaged_data, password)

    structured_payload = serialize_payload(packaged_data, is_encrypted=is_encrypted, is_file=True)

    image = load_image_as_rgb(cover_path)
    pixel_array = np.array(image, dtype=np.uint8)

    stego_array = encode_bytes_into_array(pixel_array, structured_payload)
    stego_image = Image.fromarray(stego_array, mode="RGB")

    return save_stego_image(stego_image, output_path)
