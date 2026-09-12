"""Capacity estimation and carrier boundary validation."""

from dataclasses import dataclass
from pathlib import Path
from PIL import Image

from stegogen.core.payload import HEADER_SIZE
from stegogen.crypto.encryption import SALT_SIZE, NONCE_SIZE
from stegogen.utils.image_utils import load_image_as_rgb

GCM_TAG_SIZE = 16
CRYPTO_OVERHEAD = SALT_SIZE + NONCE_SIZE + GCM_TAG_SIZE  # 44 bytes
FILE_HEADER_FIXED = 2  # uint16 length field


@dataclass(frozen=True)
class CapacityReport:
    """Detailed calculation report on carrier and payload capacities."""

    width: int
    height: int
    channels: int
    total_carrier_bytes: int
    overhead_bytes: int
    max_usable_bytes: int
    payload_bytes: int
    total_required_bytes: int
    remaining_bytes: int
    usage_percentage: float
    fits: bool

    def summary(self) -> str:
        """User-friendly human-readable representation for CLI and GUI displays."""
        carrier_kb = self.total_carrier_bytes / 1024.0
        usable_kb = self.max_usable_bytes / 1024.0
        req_kb = self.total_required_bytes / 1024.0
        rem_kb = self.remaining_bytes / 1024.0

        status = "FITS" if self.fits else "INSUFFICIENT CAPACITY"
        return (
            f"Image Geometry: {self.width}x{self.height} ({self.channels} channels)\n"
            f"Total Carrier Capacity: {carrier_kb:.2f} KB ({self.total_carrier_bytes:,} bytes)\n"
            f"Usable Carrier Capacity: {usable_kb:.2f} KB ({self.max_usable_bytes:,} bytes)\n"
            f"Required Payload Size: {req_kb:.2f} KB ({self.total_required_bytes:,} bytes)\n"
            f"Remaining Capacity: {rem_kb:.2f} KB ({self.remaining_bytes:,} bytes)\n"
            f"Capacity Usage: {self.usage_percentage:.2f}%\n"
            f"Status: {status}"
        )


def calculate_overhead(is_encrypted: bool = False, is_file: bool = False, filename: str | None = None) -> int:
    """Calculate fixed byte overhead required for headers and crypto padding."""
    overhead = HEADER_SIZE
    if is_encrypted:
        overhead += CRYPTO_OVERHEAD
    if is_file:
        name_len = len(Path(filename).name.encode("utf-8")) if filename else 0
        overhead += FILE_HEADER_FIXED + name_len
    return overhead


def get_image_carrier_bytes(image: Image.Image | str | Path) -> tuple[int, int, int, int]:
    """Return (width, height, channels, total_carrier_bytes) for an image."""
    if isinstance(image, (str, Path)):
        img = load_image_as_rgb(image)
    else:
        img = image.convert("RGB") if image.mode != "RGB" else image

    w, h = img.size
    channels = 3  # RGB
    total_bits = w * h * channels
    total_bytes = total_bits // 8
    return w, h, channels, total_bytes


def assess_capacity(
    image: Image.Image | str | Path,
    payload_data: bytes | str | Path,
    is_encrypted: bool = False,
    is_file: bool = False,
) -> CapacityReport:
    """Compute detailed capacity breakdown and verify whether payload fits in carrier.

    Args:
        image: PIL Image or path to cover image.
        payload_data: String message, raw bytes, or Path to a file to hide.
        is_encrypted: Whether password encryption is requested.
        is_file: Whether payload is an arbitrary binary file.

    Returns:
        CapacityReport with comprehensive metrics.
    """
    w, h, channels, total_carrier = get_image_carrier_bytes(image)

    filename = None
    if is_file:
        if isinstance(payload_data, (str, Path)) and Path(payload_data).is_file():
            file_p = Path(payload_data)
            filename = file_p.name
            raw_payload_size = file_p.stat().st_size
        elif isinstance(payload_data, bytes):
            filename = "secret.bin"
            raw_payload_size = len(payload_data)
        else:
            raw_payload_size = len(str(payload_data).encode("utf-8"))
    else:
        if isinstance(payload_data, str):
            raw_payload_size = len(payload_data.encode("utf-8"))
        elif isinstance(payload_data, bytes):
            raw_payload_size = len(payload_data)
        else:
            raw_payload_size = 0

    overhead = calculate_overhead(is_encrypted=is_encrypted, is_file=is_file, filename=filename)
    total_required = overhead + raw_payload_size
    max_usable = max(0, total_carrier - overhead)
    remaining = total_carrier - total_required
    fits = total_required <= total_carrier

    usage_pct = (total_required / total_carrier * 100.0) if total_carrier > 0 else 100.0

    return CapacityReport(
        width=w,
        height=h,
        channels=channels,
        total_carrier_bytes=total_carrier,
        overhead_bytes=overhead,
        max_usable_bytes=max_usable,
        payload_bytes=raw_payload_size,
        total_required_bytes=total_required,
        remaining_bytes=remaining,
        usage_percentage=min(usage_pct, 100.0),
        fits=fits,
    )
