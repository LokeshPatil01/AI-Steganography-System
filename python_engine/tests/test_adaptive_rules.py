"""Tests for Rule-Based Adaptive Steganography Engine (Phase 10).

Validates:
- Block partitioning and MSB-plane texture suitability calculation
- Invariant block ranking between cover and stego images
- Selective embedding (only textured blocks modified; smooth blocks preserved)
- Adaptive wire framing, extraction, and CRC-32 verification
- Capacity overflow guards and tamper detection
- Baseline LSB vs. Adaptive LSB empirical comparison
- FastAPI /adaptive REST endpoints
"""
import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.image.loader import ImageLoader
from app.main import app
from app.steganography.adaptive_rules import (
    AdaptivePayloadPacker,
    AdaptiveRulesLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
    PayloadCorruptedError,
)


@pytest.fixture
def dual_texture_cover_img():
    """Generates a 128x128 synthetic image:
    - Top half (rows 0-63): Smooth linear gradient (low texture, sensitive)
    - Bottom half (rows 64-127): High variance, high-frequency texture noise
    """
    img = np.zeros((128, 128, 3), dtype=np.uint8)
    # Smooth gradient top
    img[:64, :, :] = np.linspace(100, 160, 128, dtype=np.uint8).reshape(1, 128, 1)
    # High-texture bottom
    np.random.seed(42)
    img[64:, :, :] = np.random.randint(50, 200, (64, 128, 3), dtype=np.uint8)
    return img


@pytest.fixture
def dual_texture_png_bytes(dual_texture_cover_img):
    """Lossless PNG bytes of dual-texture test image."""
    return ImageLoader.save_image_to_bytes(dual_texture_cover_img)


class TestAdaptiveSuitabilityAndRanking:
    """Tests for block suitability evaluation and ranking determinism."""

    def test_calculate_block_suitability_texture_vs_smooth(self, dual_texture_cover_img):
        # 128x128 with block size 16 = 8x8 = 64 blocks
        blocks = AdaptiveRulesLSB.calculate_block_suitability(dual_texture_cover_img, block_size=16)
        assert len(blocks) == 64

        # Top 10 blocks must all come from the textured bottom half (by >= 4)
        top_10 = blocks[:10]
        for b in top_10:
            assert b.by >= 4, f"Expected textured block (by >= 4), got by={b.by}"

        # Bottom 10 blocks must all come from the smooth top half (by < 4)
        bottom_10 = blocks[-10:]
        for b in bottom_10:
            assert b.by < 4, f"Expected smooth block (by < 4), got by={b.by}"

    def test_msb_plane_invariance_ranking(self, dual_texture_cover_img):
        """CRITICAL: Tests that modifying the LSB plane (embedding) DOES NOT change the ranking."""
        cover_ranking = AdaptiveRulesLSB.calculate_block_suitability(dual_texture_cover_img, block_size=16)

        # Perturb LSB plane of entire image randomly (simulating steganography)
        np.random.seed(123)
        stego_pixels = dual_texture_cover_img.copy()
        stego_pixels ^= np.random.randint(0, 2, dual_texture_cover_img.shape, dtype=np.uint8)

        stego_ranking = AdaptiveRulesLSB.calculate_block_suitability(stego_pixels, block_size=16)

        # Verify that the sorted order of block indices is IDENTICAL
        cover_indices = [(b.by, b.bx) for b in cover_ranking]
        stego_indices = [(b.by, b.bx) for b in stego_ranking]
        assert cover_indices == stego_indices, "Block ranking shifted after LSB embedding!"

        # Verify exact suitability score matches
        for b_cov, b_steg in zip(cover_ranking, stego_ranking):
            assert pytest.approx(b_cov.score, rel=1e-5) == b_steg.score


