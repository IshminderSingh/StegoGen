"""Tests for basic LSB encoding and decoding with structured payloads."""

import pytest
from PIL import Image

from stegogen.core.encoder import encode_text
from stegogen.core.decoder import decode_text


@pytest.fixture
def blank_rgb_image(tmp_path):
    """Generate a clean 100x100 RGB image for testing."""
    img_path = tmp_path / "cover.png"
    img = Image.new("RGB", (100, 100), color=(128, 128, 128))
    img.save(img_path)
    return img_path


def test_roundtrip_ascii_message(blank_rgb_image, tmp_path):
    """Verify standard text embeds and decodes identically."""
    stego_path = tmp_path / "stego_ascii.png"
    secret = "Hello World!"
    encode_text(blank_rgb_image, secret, stego_path)
    assert decode_text(stego_path) == secret


def test_roundtrip_unicode_message(blank_rgb_image, tmp_path):
    """Verify multi-byte Unicode strings work properly using standard unicode escapes."""
    stego_path = tmp_path / "stego_unicode.png"
    secret = "StegoGen \U0001F512 -- Unicode: \u0645\u0631\u062d\u0628\u0627, \u0a17\u0a41\u0a2a\u0a24, Caf\u00e9 \U0001F680"
    encode_text(blank_rgb_image, secret, stego_path)
    assert decode_text(stego_path) == secret


def test_empty_message(blank_rgb_image, tmp_path):
    """Verify 0-length messages embed and decode without crashing."""
    stego_path = tmp_path / "stego_empty.png"
    secret = ""
    encode_text(blank_rgb_image, secret, stego_path)
    assert decode_text(stego_path) == ""


def test_capacity_overflow(tmp_path):
    """Verify an exception is raised when data exceeds pixel count."""
    tiny_path = tmp_path / "tiny.png"
    Image.new("RGB", (2, 2), color=(0, 0, 0)).save(tiny_path)  # 12 bits capacity
    message = "Too big for 12 bits"
    with pytest.raises(ValueError, match="Carrier capacity exceeded"):
        encode_text(tiny_path, message, tmp_path / "out.png")


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
