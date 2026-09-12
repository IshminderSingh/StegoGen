"""Advanced Payload Handler: Compression, Metadata, and Binary Packing."""

import zlib
import struct
import os

def pack_payload(file_path: str) -> bytes:
    """
    Reads an arbitrary file, compresses it, and prepends metadata.
    Header format: [4 bytes payload size][10 bytes extension][compressed data]
    """
    # 1. Read raw file bytes
    with open(file_path, "rb") as f:
        raw_data = f.read()

    # 2. Compress the data
    compressed_data = zlib.compress(raw_data, level=9)
    
    # 3. Extract and pad the file extension (e.g., '.pdf', '.zip')
    _, ext = os.path.splitext(file_path)
    ext_bytes = ext.encode('utf-8')[:10].ljust(10, b'\x00')
    
    # 4. Pack metadata: (Size of compressed data as 32-bit unsigned int) + Ext
    size_header = struct.pack(">I", len(compressed_data))
    
    return size_header + ext_bytes + compressed_data

def unpack_payload(extracted_bytes: bytes, output_dir: str = "output"):
    """
    Parses the header, decompresses the data, and writes the original file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Extract headers
    size_header = extracted_bytes[:4]
    compressed_size = struct.unpack(">I", size_header)[0]
    
    ext_bytes = extracted_bytes[4:14]
    ext = ext_bytes.replace(b'\x00', b'').decode('utf-8')
    
    # 2. Extract and decompress payload
    compressed_data = extracted_bytes[14 : 14 + compressed_size]
    raw_data = zlib.decompress(compressed_data)
    
    # 3. Save to disk
    out_path = os.path.join(output_dir, f"extracted_secret{ext}")
    with open(out_path, "wb") as f:
        f.write(raw_data)
        
    return out_path