class TestAdaptiveEmbeddingAndExtraction:
    """Tests for adaptive payload embedding and recovery."""

    def test_adaptive_capacity_calculation(self, dual_texture_cover_img):
        cap = AdaptiveRulesLSB.calculate_capacity(dual_texture_cover_img, block_size=16)
        assert cap["total_blocks"] == 64
        # 16x16x3 bits = 768 bits = 96 bytes per block
        assert cap["bytes_per_block"] == 96
        # Total bytes = 64 * 96 = 6144 bytes; overhead = 16 bytes
        assert cap["max_payload_bytes"] == 6144 - 16

    def test_adaptive_embed_and_extract_roundtrip(self, dual_texture_cover_img):
        secret_payload = b"ADAPTIVE_STEGANOGRAPHY_RESEARCH_2026_RULE_BASED_TEST"

        stego_pixels, meta = AdaptiveRulesLSB.embed(dual_texture_cover_img, secret_payload, block_size=16)
        assert meta["payload_bytes"] == len(secret_payload)
        assert meta["blocks_utilized"] > 0
        assert meta["blocks_preserved_smooth"] > 0

        # Extract
        recovered_bytes, ext_meta = AdaptiveRulesLSB.extract(stego_pixels, block_size=16)
        assert recovered_bytes == secret_payload
        assert ext_meta["crc_verified"] is True

    def test_adaptive_selective_embedding_preserves_smooth_blocks(self, dual_texture_cover_img):
        """Verifies that only textured blocks are modified, while smooth blocks remain untouched."""
        # Short message of 40 bytes: fits in 1 block (16 bytes header + 40 bytes = 56 bytes < 96 bytes)
        short_msg = b"Short payload for selective block test"

        stego_pixels, meta = AdaptiveRulesLSB.embed(dual_texture_cover_img, short_msg, block_size=16)
        assert meta["blocks_utilized"] == 1
        assert meta["blocks_preserved_smooth"] == 63

        # Check smooth top half (rows 0 to 63): MUST BE 100% UNCHANGED
        smooth_cover_top = dual_texture_cover_img[:64, :, :]
        smooth_stego_top = stego_pixels[:64, :, :]
        assert np.array_equal(smooth_cover_top, smooth_stego_top), "Smooth region was erroneously modified!"

    def test_adaptive_overflow_protection(self, dual_texture_cover_img):
        cap = AdaptiveRulesLSB.calculate_capacity(dual_texture_cover_img, block_size=16)
        oversized = b"X" * (cap["max_payload_bytes"] + 1)

        with pytest.raises(CapacityExceededError):
            AdaptiveRulesLSB.embed(dual_texture_cover_img, oversized, block_size=16)

    def test_adaptive_tampered_payload_crc32_error(self, dual_texture_cover_img):
        payload = b"Critical Secret Message 2026"
        stego_pixels, meta = AdaptiveRulesLSB.embed(dual_texture_cover_img, payload, block_size=16)

        # Retrieve the highest-ranked block where embedding begins
        ranked = AdaptiveRulesLSB.calculate_block_suitability(dual_texture_cover_img, block_size=16)
        top_block = ranked[0]

        # Tamper with a bit inside the active payload region of top_block
        stego_pixels[top_block.y_start, top_block.x_start + 1, 0] ^= 1

        with pytest.raises((PayloadCorruptedError, NoStegoPayloadFoundError)):
            AdaptiveRulesLSB.extract(stego_pixels, block_size=16)


class TestComparativeAnalysis:
    """Tests for empirical comparison between Baseline LSB and Adaptive LSB."""

    def test_compare_with_baseline(self, dual_texture_cover_img):
        payload = b"Empirical Benchmark Comparison: Baseline LSB vs Adaptive Rule-Based LSB"
        comparison = AdaptiveRulesLSB.compare_with_baseline(dual_texture_cover_img, payload, block_size=16)

        assert "baseline_lsb" in comparison
        assert "adaptive_lsb" in comparison
        assert comparison["payload_bytes"] == len(payload)

        base_metrics = comparison["baseline_lsb"]
        adap_metrics = comparison["adaptive_lsb"]

        # Both methods must deliver high fidelity (PSNR > 50 dB, SSIM > 0.999)
        assert base_metrics["psnr_db"] > 50.0
        assert adap_metrics["psnr_db"] > 50.0
        assert base_metrics["ssim"] > 0.999
        assert adap_metrics["ssim"] > 0.999

        # Adaptive LSB preserved smooth blocks
        assert adap_metrics["blocks_preserved_smooth"] > 50


class TestApiAdaptiveEndpoints:
    """Integration tests for /adaptive FastAPI endpoints."""

    def test_fastapi_adaptive_capacity_endpoint(self, dual_texture_png_bytes):
        client = TestClient(app)
        res = client.post(
            "/adaptive/capacity",
            files={"image": ("test.png", dual_texture_png_bytes, "image/png")},
            data={"block_size": "16"},
        )
        assert res.status_code == 200
        data = res.json()
        assert data["total_blocks"] == 64
        assert data["max_payload_bytes"] > 0

    def test_fastapi_adaptive_encode_and_decode_lifecycle(self, dual_texture_png_bytes):
        client = TestClient(app)
        secret_text = "FastAPI Adaptive Steganography Test Payload 2026"

        # 1. Encode
        enc_res = client.post(
            "/adaptive/encode",
            files={"image": ("cover.png", dual_texture_png_bytes, "image/png")},
            data={"message": secret_text, "block_size": "16"},
        )
        assert enc_res.status_code == 200
        assert enc_res.headers["x-stego-method"] == "Adaptive_Rule_Based_LSB"
        assert int(enc_res.headers["x-blocks-utilized"]) > 0
        assert int(enc_res.headers["x-blocks-preserved"]) > 0
        stego_png_bytes = enc_res.content

        # 2. Decode
        dec_res = client.post(
            "/adaptive/decode",
            files={"image": ("stego.png", stego_png_bytes, "image/png")},
            data={"block_size": "16"},
        )
        assert dec_res.status_code == 200
        dec_data = dec_res.json()
        assert dec_data["payload_text"] == secret_text
        assert dec_data["crc_verified"] is True
        assert dec_data["blocks_traversed"] > 0

    def test_fastapi_adaptive_compare_endpoint(self, dual_texture_png_bytes):
        client = TestClient(app)
        res = client.post(
            "/adaptive/compare",
            files={"image": ("cover.png", dual_texture_png_bytes, "image/png")},
            data={"message": "Side-by-side empirical test message", "block_size": "16"},
        )
        assert res.status_code == 200
        data = res.json()
        assert "baseline_lsb" in data
        assert "adaptive_lsb" in data
        assert "psnr_improvement_db" in data
        assert "ssim_difference" in data
