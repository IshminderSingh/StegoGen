# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2026-09-12
### Added
- Complete capacity and overhead analysis system in `core/capacity.py`.
- Automated detection of header framing and AES-GCM salt/nonce/tag overhead.
- Pre-flight capacity checks in `encode_text` and `encode_file`.
- Comprehensive capacity calculation test suite in `tests/test_capacity.py`.

## [0.5.0] - 2026-09-12
### Added
- Arbitrary binary file packaging protocol (`pack_file_data`, `unpack_file_data`) in `core/payload.py`.
- Binary file embedding engine `encode_file` in `core/encoder.py`.
- Safe file reconstruction and output writing `decode_file` in `core/decoder.py`.
- Unit tests covering plaintext files, simulated binary PDFs, and encrypted file hiding in `tests/test_files.py`.

## [0.4.0] - 2026-09-12
### Added
- Authenticated AES-256-GCM encryption engine with random salt and IV generation in `crypto/encryption.py`.
- PBKDF2-HMAC-SHA256 key derivation with 100,000 iterations.
- Integrated encryption/decryption hooks into `core/encoder.py` and `core/decoder.py`.

## [0.3.0] - 2026-09-12
### Added
- Structured binary framing protocol (`STGO` magic header, versioning, bitflags, payload length, CRC32 checksum) in `core/payload.py`.

## [0.2.0] - 2026-09-12
### Added
- Core image utilities and spatial 1-bit LSB encoder/decoder.

## [0.1.0] - 2026-09-12
### Added
- Standard GitHub-ready repository layout and packaging.
