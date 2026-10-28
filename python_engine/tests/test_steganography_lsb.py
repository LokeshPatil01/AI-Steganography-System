"""Unit and API integration tests for Baseline LSB steganography engine."""
import io
import os
import numpy as np
from PIL import Image
import pytest
from httpx import ASGITransport, AsyncClient

from app.image.loader import ImageLoader, ImageValidationError
from app.main import app
from app.steganography.baseline_lsb import (
    BaselineLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
)
from app.steganography.payload_packer import PayloadCorruptedError

def create_sample_png_bytes(width: int = 128, height: int = 128) -> bytes:
    """Helper creating an in-memory sample RGB PNG image."""
    x = np.linspace(0, 255, width, dtype=np.uint8)
    y = np.linspace(0, 255, height, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    r = xx
    g = yy
    b = ((xx.astype(int) + yy.astype(int)) // 2).astype(np.uint8)

    arr = np.stack([r, g, b], axis=2)
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_image_loader_validates_png_and_dimensions():
    png_bytes = create_sample_png_bytes(64, 64)
    pixels, (w, h) = ImageLoader.load_image(png_bytes)

    assert pixels.shape == (64, 64, 3)
    assert w == 64 and h == 64
    assert pixels.dtype == np.uint8

def test_image_loader_rejects_tiny_dimension():
    tiny_arr = np.zeros((16, 16, 3), dtype=np.uint8)
    img = Image.fromarray(tiny_arr)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    with pytest.raises(ImageValidationError):
        ImageLoader.load_image(buf.getvalue())

def test_capacity_calculation_formula():
    w, h = 100, 100
    arr = np.zeros((h, w, 3), dtype=np.uint8)
    cap = BaselineLSB.calculate_capacity(arr)

    expected_total_bits = 100 * 100 * 3  # 30,000 bits
    expected_raw_bytes = 30000 // 8       # 3,750 bytes
    expected_payload_bytes = expected_raw_bytes - 16  # 3,734 bytes

    assert cap.width == 100
    assert cap.height == 100
    assert cap.total_bits_available == expected_total_bits
    assert cap.header_overhead_bytes == 16
    assert cap.max_payload_bytes == expected_payload_bytes

def test_embed_and_extract_short_message_roundtrip():
    png_bytes = create_sample_png_bytes(100, 100)
    cover_pixels, _ = ImageLoader.load_image(png_bytes)

    secret = "Classified research coordinates for B.Tech project 2026."
    stego_pixels, meta = BaselineLSB.embed(cover_pixels, secret)

    assert meta["payload_bytes"] == len(secret.encode("utf-8"))
    assert meta["total_bits_embedded"] > 0

    # Image visually identical (pixels altered by at most 1 unit in LSB)
    diff = np.abs(stego_pixels.astype(int) - cover_pixels.astype(int))
    assert np.all(diff <= 1)

    # Extract
    recovered_text = BaselineLSB.extract_to_str(stego_pixels)
    assert recovered_text == secret

def test_embed_and_extract_binary_payload_roundtrip():
    png_bytes = create_sample_png_bytes(128, 128)
    cover_pixels, _ = ImageLoader.load_image(png_bytes)

    binary_secret = os.urandom(1024)  # 1 KB of arbitrary random bytes
    stego_pixels, meta = BaselineLSB.embed(cover_pixels, binary_secret)

    recovered_bytes, ext_meta = BaselineLSB.extract(stego_pixels)
    assert recovered_bytes == binary_secret
    assert ext_meta["crc_verified"] is True

def test_overflow_prevention_rejects_oversized_payload():
    # 64x64x3 = 12,288 bits = 1,536 bytes raw - 16 = 1,520 max bytes
    png_bytes = create_sample_png_bytes(64, 64)
    cover_pixels, _ = ImageLoader.load_image(png_bytes)

    oversized_payload = b"X" * 2000

    with pytest.raises(CapacityExceededError):
        BaselineLSB.embed(cover_pixels, oversized_payload)

def test_decode_clean_image_raises_no_stego_payload():
    png_bytes = create_sample_png_bytes(64, 64)
    clean_pixels, _ = ImageLoader.load_image(png_bytes)

    with pytest.raises(NoStegoPayloadFoundError):
        BaselineLSB.extract(clean_pixels)

def test_crc32_catches_corrupted_payload_bits():
    png_bytes = create_sample_png_bytes(64, 64)
    cover_pixels, _ = ImageLoader.load_image(png_bytes)

    secret = "Sensitive verification payload."
    stego_pixels, _ = BaselineLSB.embed(cover_pixels, secret)

    # Intentionally corrupt a bit in the stego payload area (after 16-byte header = 128 bits)
    corrupted_pixels = stego_pixels.copy()
    flat = corrupted_pixels.reshape(-1)
    flat[130] ^= 0x01  # Flip one bit in the payload stream

    with pytest.raises(PayloadCorruptedError):
        BaselineLSB.extract(corrupted_pixels)

# --- FastAPI HTTP Endpoint Tests ---

@pytest.mark.anyio
async def test_fastapi_capacity_endpoint():
    png_bytes = create_sample_png_bytes(80, 80)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("test.png", png_bytes, "image/png")}
        response = await client.post("/capacity", files=files)

    assert response.status_code == 200
    data = response.json()
    assert data["width"] == 80
    assert data["height"] == 80
    assert data["max_payload_bytes"] > 0

@pytest.mark.anyio
async def test_fastapi_encode_and_decode_lifecycle():
    png_bytes = create_sample_png_bytes(100, 100)
    secret_msg = "FastAPI HTTP roundtrip steganography payload test"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. /encode
        files = {"image": ("cover.png", png_bytes, "image/png")}
        data = {"message": secret_msg}
        enc_response = await client.post("/encode", files=files, data=data)

        assert enc_response.status_code == 200
        assert enc_response.headers["content-type"] == "image/png"
        stego_png_bytes = enc_response.content

        # 2. /decode
        dec_files = {"image": ("stego.png", stego_png_bytes, "image/png")}
        dec_response = await client.post("/decode", files=dec_files)

        assert dec_response.status_code == 200
        dec_data = dec_response.json()
        assert dec_data["payload_text"] == secret_msg
        assert dec_data["crc_verified"] is True

@pytest.mark.anyio
async def test_fastapi_encode_rejects_oversized_payload_with_413():
    png_bytes = create_sample_png_bytes(40, 40)  # Very small image
    huge_message = "A" * 10000

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("cover.png", png_bytes, "image/png")}
        data = {"message": huge_message}
        response = await client.post("/encode", files=files, data=data)

    assert response.status_code == 413
    assert "exceeds maximum image capacity" in response.json()["detail"]
