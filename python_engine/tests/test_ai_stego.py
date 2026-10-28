"""Unit and Integration Tests for AI-Selected Adaptive Steganography (Phase 14).

Validates:
- AiPayloadPacker wire framing and CRC-32 integrity.
- MSB-plane invariance guarantee: block ranking is 100% identical between cover and stego.
- Capacity calculation with smooth region preservation.
- Embed and extract roundtrips for text and binary payloads.
- Selective embedding: smooth blocks are 100% untouched when payload fits in textured regions.
- CapacityExceededError on oversized payloads.
- NoStegoPayloadFoundError on clean cover images.
- PayloadCorruptedError on tampered stego bitstream.
- 3-way empirical comparison method (Baseline vs. Rule-Based vs. AI-Adaptive).
- FastAPI endpoints: /ai-stego/capacity, /ai-stego/encode, /ai-stego/decode, /ai-stego/compare.
"""
import io
import os
import struct
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.image.loader import ImageLoader
from app.main import app
from app.steganography.ai_stego import (
    AiAdaptiveLSB,
    AiPayloadPacker,
    CapacityExceededError,
    NoStegoPayloadFoundError,
    PayloadCorruptedError,
)


def _create_synthetic_test_image(width: int = 64, height: int = 64) -> np.ndarray:
    """Creates a deterministic synthetic test image containing both smooth and highly textured blocks."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    # Top half: solid uniform color (Class 0: Smooth)
    img[: height // 2, :, :] = 128

    # Bottom half: high texture pseudo-random noise (Class 2: HighTexture)
    rng = np.random.RandomState(42)
    noise = rng.randint(0, 256, size=(height // 2, width, 3)).astype(np.uint8)
    img[height // 2 :, :, :] = noise
    return img


def _png_bytes_from_array(arr: np.ndarray) -> bytes:
    """Converts numpy array to in-memory PNG bytes."""
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


# -------------------------------------------------------------------------
# Unit Tests: Payload Packer
# -------------------------------------------------------------------------

def test_ai_payload_packer_pack_and_unpack():
    payload = b"Research-Grade AI Steganography Payload 2026"
    packed = AiPayloadPacker.pack(payload)

    assert packed.startswith(b"STEGAI01")
    assert len(packed) == 16 + len(payload)

    extracted_len, crc = AiPayloadPacker.unpack_header(packed)
    assert extracted_len == len(payload)
    assert crc > 0


def test_ai_payload_packer_header_mismatch():
    invalid_frame = b"BADMAGIC" + b"\x00" * 8
    with pytest.raises(NoStegoPayloadFoundError, match="magic header mismatch"):
        AiPayloadPacker.unpack_header(invalid_frame)


def test_ai_payload_packer_truncated_header():
    with pytest.raises(NoStegoPayloadFoundError, match="Insufficient data"):
        AiPayloadPacker.unpack_header(b"SHORT")


# -------------------------------------------------------------------------
# Unit Tests: AI Region Ranking & MSB-Plane Invariance
# -------------------------------------------------------------------------

def test_ai_rank_blocks_order_and_invariance():
    """Mathematical verification: Feature extraction on pixel & 0xFE produces
    identical block rankings before and after 1-bit LSB embedding.
    """
    cover = _create_synthetic_test_image(64, 64)
    ranked_cover = AiAdaptiveLSB.rank_blocks_with_ai(cover, block_size=16)

    assert len(ranked_cover) == 16  # (64/16) * (64/16) = 16 blocks
    # Verify descending sort order by suitability_score
    for i in range(len(ranked_cover) - 1):
        assert ranked_cover[i].suitability_score >= ranked_cover[i + 1].suitability_score

    # Embed test payload
    payload = b"Invariance test string 12345"
    stego, _ = AiAdaptiveLSB.embed(cover, payload, block_size=16)

    # Re-rank stego blocks
    ranked_stego = AiAdaptiveLSB.rank_blocks_with_ai(stego, block_size=16)

    cover_order = [(b.by, b.bx, b.suitability_score) for b in ranked_cover]
    stego_order = [(b.by, b.bx, b.suitability_score) for b in ranked_stego]

    # Block rankings must match exactly between sender (cover) and receiver (stego)
    assert cover_order == stego_order


# -------------------------------------------------------------------------
# Unit Tests: Capacity & Preservation
# -------------------------------------------------------------------------

def test_ai_stego_capacity_calculation():
    cover = _create_synthetic_test_image(64, 64)
    cap = AiAdaptiveLSB.calculate_capacity(cover, block_size=16)

    assert cap["width"] == 64
    assert cap["height"] == 64
    assert cap["total_blocks"] == 16
    assert cap["bits_per_block"] == 16 * 16 * 3  # 768 bits
    assert cap["bytes_per_block"] == 96  # 768 / 8 = 96 bytes
    assert cap["total_capacity_bytes"] == 16 * 96  # 1536 bytes
    assert cap["max_payload_bytes"] == 1536 - 16  # 1520 bytes
    assert cap["high_texture_blocks"] + cap["medium_texture_blocks"] + cap["smooth_blocks"] == 16
    assert cap["ai_usable_blocks"] >= 0


def test_ai_stego_smooth_regions_preserved():
    """Verify that smooth regions are 100% untouched when payload fits within textured regions."""
    cover = _create_synthetic_test_image(64, 64)
    # 40 bytes easily fits within 1 textured block (96 bytes available)
    payload = b"Small payload destined only for texture"

    stego, meta = AiAdaptiveLSB.embed(cover, payload, block_size=16)
    assert meta["blocks_utilized"] >= 1
    assert meta["blocks_preserved_smooth"] >= 1

    # Check that top 32 lines (smooth region) have zero pixel modifications
    top_half_cover = cover[:32, :, :]
    top_half_stego = stego[:32, :, :]
    np.testing.assert_array_equal(top_half_cover, top_half_stego)


# -------------------------------------------------------------------------
# Unit Tests: Embed & Extract Roundtrips
# -------------------------------------------------------------------------

def test_ai_stego_embed_extract_text_roundtrip():
    cover = _create_synthetic_test_image(64, 64)
    message = "Confidential B.Tech AI Steganography Project 2026! 🔒"
    payload = message.encode("utf-8")

    stego, meta = AiAdaptiveLSB.embed(cover, payload, block_size=16)
    assert meta["payload_bytes"] == len(payload)
    assert meta["altered_pixels"] > 0
    assert meta["bpp"] > 0

    extracted_bytes, ext_meta = AiAdaptiveLSB.extract(stego, block_size=16)
    assert ext_meta["crc_verified"] is True
    assert extracted_bytes == payload
    assert extracted_bytes.decode("utf-8") == message


def test_ai_stego_embed_extract_binary_roundtrip():
    cover = _create_synthetic_test_image(64, 64)
    rng = np.random.RandomState(99)
    binary_payload = rng.bytes(80)

    stego, _ = AiAdaptiveLSB.embed(cover, binary_payload, block_size=16)
    extracted_bytes, ext_meta = AiAdaptiveLSB.extract(stego, block_size=16)

    assert ext_meta["crc_verified"] is True
    assert extracted_bytes == binary_payload


def test_ai_stego_capacity_exceeded_error():
    cover = _create_synthetic_test_image(32, 32)  # 4 blocks of 96 bytes = 384 bytes max
    oversized = b"X" * 1000
    with pytest.raises(CapacityExceededError):
        AiAdaptiveLSB.embed(cover, oversized, block_size=16)


def test_ai_stego_clean_image_raises_no_stego_payload():
    cover = _create_synthetic_test_image(64, 64)
    with pytest.raises(NoStegoPayloadFoundError):
        AiAdaptiveLSB.extract(cover, block_size=16)


def test_ai_stego_crc32_tamper_detection():
    cover = _create_synthetic_test_image(64, 64)
    payload = b"Critical data to protect against bit modification"
    stego, meta = AiAdaptiveLSB.embed(cover, payload, block_size=16)

    # Tamper with stego image in a block that was used for embedding
    ranked = AiAdaptiveLSB.rank_blocks_with_ai(cover, block_size=16)
    top_block = ranked[0]
    # Invert the LSB of a pixel inside the first embedded block
    y_target = top_block.y_start + 8
    x_target = top_block.x_start + 8
    stego[y_target, x_target, 0] ^= 1

    with pytest.raises((PayloadCorruptedError, NoStegoPayloadFoundError)):
        AiAdaptiveLSB.extract(stego, block_size=16)


def test_ai_stego_compare_all_methods():
    cover = _create_synthetic_test_image(64, 64)
    payload = b"3-way comparative benchmark evaluation payload"

    comp = AiAdaptiveLSB.compare_all_methods(cover, payload, block_size=16)
    assert "baseline_lsb" in comp
    assert "rule_adaptive_lsb" in comp
    assert "ai_adaptive_lsb" in comp
    assert "psnr_gain_vs_baseline_db" in comp
    assert "psnr_gain_vs_rule_db" in comp
    assert comp["baseline_lsb"]["psnr_db"] > 0
    assert comp["rule_adaptive_lsb"]["psnr_db"] > 0
    assert comp["ai_adaptive_lsb"]["psnr_db"] > 0


# -------------------------------------------------------------------------
# Integration Tests: FastAPI Endpoints
# -------------------------------------------------------------------------

@pytest.mark.anyio
async def test_api_ai_stego_capacity_endpoint():
    cover = _create_synthetic_test_image(64, 64)
    png_bytes = _png_bytes_from_array(cover)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("test.png", png_bytes, "image/png")}
        response = await client.post("/ai-stego/capacity", files=files, data={"block_size": "16"})

    assert response.status_code == 200
    data = response.json()
    assert data["total_blocks"] == 16
    assert data["max_payload_bytes"] > 0
    assert data["ai_usable_blocks"] >= 0


@pytest.mark.anyio
async def test_api_ai_stego_encode_and_decode_endpoint():
    cover = _create_synthetic_test_image(64, 64)
    png_bytes = _png_bytes_from_array(cover)
    secret_text = "FastAPI AI Steganography Full Lifecycle Test 🚀"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Encode
        files = {"image": ("test.png", png_bytes, "image/png")}
        encode_resp = await client.post(
            "/ai-stego/encode",
            files=files,
            data={"message": secret_text, "block_size": "16"},
        )
        assert encode_resp.status_code == 200
        assert encode_resp.headers["X-Stego-Method"] == "AI_Random_Forest_Adaptive_LSB"
        assert int(encode_resp.headers["X-Blocks-Utilized"]) >= 1
        assert float(encode_resp.headers["X-Metric-PSNR"]) > 30.0
        stego_png_bytes = encode_resp.content

        # 2. Decode
        decode_files = {"image": ("stego.png", stego_png_bytes, "image/png")}
        decode_resp = await client.post(
            "/ai-stego/decode",
            files=decode_files,
            data={"block_size": "16"},
        )
        assert decode_resp.status_code == 200
        decode_data = decode_resp.json()
        assert decode_data["crc_verified"] is True
        assert decode_data["payload_text"] == secret_text


@pytest.mark.anyio
async def test_api_ai_stego_compare_endpoint():
    cover = _create_synthetic_test_image(64, 64)
    png_bytes = _png_bytes_from_array(cover)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("test.png", png_bytes, "image/png")}
        response = await client.post(
            "/ai-stego/compare",
            files=files,
            data={"message": "Benchmark secret text across all 3 engines", "block_size": "16"},
        )

    assert response.status_code == 200
    comp_data = response.json()
    assert "baseline_lsb" in comp_data
    assert "rule_adaptive_lsb" in comp_data
    assert "ai_adaptive_lsb" in comp_data
    assert "psnr_gain_vs_baseline_db" in comp_data
