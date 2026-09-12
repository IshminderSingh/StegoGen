"""Advanced PRNG-Scattered LSB Encoder with AES-GCM & zlib Compression."""

import os
import struct
import hashlib
import tempfile
import gc
import numpy as np
from PIL import Image

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

from stegogen.core.advanced_payload import pack_payload

DEFAULT_SEED = "StegoGen_V1_3_Unencrypted"

def _derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    return kdf.derive(password.encode())

def _get_prng_indices(seed_string: str, max_val: int) -> np.ndarray:
    """Generates a reproducible, shuffled array of pixel coordinates based on the password."""
    seed_int = int(hashlib.sha256(seed_string.encode()).hexdigest(), 16) % (2**32)
    rng = np.random.default_rng(seed_int)
    indices = np.arange(max_val)
    rng.shuffle(indices)
    return indices

def _bytes_to_bits(data: bytes) -> np.ndarray:
    return np.unpackbits(np.frombuffer(data, dtype=np.uint8))

def encode_file(cover_path: str, file_path: str, out_path: str, password: str = None):
    """Compresses, encrypts, and scatters an arbitrary file into an image."""
    packed_bytes = pack_payload(file_path)
    
    if password:
        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = _derive_key(password, salt)
        aesgcm = AESGCM(key)
        encrypted_payload = aesgcm.encrypt(nonce, packed_bytes, None)
        final_payload = salt + nonce + encrypted_payload
        seed = password
    else:
        final_payload = packed_bytes
        seed = DEFAULT_SEED
        
    payload_bits = _bytes_to_bits(final_payload)
    
    # Prepend a 32-bit integer indicating how many bits follow
    length_bits = _bytes_to_bits(struct.pack(">I", len(payload_bits)))
    full_bits = np.concatenate((length_bits, payload_bits))
    
    img = Image.open(cover_path).convert("RGB")
    img_arr = np.array(img)
    flat_img = img_arr.flatten()
    max_capacity = len(flat_img)
    
    if len(full_bits) > max_capacity:
        raise ValueError(f"Payload too large! Need {len(full_bits)} bits, carrier only holds {max_capacity} bits.")
        
    # Generate PRNG sequence and select exact number of coordinates needed
    indices = _get_prng_indices(seed, max_capacity)
    target_indices = indices[:len(full_bits)]
    
    # Perform LSB substitution ONLY on the scattered coordinates
    flat_img[target_indices] = (flat_img[target_indices] & 254) | full_bits
    
    stego_img = flat_img.reshape(img_arr.shape)
    Image.fromarray(stego_img).save(out_path, format="PNG")
    
    # Memory cleanup
    del img_arr, flat_img, payload_bits, full_bits, indices, target_indices
    gc.collect()

def encode_text(cover_path: str, msg: str, out_path: str, password: str = None):
    """Wrapper to keep the UI functional: saves text to a temp file, then embeds it."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        tmp.write(msg.encode('utf-8'))
        tmp_path = tmp.name
        
    try:
        encode_file(cover_path, tmp_path, out_path, password)
    finally:
        os.remove(tmp_path)