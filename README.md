# StegoGen

**Secure Image Steganography Generator**

An educational, offline-capable desktop application built with Python to securely embed encrypted messages and files inside lossless carrier images using spatial LSB (Least Significant Bit) steganography.

---

## Architecture

```mermaid
flowchart LR
    Cover[Cover PNG] --> Embed[LSB Embedder]
    Secret[Secret Data] --> Encrypt[AES-GCM] --> Payload[Structured Payload] --> Embed
    Embed --> Stego[Stego PNG]