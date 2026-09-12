# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-09-12
### Added
- Core image utilities (`load_image_as_rgb`, `save_stego_image`) with channel normalization in `utils/image_utils.py`.
- Spatial 1-bit LSB encoder with 32-bit length prefix and `uint8` bitmasking in `core/encoder.py`.
- LSB decoder with length-delimited byte recovery in `core/decoder.py`.
- Unit tests covering ASCII, Unicode, zero-length strings, capacity overflow, and file-level immutability in `tests/test_basic_lsb.py`.

## [0.1.0] - 2026-09-12
### Added
- Standard GitHub-ready repository layout.
- Modular Python packaging via `pyproject.toml`.
- Foundation tests and environment configuration.
