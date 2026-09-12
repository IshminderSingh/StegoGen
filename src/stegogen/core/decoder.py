"""Advanced PRNG-Scattered LSB Decoder with AES-GCM & zlib Decompression."""

import os
import struct
import hashlib
import numpy as np
from PIL import Image

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from stegogen.core.advanced_payload import unpack_payload

DEFAULT_SEED = "StegoGen_V1_3_Unencrypted"

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(password.encode())

def _get_prng_indices(seed_string: str, max_val: int) -> np.ndarray:
    """Reconstructs the exact pixel sequence using the password as the seed."""
    seed_int = int(hashlib.sha256(seed_string.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed_int)
    indices = np.arange(max_val)
    rng.shuffle(indices)
    return indices

def decode_file(stego_path: str, output_dir: str = "output", password: str = None) -> str:
    """Reconstructs the PRNG path, decrypts, and unpacks the hidden file."""
    img = Image.open(stego_path).convert("RGB")
    flat_img = np.array(img).flatten()
    max_capacity = len(flat_img)
    
    seed = password if password else DEFAULT_SEED
    indices = _get_prng_indices(seed, max_capacity)
    
    # 1. Read the first 32 scattered bits to determine payload length
    header_indices = indices[:32]
    header_bits = flat_img[header_indices] & 1
    
    try:
        payload_bit_len = struct.unpack(">I", np.packbits(header_bits).tobytes())[0]
    except Exception:
        raise ValueError("Image corrupted or incorrect password (failed to read header length).")
    
    if payload_bit_len == 0 or payload_bit_len > max_capacity - 32:
        raise ValueError("Invalid payload length detected. Incorrect password or image is not a StegoGen carrier.")
        
    # 2. Extract the scattered payload bits
    payload_indices = indices[32 : 32 + payload_bit_len]
    payload_bits = flat_img[payload_indices] & 1
    raw_payload = np.packbits(payload_bits).tobytes()
    
    # 3. Decrypt
    if password:
        if len(raw_payload) < 28: # Salt (16) + Nonce (12) minimum
            raise ValueError("Payload too small to contain encryption parameters.")
            
        salt = raw_payload[:16]
        nonce = raw_payload[16:28]
        ciphertext = raw_payload[28:]
        
        key = _derive_key(password, salt)
        aesgcm = AESGCM(key)
        try:
            final_bytes = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            raise ValueError("AES-GCM Authentication Failed: Wrong password or tampered image.")
    else:
        final_bytes = raw_payload
        
    # 4. Decompress and restore the file structure
    return unpack_payload(final_bytes, output_dir)

def decode_text(stego_path: str, password: str = None) -> str:
    """Wrapper to extract the file to disk, read its text contents, and clean it up."""
    extracted_path = decode_file(stego_path, output_dir="temp_extract", password=password)
    
    try:
        with open(extracted_path, "rb") as f:
            text = f.read().decode('utf-8')
    finally:
        os.remove(extracted_path)
        
    return text