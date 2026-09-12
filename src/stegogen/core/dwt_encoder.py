"""Discrete Wavelet Transform (DWT) Frequency Domain Steganography Engine."""

import os
import struct
import numpy as np
import pywt
from PIL import Image
from stegogen.core.advanced_payload import pack_payload, unpack_payload

def encode_dwt_file(cover_path: str, file_path: str, out_path: str):
    """Embeds an arbitrary file into the high-frequency DWT sub-bands of an image."""
    packed_bytes = pack_payload(file_path)
    payload_bits = np.unpackbits(np.frombuffer(packed_bytes, dtype=np.uint8))
    
    # Prepend 32-bit length header
    length_bits = np.unpackbits(np.frombuffer(struct.pack(">I", len(payload_bits)), dtype=np.uint8))
    full_bits = np.concatenate((length_bits, payload_bits))

    # Load image and convert to float channels
    img = Image.open(cover_path).convert("RGB")
    img_arr = np.array(img, dtype=np.float32)

    # Perform 2D Discrete Wavelet Transform using 'db4' wavelet
    coeffs2 = pywt.dwt2(img_arr[:, :, 0], 'db4')
    LL, (LH, HL, HH) = coeffs2

    # Check capacity of High-Frequency sub-bands
    max_capacity = LH.size + HL.size + HH.size
    if len(full_bits) > max_capacity:
        raise ValueError(f"Payload too large for DWT capacity! Need {len(full_bits)} bits, available: {max_capacity}")

    flat_lh = LH.flatten()
    int_lh = flat_lh.astype(np.int64)
    
    bits_to_inject = full_bits[:len(int_lh)]
    int_lh[:len(bits_to_inject)] = (int_lh[:len(bits_to_inject)] & ~1) | bits_to_inject
    
    modified_lh = int_lh.reshape(LH.shape).astype(np.float32)

    # Reconstruct image using inverse DWT
    new_coeffs2 = LL, (modified_lh, HL, HH)
    reconstructed_red = pywt.idwt2(new_coeffs2, 'db4')
    reconstructed_red = np.clip(reconstructed_red, 0, 255)

    stego_arr = img_arr.copy()
    h, w = reconstructed_red.shape
    stego_arr = stego_arr[:h, :w]
    stego_arr[:, :, 0] = reconstructed_red

    final_img = Image.fromarray(stego_arr.astype(np.uint8))
    final_img.save(out_path, format="PNG")

def decode_dwt_file(stego_path: str, output_dir: str = "output") -> str:
    """Extracts hidden data from the DWT frequency domain."""
    img = Image.open(stego_path).convert("RGB")
    img_arr = np.array(img, dtype=np.float32)

    coeffs2 = pywt.dwt2(img_arr[:, :, 0], 'db4')
    LL, (LH, HL, HH) = coeffs2

    flat_lh = LH.flatten().astype(np.int64)
    
    header_bits = flat_lh[:32] & 1
    payload_bit_len = struct.unpack(">I", np.packbits(header_bits).tobytes())[0]

    payload_bits = flat_lh[32 : 32 + payload_bit_len] & 1
    raw_payload = np.packbits(payload_bits).tobytes()

    return unpack_payload(raw_payload, output_dir)