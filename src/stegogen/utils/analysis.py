"""Quantitative image quality comparison and statistical steganalysis."""

import math
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Any, Tuple
import numpy as np
from PIL import Image


@dataclass(frozen=True)
class QualityMetrics:
    """Quantitative quality metrics between cover and stego images."""

    mse: float
    mse_rgb: Tuple[float, float, float]
    psnr_db: float
    ssim: float
    cover_size_bytes: int
    stego_size_bytes: int
    is_identical: bool
    cover_hist: np.ndarray
    stego_hist: np.ndarray


def _calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """Computes Structural Similarity Index across RGB channels."""
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)

    mu1 = img1.mean()
    mu2 = img2.mean()

    sigma1_sq = np.mean((img1 - mu1) ** 2)
    sigma2_sq = np.mean((img2 - mu2) ** 2)
    sigma12 = np.mean((img1 - mu1) * (img2 - mu2))

    numerator = (2 * mu1 * mu2 + c1) * (2 * sigma12 + c2)
    denominator = (mu1**2 + mu2**2 + c1) * (sigma1_sq + sigma2_sq + c2)

    return float(numerator / denominator)


def compare_images(cover_image_path: str | Path, stego_image_path: str | Path) -> QualityMetrics:
    """Compares original carrier (PNG or JPG) with generated stego PNG."""
    cover_p = Path(cover_image_path)
    stego_p = Path(stego_image_path)

    if not cover_p.exists():
        raise FileNotFoundError(f"Cover image not found: {cover_p}")
    if not stego_p.exists():
        raise FileNotFoundError(f"Stego image not found: {stego_p}")

    with Image.open(cover_p) as c_img, Image.open(stego_p) as s_img:
        cover_arr = np.array(c_img.convert("RGB"), dtype=np.float64)
        stego_arr = np.array(s_img.convert("RGB"), dtype=np.float64)

    if cover_arr.shape != stego_arr.shape:
        raise ValueError(f"Image dimensions do not match: {cover_arr.shape} vs {stego_arr.shape}")

    is_identical = np.array_equal(cover_arr, stego_arr)
    
    # Channel-wise MSE: R, G, B
    diff_sq = (cover_arr - stego_arr) ** 2
    mse_r = float(np.mean(diff_sq[:, :, 0]))
    mse_g = float(np.mean(diff_sq[:, :, 1]))
    mse_b = float(np.mean(diff_sq[:, :, 2]))
    mse = float(np.mean(diff_sq))

    if mse == 0.0 or is_identical:
        psnr_db = float("inf")
        ssim_val = 1.0
    else:
        psnr_db = float(10.0 * math.log10((255.0 ** 2) / mse))
        ssim_val = max(0.0, min(1.0, _calculate_ssim(cover_arr, stego_arr)))

    # Compute luminance histograms (0-255) for visual overlay graphs
    c_lum = (0.299 * cover_arr[:, :, 0] + 0.587 * cover_arr[:, :, 1] + 0.114 * cover_arr[:, :, 2]).astype(np.uint8)
    s_lum = (0.299 * stego_arr[:, :, 0] + 0.587 * stego_arr[:, :, 1] + 0.114 * stego_arr[:, :, 2]).astype(np.uint8)
    c_hist, _ = np.histogram(c_lum, bins=64, range=(0, 256))
    s_hist, _ = np.histogram(s_lum, bins=64, range=(0, 256))

    return QualityMetrics(
        mse=mse,
        mse_rgb=(mse_r, mse_g, mse_b),
        psnr_db=psnr_db,
        ssim=ssim_val,
        cover_size_bytes=cover_p.stat().st_size,
        stego_size_bytes=stego_p.stat().st_size,
        is_identical=is_identical,
        cover_hist=c_hist,
        stego_hist=s_hist
    )


def generate_diff_heatmap(cover_path: str | Path, stego_path: str | Path, amplification: int = 150) -> Image.Image:
    """Generates an amplified residual heatmap showing bit alterations."""
    with Image.open(cover_path) as c_img, Image.open(stego_path) as s_img:
        c_arr = np.array(c_img.convert("RGB"), dtype=np.int16)
        s_arr = np.array(s_img.convert("RGB"), dtype=np.int16)

    diff = np.abs(s_arr - c_arr) * amplification
    diff_clipped = np.clip(diff, 0, 255).astype(np.uint8)
    return Image.fromarray(diff_clipped, mode="RGB")


def analyze_pairs_of_values(image_path: str | Path) -> Dict[str, Any]:
    """Evaluates Pairs of Values (PoV) uniformity in luminance for LSB steganalysis."""
    with Image.open(image_path) as img:
        arr = np.array(img.convert("L"), dtype=np.uint8).flatten()

    hist, _ = np.histogram(arr, bins=256, range=(0, 256))
    even_counts = hist[0::2]
    odd_counts = hist[1::2]

    diffs = np.abs(even_counts.astype(np.float64) - odd_counts.astype(np.float64))
    total_pairs = np.sum(even_counts + odd_counts)

    balance_ratio = float(np.sum(diffs) / total_pairs) if total_pairs > 0 else 0.0
    suspicion_score = max(0.0, min(100.0, (1.0 - (balance_ratio / 0.05)) * 100.0))

    return {
        "balance_ratio": balance_ratio,
        "suspicion_pct": suspicion_score,
        "stego_detected": suspicion_score > 60.0
    }