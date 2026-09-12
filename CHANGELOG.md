# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] - 2026-09-12
### Added
- Complete Tkinter graphical user interface in `gui/app.py`.
- Tabbed view for **Encode** and **Decode** workflows.
- Live image thumbnail preview and dynamic capacity calculations.
- File vs text input toggle with non-executable extraction guards.
- Unit tests for GUI lifecycle in `tests/test_gui.py`.

## [0.6.0] - 2026-09-12
### Added
- Capacity and overhead analysis system in `core/capacity.py`.
- Automated detection of header framing and AES-GCM overhead.
- Pre-flight capacity checks in `encode_text` and `encode_file`.

## [0.5.0] - 2026-09-12
### Added
- Arbitrary binary file packaging protocol (`pack_file_data`, `unpack_file_data`) in `core/payload.py`.
- Binary file embedding engine `encode_file` and extractor `decode_file`.

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
