"""Cryptographic primitives: Key derivation and authenticated AES-GCM encryption."""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

SALT_SIZE = 16
NONCE_SIZE = 12
KEY_SIZE = 32  # 256 bits
KDF_ITERATIONS = 100_000


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a text password and salt using PBKDF2-HMAC-SHA256.

    Args:
        password: User-provided plaintext password.
        salt: 16-byte cryptographically random salt.

    Returns:
        32-byte derived symmetric key.
    """
    if not password:
        raise ValueError("Password cannot be empty.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=salt,
        iterations=KDF_ITERATIONS,
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_bytes(data: bytes, password: str) -> bytes:
    """Encrypt data using AES-256-GCM with a PBKDF2-derived key.

    Wire format:
      [0:16]  Salt (16 bytes)
      [16:28] Nonce / IV (12 bytes)
      [28:]   Ciphertext + Tag (N + 16 bytes)

    Args:
        data: Plaintext bytes to encrypt.
        password: Plaintext password used for key derivation.

    Returns:
        Combined encrypted container bytes.
    """
    if not password:
        raise ValueError("Password must not be empty for encryption.")

    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    key = derive_key(password, salt)

    aesgcm = AESGCM(key)
    ciphertext_and_tag = aesgcm.encrypt(nonce, data, None)

    return salt + nonce + ciphertext_and_tag


def decrypt_bytes(encrypted_container: bytes, password: str) -> bytes:
    """Decrypt an AES-256-GCM container using the provided password.

    Args:
        encrypted_container: Byte buffer containing salt + nonce + ciphertext + tag.
        password: User password.

    Returns:
        Decrypted plaintext bytes.

    Raises:
        ValueError: If container is too short, password is wrong, or data is tampered.
    """
    min_size = SALT_SIZE + NONCE_SIZE + 16  # 16 bytes minimum for GCM auth tag
    if len(encrypted_container) < min_size:
        raise ValueError("Encrypted data is truncated or too short to be valid.")

    salt = encrypted_container[:SALT_SIZE]
    nonce = encrypted_container[SALT_SIZE : SALT_SIZE + NONCE_SIZE]
    ciphertext_and_tag = encrypted_container[SALT_SIZE + NONCE_SIZE :]

    key = derive_key(password, salt)
    aesgcm = AESGCM(key)

    try:
        return aesgcm.decrypt(nonce, ciphertext_and_tag, None)
    except Exception as exc:
        raise ValueError("Decryption failed: Incorrect password or corrupted data.") from exc
