"""Unit tests for embedding and extracting arbitrary binary files."""

import pytest
from PIL import Image

from stegogen.core.encoder import encode_file
from stegogen.core.decoder import decode_file, decode_text


@pytest.fixture
def carrier_image(tmp_path):
    """Create a 200x200 RGB carrier PNG."""
    path = tmp_path / "carrier.png"
    Image.new("RGB", (200, 200), (70, 80, 90)).save(path)
    return path


def test_roundtrip_text_file(carrier_image, tmp_path):
    """Verify hiding and extracting a plaintext file."""
    secret_txt = tmp_path / "notes.txt"
    secret_txt.write_text("University CSE Viva Notes", encoding="utf-8")

    stego_path = tmp_path / "stego_txt.png"
    out_dir = tmp_path / "recovered_txt"

    encode_file(carrier_image, secret_txt, stego_path)
    restored_path = decode_file(stego_path, out_dir)

    assert restored_path.is_file()
    assert restored_path.name == "notes.txt"
    assert restored_path.read_text(encoding="utf-8") == "University CSE Viva Notes"


def test_roundtrip_binary_pdf_file_encrypted(carrier_image, tmp_path):
    """Verify hiding arbitrary binary data (simulated PDF) with encryption."""
    fake_pdf = tmp_path / "thesis.pdf"
    # PDF magic bytes %PDF- followed by arbitrary binary
    fake_pdf_content = b"%PDF-1.7\n\x00\xFF\xAA\x55RandomBinaryPayloadDataHere"
    fake_pdf.write_bytes(fake_pdf_content)

    stego_path = tmp_path / "stego_pdf.png"
    out_dir = tmp_path / "recovered_pdf"
    password = "SecuredThesisPassword2026"

    encode_file(carrier_image, fake_pdf, stego_path, password=password)

    # Calling decode_text on a file payload should fail with informative error
    with pytest.raises(ValueError, match="Payload contains a file"):
        decode_text(stego_path, password=password)

    # Calling decode_file without password must fail
    with pytest.raises(ValueError, match="Decryption password required"):
        decode_file(stego_path, out_dir)

    # Calling with correct password succeeds
    restored = decode_file(stego_path, out_dir, password=password)
    assert restored.is_file()
    assert restored.name == "thesis.pdf"
    assert restored.read_bytes() == fake_pdf_content
