# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.0] - 2026-09-12
### Added
- Hardening test suite in `tests/test_hardening.py` covering odd dimensions, non-square images, RGBA alpha flattening, and grayscale conversion.
- Zero-byte binary file roundtrip preservation.
- Strict input validation raising `FileNotFoundError` on nonexistent carrier or secret files.
- Full 37-test suite passing cleanly.

## [0.7.0] - 2026-09-12
### Added
- Complete Tkinter graphical user interface in `gui/app.py`.
- Quality analysis module (`utils/analysis.py`) computing MSE, PSNR, and SSIM.

## [0.6.0] - 2026-09-12
### Added
- Capacity and overhead analysis system in `core/capacity.py`.

## [0.5.0] - 2026-09-12
### Added
- Arbitrary binary file packaging protocol in `core/payload.py`.

## [0.4.0] - 2026-09-12
### Added
- Authenticated AES-256-GCM encryption engine and PBKDF2 key derivation.

## [0.3.0] - 2026-09-12
### Added
- Structured binary framing protocol (`STGO` magic header, versioning, bitflags, payload length, CRC32 checksum).

## [0.2.0] - 2026-09-12
### Added
- Core image utilities and spatial 1-bit LSB encoder/decoder.

## [0.1.0] - 2026-09-12
### Added
- Standard GitHub-ready repository layout and packaging.
