"""Structured payload serialization, framing, and integrity verification."""

from dataclasses import dataclass
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


def serialize_payload(
    data: bytes,
    is_encrypted: bool = False,
    is_file: bool = False,
) -> bytes:
    """Pack raw bytes into the structured binary format with integrity checksum.

    Layout:
      [0:4]   Magic Header (b'STGO')
      [4:5]   Protocol Version (uint8)
      [5:6]   Flags (uint8: bit0=encrypted, bit1=file)
      [6:10]  Payload Length (uint32 big-endian)
      [10:14] CRC32 Checksum of data (uint32 big-endian)
      [14:]   Data bytes
    """
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
    """Validate and unpack binary data into a StegoPayload instance.

    Raises:
        ValueError: If magic bytes mismatch, version is unsupported,
                    length is incomplete, or CRC32 fails.
    """
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
