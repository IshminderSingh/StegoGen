"""Tests for basic LSB encoding and decoding."""

import pytest
import numpy as np
from PIL import Image

from stegogen.core.encoder import encode_message_into_array, encode_text
from stegogen.core.decoder import decode_message_from_array, decode_text


@pytest.fixture
def blank_rgb_image(tmp_path):
    """Generate a clean 100x100 RGB image for testing."""
    img_path = tmp_path / "cover.png"
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    img.save(img_path)
    return img_path


def test_roundtrip_ascii_message():
    """Verify standard text embeds and decodes identically."""
    pixels = np.full((50, 50, 3), 100, dtype=np.uint8)
    secret = "Hello World!"
    stego = encode_message_into_array(pixels, secret)
    recovered = decode_message_from_array(stego)
    assert recovered == secret


def test_roundtrip_unicode_message():
    """Verify multi-byte Unicode strings (emojis, accents) work properly."""
    pixels = np.full((60, 60, 3), 150, dtype=np.uint8)
    secret = "StegoGen 🔒 — Unicode Test: مرحبا, ਗੁਪਤ, Café 🚀"
    stego = encode_message_into_array(pixels, secret)
    recovered = decode_message_from_array(stego)
    assert recovered == secret


def test_empty_message():
    """Verify 0-length messages do not crash."""
    pixels = np.zeros((20, 20, 3), dtype=np.uint8)
    secret = ""
    stego = encode_message_into_array(pixels, secret)
    recovered = decode_message_from_array(stego)
    assert recovered == ""


def test_capacity_overflow():
    """Verify an exception is raised when data exceeds pixel count."""
    tiny_pixels = np.zeros((2, 2, 3), dtype=np.uint8)  # 2x2x3 = 12 bits capacity
    message = "Too big for 12 bits"  # Needs 32 header bits + message bits
    with pytest.raises(ValueError, match="Message too large"):
        encode_message_into_array(tiny_pixels, message)


def test_file_level_encoding_without_overwriting(blank_rgb_image, tmp_path):
    """Ensure original cover image file is untouched and separate output created."""
    output_path = tmp_path / "stego.png"
    cover_bytes_before = blank_rgb_image.read_bytes()

    secret = "Top Secret Information"
    saved_path = encode_text(blank_rgb_image, secret, output_path)

    assert saved_path.is_file()
    assert blank_rgb_image.read_bytes() == cover_bytes_before
    assert decode_text(saved_path) == secret


def test_prevent_same_input_output_path(blank_rgb_image):
    """Ensure code refuses to overwrite original cover image."""
    with pytest.raises(ValueError, match="must not be identical"):
        encode_text(blank_rgb_image, "test", blank_rgb_image)