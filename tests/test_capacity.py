"""Unit tests for capacity calculations and overhead management."""

import pytest
from PIL import Image

from stegogen.core.capacity import assess_capacity, calculate_overhead, get_image_carrier_bytes


def test_carrier_bytes_calculation():
    """Verify width * height * 3 // 8 produces accurate byte count."""
    img = Image.new("RGB", (100, 100))
    w, h, channels, carrier_bytes = get_image_carrier_bytes(img)
    assert w == 100
    assert h == 100
    assert channels == 3
    # 100 * 100 * 3 = 30,000 bits // 8 = 3,750 bytes
    assert carrier_bytes == 3750


def test_calculate_overhead_matrix():
    """Verify overhead accounting for unencrypted, encrypted, and file variants."""
    base = calculate_overhead(is_encrypted=False, is_file=False)
    assert base == 14  # STGO header

    enc = calculate_overhead(is_encrypted=True, is_file=False)
    assert enc == 14 + 44  # Header + Salt(16) + Nonce(12) + Tag(16) = 58

    file_unenc = calculate_overhead(is_encrypted=False, is_file=True, filename="data.txt")
    assert file_unenc == 14 + 2 + len("data.txt")

    file_enc = calculate_overhead(is_encrypted=True, is_file=True, filename="data.txt")
    assert file_enc == 14 + 44 + 2 + len("data.txt")


def test_capacity_assessment_fit(tmp_path):
    """Verify assessment marks payload as fitting with accurate remaining metrics."""
    img_path = tmp_path / "img.png"
    Image.new("RGB", (200, 200)).save(img_path)  # 200*200*3 // 8 = 15,000 bytes

    report = assess_capacity(img_path, "Short secret text", is_encrypted=True, is_file=False)

    assert report.fits is True
    assert report.total_carrier_bytes == 15000
    assert report.total_required_bytes == 58 + len("Short secret text".encode("utf-8"))
    assert report.remaining_bytes == report.total_carrier_bytes - report.total_required_bytes
    assert report.usage_percentage < 1.0


def test_capacity_assessment_overflow(tmp_path):
    """Verify assessment identifies oversized payloads accurately."""
    tiny_path = tmp_path / "tiny.png"
    Image.new("RGB", (4, 4)).save(tiny_path)  # 4*4*3 = 48 bits // 8 = 6 bytes

    report = assess_capacity(tiny_path, "This string is much larger than 6 bytes", is_encrypted=False)

    assert report.fits is False
    assert report.remaining_bytes < 0
    assert "INSUFFICIENT CAPACITY" in report.summary()
