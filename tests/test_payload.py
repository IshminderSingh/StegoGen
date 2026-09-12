"""Tests for structured payload serialization, framing, and corruption detection."""

import pytest
import numpy as np

from stegogen.core.payload import (
    serialize_payload,
    parse_payload,
)
from stegogen.core.decoder import extract_payload_from_array


def test_payload_serialization_roundtrip():
    """Verify serialization and parsing preserve data and flags."""
    raw = b"Structured payload test bytes"
    packed = serialize_payload(raw, is_encrypted=True, is_file=False)
    unpacked = parse_payload(packed)

    assert unpacked.data == raw
    assert unpacked.is_encrypted is True
    assert unpacked.is_file is False
    assert unpacked.version == 1


def test_detect_invalid_magic():
    """Verify non-StegoGen data is rejected immediately."""
    fake_data = b"RAND" + b"\x00" * 20
    with pytest.raises(ValueError, match="StegoGen magic header"):
        parse_payload(fake_data)


def test_detect_corrupted_crc32():
    """Verify modifying a single byte triggers CRC32 failure."""
    raw = b"Sensitive data"
    packed = bytearray(serialize_payload(raw))

    # Corrupt last byte of the payload
    packed[-1] ^= 0xFF

    with pytest.raises(ValueError, match="Data corruption detected: CRC32"):
        parse_payload(bytes(packed))


def test_detect_unsupported_version():
    """Verify future/invalid versions are rejected."""
    raw = b"data"
    packed = bytearray(serialize_payload(raw))
    packed[4] = 99  # Change version to 99

    with pytest.raises(ValueError, match="Unsupported payload version"):
        parse_payload(bytes(packed))


def test_clean_image_rejection():
    """Ensure standard image without payload is rejected gracefully."""
    blank_pixels = np.zeros((50, 50, 3), dtype=np.uint8)
    with pytest.raises(ValueError, match="No StegoGen secret found"):
        extract_payload_from_array(blank_pixels)
