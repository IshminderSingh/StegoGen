"""Structured payload serialization, framing, and integrity verification."""

from dataclasses import dataclass
from pathlib import Path
import zlib

MAGIC_BYTES = b"STGO"
CURRENT_VERSION = 1

# Flag bitmasks
FLAG_ENCRYPTED = 0x01
FLAG_FILE = 0x02

HEADER_SIZE = 14  # 4 (Magic) + 1 (Ver) + 1 (Flags) + 4 (Len) + 4 (CRC32)


@dataclass(frozen=True)
class StegoPayload:
    """Structured in-memory representation of a StegoGen payload."""

    data: bytes
    is_encrypted: bool = False
    is_file: bool = False
    version: int = CURRENT_VERSION


@dataclass(frozen=True)
class ExtractedFile:
    """Structured representation of an extracted embedded file."""

    filename: str
    file_bytes: bytes


def pack_file_data(filename: str, file_bytes: bytes) -> bytes:
    """Pack a filename and file contents into a binary container.

    Wire layout:
      [0:2]   Filename length in bytes (uint16 big-endian)
      [2:2+N] Filename encoded in UTF-8
      [2+N:]  Raw file content bytes
    """
    clean_name = Path(filename).name  # Discard directory paths for security
    name_bytes = clean_name.encode("utf-8")
    if len(name_bytes) > 65535:
        raise ValueError("Filename is too long to encode (max 65,535 bytes).")

    return len(name_bytes).to_bytes(2, byteorder="big") + name_bytes + file_bytes


def unpack_file_data(raw_data: bytes) -> ExtractedFile:
    """Unpack a filename and raw bytes from an extracted file container."""
    if len(raw_data) < 2:
        raise ValueError("Corrupted file payload: header missing.")

    name_len = int.from_bytes(raw_data[:2], byteorder="big")
    if len(raw_data) < 2 + name_len:
        raise ValueError("Corrupted file payload: filename field truncated.")

    filename = raw_data[2 : 2 + name_len].decode("utf-8", errors="replace")
    clean_name = Path(filename).name
    file_bytes = raw_data[2 + name_len :]

    return ExtractedFile(filename=clean_name, file_bytes=file_bytes)


def serialize_payload(
    data: bytes,
    is_encrypted: bool = False,
    is_file: bool = False,
) -> bytes:
    """Pack raw bytes into the structured binary format with integrity checksum."""
    flags = 0
    if is_encrypted:
        flags |= FLAG_ENCRYPTED
    if is_file:
        flags |= FLAG_FILE

    payload_len = len(data)
    crc = zlib.crc32(data) & 0xFFFFFFFF

    header = (
        MAGIC_BYTES
        + bytes([CURRENT_VERSION])
        + bytes([flags])
        + payload_len.to_bytes(4, byteorder="big")
        + crc.to_bytes(4, byteorder="big")
    )
    return header + data


def parse_payload(raw_bytes: bytes) -> StegoPayload:
    """Validate and unpack binary data into a StegoPayload instance."""
    if len(raw_bytes) < HEADER_SIZE:
        raise ValueError("Data too short to contain a valid StegoGen header.")

    magic = raw_bytes[:4]
    if magic != MAGIC_BYTES:
        raise ValueError("Invalid format: StegoGen magic header ('STGO') not found.")

    version = raw_bytes[4]
    if version != CURRENT_VERSION:
        raise ValueError(f"Unsupported payload version: {version}. Expected: {CURRENT_VERSION}.")

    flags = raw_bytes[5]
    is_encrypted = bool(flags & FLAG_ENCRYPTED)
    is_file = bool(flags & FLAG_FILE)

    payload_len = int.from_bytes(raw_bytes[6:10], byteorder="big")
    expected_crc = int.from_bytes(raw_bytes[10:14], byteorder="big")

    total_expected = HEADER_SIZE + payload_len
    if len(raw_bytes) < total_expected:
        raise ValueError(
            f"Incomplete payload: header specifies {payload_len} data bytes, "
            f"but only {len(raw_bytes) - HEADER_SIZE} bytes were provided."
        )

    data = raw_bytes[HEADER_SIZE:total_expected]
    actual_crc = zlib.crc32(data) & 0xFFFFFFFF
    if actual_crc != expected_crc:
        raise ValueError("Data corruption detected: CRC32 checksum verification failed.")

    return StegoPayload(
        data=data,
        is_encrypted=is_encrypted,
        is_file=is_file,
        version=version,
    )
