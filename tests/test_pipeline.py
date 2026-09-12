"""Automated End-to-End StegoGen Pipeline Tests."""

import os
import shutil
from PIL import Image
import numpy as np

from stegogen.core.encoder import encode_text, decode_text
from stegogen.core.dwt_encoder import encode_dwt_file, decode_dwt_file

def setup_test_environment():
    os.makedirs("tests/output", exist_ok=True)
    # Create a dummy 300x300 cover image
    img = Image.fromarray(np.random.randint(0, 255, (300, 300, 3), dtype=np.uint8))
    img.save("tests/cover.png")

def test_spatial_pipeline():
    setup_test_environment()
    cover = "tests/cover.png"
    stego = "tests/output/spatial_stego.png"
    secret = "Confidential PRNG test message 12345!"
    
    # Encode
    encode_text(cover, secret, stego, password="SecurePassword123")
    assert os.path.exists(stego), "Spatial stego image was not created."
    
    # Decode
    revealed = decode_text(stego, password="SecurePassword123")
    assert revealed == secret, f"Mismatch! Expected '{secret}', got '{revealed}'"
    print("[PASS] Spatial PRNG Pipeline Test Passed.")

def test_dwt_pipeline():
    cover = "tests/cover.png"
    stego = "tests/output/dwt_stego.png"
    
    # Write a temporary text file for DWT file packer
    txt_path = "tests/temp_payload.txt"
    secret = "DWT frequency domain hidden text payload."
    with open(txt_path, "w") as f:
        f.write(secret)
        
    try:
        encode_dwt_file(cover, txt_path, stego)
        assert os.path.exists(stego), "DWT stego image was not created."
        
        extracted_path = decode_dwt_file(stego, output_dir="tests/output/extracted")
        with open(extracted_path, "r") as f:
            revealed = f.read()
            
        assert revealed == secret, f"Mismatch! Expected '{secret}', got '{revealed}'"
        print("[PASS] Frequency DWT Pipeline Test Passed.")
    finally:
        if os.path.exists(txt_path):
            os.remove(txt_path)
            
if __name__ == "__main__":
    test_spatial_pipeline()
    test_dwt_pipeline()
    shutil.rmtree("tests")
    print("All optimization and test checks cleared successfully.")