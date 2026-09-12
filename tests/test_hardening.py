"""Milestone 8: Comprehensive test suite and edge-case hardening."""

import pytest
import numpy as np
from PIL import Image

from stegogen.core.encoder import encode_text, encode_file
from stegogen.core.decoder import decode_text, decode_file, extract_payload_from_array
from stegogen.utils.image_utils import load_image_as_rgb


def test_odd_and_non_square_dimensions(tmp_path):
    """Verify LSB embedding works on odd, non-square dimensions without shape mismatch."""
    cover_path = tmp_path / "odd_shape.png"
    stego_path = tmp_path / "odd_stego.png"

    # 47 x 73 image
    Image.new("RGB", (47, 73), color=(20, 40, 60)).save(cover_path)
    secret = "Odd dimension test string"

    encode_text(cover_path, secret, stego_path)
    assert decode_text(stego_path) == secret


def test_rgba_image_normalization(tmp_path):
    """Verify RGBA images with transparency are cleanly converted to RGB for embedding."""
    cover_path = tmp_path / "transparent.png"
    stego_path = tmp_path / "stego_rgba.png"

    # Create RGBA image with alpha channel
    Image.new("RGBA", (80, 80), color=(100, 150, 200, 128)).save(cover_path)
    secret = "Alpha channel flattened payload"

    encode_text(cover_path, secret, stego_path)
    assert decode_text(stego_path) == secret

    # Verify output is valid RGB PNG
    output_img = load_image_as_rgb(stego_path)
    assert output_img.mode == "RGB"


def test_grayscale_image_conversion(tmp_path):
    """Verify Grayscale ('L') images are converted cleanly to 3-channel RGB."""
    gray_path = tmp_path / "gray.png"
    stego_path = tmp_path / "stego_gray.png"

    Image.new("L", (80, 80), color=128).save(gray_path)
    secret = "Grayscale converted payload"

    encode_text(gray_path, secret, stego_path)
    assert decode_text(stego_path) == secret


def test_empty_binary_file_roundtrip(tmp_path):
    """Verify a 0-byte file embeds, restores, and preserves its name."""
    cover_path = tmp_path / "carrier.png"
    empty_file = tmp_path / "empty.dat"
    empty_file.write_bytes(b"")

    Image.new("RGB", (60, 60), color=(50, 50, 50)).save(cover_path)
    stego_path = tmp_path / "stego_empty_file.png"
    out_dir = tmp_path / "recovered_empty"

    encode_file(cover_path, empty_file, stego_path)
    restored = decode_file(stego_path, out_dir)

    assert restored.is_file()
    assert restored.name == "empty.dat"
    assert restored.stat().st_size == 0


def test_corrupted_payload_header_detection():
    """Verify corrupting bytes in a valid pixel array fails safely with ValueError."""
    # Create image with arbitrary bytes
    noise_array = np.random.randint(0, 256, (30, 30, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="No StegoGen secret found"):
        extract_payload_from_array(noise_array)


def test_missing_cover_image_raises_filenotfound():
    """Verify missing carrier raises FileNotFoundError."""
    with pytest.raises(FileNotFoundError):
        encode_text("non_existent_file.png", "msg", "out.png")


def test_missing_secret_file_raises_filenotfound(tmp_path):
    """Verify missing secret file raises FileNotFoundError."""
    carrier = tmp_path / "carrier.png"
    Image.new("RGB", (40, 40)).save(carrier)
    with pytest.raises(FileNotFoundError):
        encode_file(carrier, "missing_secret.dat", tmp_path / "out.png")
