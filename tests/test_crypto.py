"""Unit tests for cryptographic primitives and authenticated encryption."""

import pytest
from PIL import Image

from stegogen.crypto.encryption import encrypt_bytes, decrypt_bytes, derive_key
from stegogen.core.encoder import encode_text
from stegogen.core.decoder import decode_text


def test_derive_key_deterministic_with_salt():
    """Verify identical password and salt produce the identical derived key."""
    salt = b"0123456789abcdef"
    key1 = derive_key("masterkey", salt)
    key2 = derive_key("masterkey", salt)
    assert key1 == key2
    assert len(key1) == 32


def test_derive_key_different_salt():
    """Verify different salts produce completely different keys."""
    key1 = derive_key("masterkey", b"0123456789abcdef")
    key2 = derive_key("masterkey", b"fedcba9876543210")
    assert key1 != key2


def test_empty_password_rejected():
    """Verify empty passwords raise ValueError."""
    with pytest.raises(ValueError, match="Password cannot be empty"):
        derive_key("", b"0123456789abcdef")


def test_encryption_roundtrip():
    """Verify plaintext encrypts and decrypts with correct password."""
    secret = b"Highly confidential payload!"
    password = "CorrectHorseBatteryStaple"
    encrypted = encrypt_bytes(secret, password)
    assert encrypted != secret
    decrypted = decrypt_bytes(encrypted, password)
    assert decrypted == secret


def test_wrong_password_fails():
    """Verify decryption fails when given an incorrect password."""
    secret = b"Confidential data"
    encrypted = encrypt_bytes(secret, "good_password")
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_bytes(encrypted, "wrong_password")


def test_tampered_ciphertext_fails():
    """Verify AES-GCM tag verification catches altered ciphertext bits."""
    secret = b"Financial records"
    encrypted = bytearray(encrypt_bytes(secret, "password123"))

    # Flip a single bit in the ciphertext area
    encrypted[-1] ^= 0x01

    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_bytes(bytes(encrypted), "password123")


def test_end_to_end_encrypted_steganography(tmp_path):
    """Verify full pipeline: text -> encrypted -> LSB embedded -> decoded with password."""
    cover_path = tmp_path / "carrier.png"
    stego_path = tmp_path / "stego_enc.png"
    Image.new("RGB", (120, 120), color=(100, 150, 200)).save(cover_path)

    secret = "Top Secret AES-256 Encrypted Message"
    password = "VivaExamPassword2026"

    encode_text(cover_path, secret, stego_path, password=password)

    # 1. Decoding without password must fail
    with pytest.raises(ValueError, match="Decryption password required"):
        decode_text(stego_path)

    # 2. Decoding with wrong password must fail
    with pytest.raises(ValueError, match="Decryption failed"):
        decode_text(stego_path, password="WrongPassword")

    # 3. Decoding with correct password recovers exact message
    recovered = decode_text(stego_path, password=password)
    assert recovered == secret
