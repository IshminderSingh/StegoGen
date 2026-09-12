"""Objective image quality analysis: MSE, PSNR, and SSIM."""

from dataclasses import dataclass
from pathlib import Path
import math
import numpy as np
from PIL import Image

from stegogen.utils.image_utils import load_image_as_rgb


@dataclass(frozen=True)
class QualityMetrics:
    """Quantitative quality comparison between cover and stego images."""

    mse: float
    psnr_db: float
    ssim: float
    cover_size_bytes: int
    stego_size_bytes: int
    is_identical: bool

    def summary(self) -> str:
        """Formatted quality summary for reporting and viva demonstrations."""
        psnr_str = "Infinity (Identical)" if math.isinf(self.psnr_db) else f"{self.psnr_db:.2f} dB"
        return (
            f"--- Image Quality Analysis ---\n"
            f"Mean Squared Error (MSE): {self.mse:.4f} (Lower is better, 0 is identical)\n"
            f"Peak Signal-to-Noise Ratio (PSNR): {psnr_str} (>40 dB is imperceptible)\n"
            f"Structural Similarity Index (SSIM): {self.ssim:.5f} (1.0 is identical)\n"
            f"Cover File Size: {self.cover_size_bytes:,} bytes\n"
            f"Stego File Size: {self.stego_size_bytes:,} bytes\n"
            f"Identical Pixels: {'Yes' if self.is_identical else 'No'}"
        )


def calculate_mse(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Calculate Mean Squared Error (MSE) between two image arrays."""
    if image_a.shape != image_b.shape:
        raise ValueError(f"Image shapes do not match: {image_a.shape} vs {image_b.shape}")
    diff = image_a.astype(np.float64) - image_b.astype(np.float64)
    return float(np.mean(diff ** 2))


def calculate_psnr(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Calculate Peak Signal-to-Noise Ratio (PSNR) in decibels (dB)."""
    mse = calculate_mse(image_a, image_b)
    if mse == 0.0:
        return float("inf")
    max_pixel = 255.0
    return float(20.0 * math.log10(max_pixel / math.sqrt(mse)))


def calculate_ssim(image_a: np.ndarray, image_b: np.ndarray) -> float:
    """Calculate Structural Similarity Index (SSIM) between two RGB images.

    Implementation follows the Wang et al. (2004) structural formula.
    """
    if image_a.shape != image_b.shape:
        raise ValueError("Image dimensions must match for SSIM calculation.")

    # Convert to grayscale luminance (Y channel)
    # Y = 0.299 R + 0.587 G + 0.114 B
    weights = np.array([0.299, 0.587, 0.114])
    x = np.dot(image_a.astype(np.float64), weights)
    y = np.dot(image_b.astype(np.float64), weights)

    mu_x = float(np.mean(x))
    mu_y = float(np.mean(y))

    sigma_x_sq = float(np.var(x))
    sigma_y_sq = float(np.var(y))
    sigma_xy = float(np.mean((x - mu_x) * (y - mu_y)))

    # Stability constants
    c1 = (0.01 * 255) ** 2
    c2 = (0.03 * 255) ** 2

    numerator = (2 * mu_x * mu_y + c1) * (2 * sigma_xy + c2)
    denominator = (mu_x ** 2 + mu_y ** 2 + c1) * (sigma_x_sq + sigma_y_sq + c2)

    return float(numerator / denominator)


def compare_images(
    cover_image_path: str | Path,
    stego_image_path: str | Path,
) -> QualityMetrics:
    """Evaluate quality degradation between cover image and stego image."""
    cover_p = Path(cover_image_path)
    stego_p = Path(stego_image_path)

    if not cover_p.is_file():
        raise FileNotFoundError(f"Cover image not found: {cover_p}")
    if not stego_p.is_file():
        raise FileNotFoundError(f"Stego image not found: {stego_p}")

    img_cover = load_image_as_rgb(cover_p)
    img_stego = load_image_as_rgb(stego_p)

    arr_cover = np.array(img_cover, dtype=np.uint8)
    arr_stego = np.array(img_stego, dtype=np.uint8)

    mse = calculate_mse(arr_cover, arr_stego)
    psnr_db = calculate_psnr(arr_cover, arr_stego)
    ssim = calculate_ssim(arr_cover, arr_stego)

    return QualityMetrics(
        mse=mse,
        psnr_db=psnr_db,
        ssim=ssim,
        cover_size_bytes=cover_p.stat().st_size,
        stego_size_bytes=stego_p.stat().st_size,
        is_identical=(mse == 0.0),
    )
