# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-09-12
### Added
- Arbitrary binary file packaging protocol (`pack_file_data`, `unpack_file_data`) in `core/payload.py`.
- Binary file embedding engine `encode_file` in `core/encoder.py`.
- Safe file reconstruction and output writing `decode_file` in `core/decoder.py` (non-executable extraction).
- Unit tests covering plaintext files, simulated binary PDFs, encrypted file hiding, and separation checks in `tests/test_files.py`.

## [0.4.0] - 2026-09-12
### Added
- Authenticated AES-256-GCM encryption engine with random salt and IV generation in `crypto/encryption.py`.
- PBKDF2-HMAC-SHA256 key derivation with 100,000 iterations.
- Integrated encryption/decryption hooks into `core/encoder.py` and `core/decoder.py`.
- Cryptographic test suite covering salt uniqueness, tampering detection, wrong password failures, and end-to-end encrypted stego roundtrips in `tests/test_crypto.py`.

## [0.3.0] - 2026-09-12
### Added
- Structured binary framing protocol (`STGO` magic header, versioning, bitflags, payload length, CRC32 checksum) in `core/payload.py`.
- Payload verification and corruption rejection logic in `core/decoder.py`.
- Checksum validation and carrier boundary checks.
- Test suite covering framing roundtrip, magic mismatches, corruption detection, and unsupported versions in `tests/test_payload.py`.

## [0.2.0] - 2026-09-12
### Added
- Core image utilities (`load_image_as_rgb`, `save_stego_image`) with channel normalization in `utils/image_utils.py`.
- Spatial 1-bit LSB encoder with unsigned bitmasking in `core/encoder.py`.
- LSB decoder with length-delimited byte recovery in `core/decoder.py`.
- Unit tests covering ASCII, Unicode, zero-length strings, capacity overflow, and file-level immutability in `tests/test_basic_lsb.py`.

## [0.1.0] - 2026-09-12
### Added
- Standard GitHub-ready repository layout.
- Modular Python packaging via `pyproject.toml`.
- Foundation tests and environment configuration.
