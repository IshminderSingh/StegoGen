# StegoGen System Architecture

StegoGen separates the presentation layer, cryptographic engine, payload layout, and spatial bit embedding into distinct modules.

```mermaid
flowchart TD
    subgraph Encoding
        Msg[Secret Message / File] --> P[Payload Serialization]
        P --> C[AES-256-GCM Encryption]
        C --> L[LSB Substitution Engine]
        Img[Original Cover PNG] --> L
        L --> Out[Stego PNG]
    end

    subgraph Decoding
        StegoIn[Stego PNG] --> Ext[LSB Bit Extractor]
        Ext --> Dec[AES-256-GCM Decryption]
        Dec --> Unpack[Payload Parser]
        Unpack --> Rec[Recovered Message / File]
    end