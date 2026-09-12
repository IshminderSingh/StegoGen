"""Unit tests for image quality analysis metrics: MSE, PSNR, and SSIM."""

import pytest
import math
import numpy as np
from PIL import Image

from stegogen.utils.analysis import calculate_mse, calculate_psnr, calculate_ssim, compare_images
from stegogen.core.encoder import encode_text


def test_identical_images_metrics():
    """Verify identical images yield MSE=0, PSNR=inf, SSIM=1.0."""
    arr = np.full((100, 100, 3), 120, dtype=np.uint8)
    assert calculate_mse(arr, arr) == 0.0
    assert math.isinf(calculate_psnr(arr, arr))
    assert calculate_ssim(arr, arr) == 1.0


def test_known_mse_and_psnr_shift():
    """Verify calculated metrics match exact mathematical definitions."""
    arr1 = np.zeros((10, 10, 3), dtype=np.uint8)
    # Add an absolute difference of 1 to every pixel
    arr2 = np.ones((10, 10, 3), dtype=np.uint8)

    mse = calculate_mse(arr1, arr2)
    assert mse == 1.0

    # PSNR for MSE=1 is 20 * log10(255 / 1) = 48.1308 dB
    psnr = calculate_psnr(arr1, arr2)
    assert round(psnr, 2) == 48.13


def test_stego_quality_benchmark(tmp_path):
    """Verify 1-bit LSB stego image achieves high visual fidelity (PSNR > 50 dB, SSIM > 0.99)."""
    cover_path = tmp_path / "carrier.png"
    stego_path = tmp_path / "stego.png"

    # Create a textured gradient carrier image
    arr = np.zeros((120, 120, 3), dtype=np.uint8)
    for i in range(120):
        for j in range(120):
            arr[i, j] = [i + 50, j + 50, (i + j) // 2 + 30]
    Image.fromarray(arr).save(cover_path)

    encode_text(cover_path, "College Steganography Evaluation Secret", stego_path)

    metrics = compare_images(cover_path, stego_path)

    assert metrics.is_identical is False
    assert metrics.mse < 1.0
    assert metrics.psnr_db > 50.0  # Demonstrates visual imperceptibility
    assert metrics.ssim > 0.999    # Demonstrates structural preservation
