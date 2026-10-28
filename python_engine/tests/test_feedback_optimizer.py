"""Unit and Integration Tests for Feedback Optimization Loop (Phase 17).

Tests cover:
- Feedback wire framing (b'STEGFDB1', iteration index, CRC-32 integrity)
- Multi-objective loss formulation and Pareto candidate evaluation
- Closed-loop optimization execution with Steganalyzer CNN evaluation
- Blind self-synchronizing payload extraction and wrong-key rejection
- FastAPI endpoints: POST /ai-stego/feedback/encode, /dryrun, and /decode
"""
import io
import json
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.ai.feedback_optimizer import (
    FeedbackOptimizationReport,
    FeedbackOptimizer,
    FeedbackPayloadPacker,
)
from app.image.loader import ImageLoader
from app.main import app
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_cover_png_bytes():
    """Generates a clean 64x64 synthetic RGB PNG image."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        for x in range(64):
            arr[y, x] = [int((x * 4) % 255), int((y * 4) % 255), int((x + y) * 3 % 255)]
    return ImageLoader.save_image_to_bytes(arr)


# -----------------------------------------------------------------------------
# 1. Framing and Objective Loss Tests
# -----------------------------------------------------------------------------
def test_feedback_wire_framing():
    """Verifies feedback binary frame packing and header parsing."""
    raw = b"SecretFeedbackData#42"
    packed = FeedbackPayloadPacker.pack(raw, opt_iteration=3, realloc_level=2)
    assert packed[:8] == b"STEGFDB1"
    assert len(packed) == FeedbackPayloadPacker.HEADER_SIZE_BYTES + len(raw)

    payload_len, crc, opt_iter, realloc_lvl = FeedbackPayloadPacker.unpack_header(packed)
    assert payload_len == len(raw)
    assert opt_iter == 3
    assert realloc_lvl == 2

    # Corrupt magic header should fail
    bad_frame = b"BADMAGIC" + packed[8:]
    with pytest.raises(NoStegoPayloadFoundError):
        FeedbackPayloadPacker.unpack_header(bad_frame)


def test_objective_loss_monotonicity():
    """Verifies that lower P(stego) and higher PSNR produce strictly lower loss J."""
    loss_high_detect = FeedbackOptimizer.calculate_objective_loss(
        p_stego=0.80, psnr_val=38.0, ssim_val=0.95, residual_energy=1.2
    )
    loss_low_detect = FeedbackOptimizer.calculate_objective_loss(
        p_stego=0.20, psnr_val=46.0, ssim_val=0.99, residual_energy=0.4
    )
    assert loss_low_detect < loss_high_detect


# -----------------------------------------------------------------------------
# 2. Optimization and Extraction Core Tests
# -----------------------------------------------------------------------------
def test_feedback_optimization_and_extraction(sample_cover_png_bytes):
    """Verifies end-to-end feedback optimization and blind extraction."""
    cover_pixels, _ = ImageLoader.load_image(sample_cover_png_bytes)
    payload = b"ResearchGradeFeedbackPayload2026!"
    key = "AdversarialKey#Omega"

    stego_pixels, report = FeedbackOptimizer.optimize(
        cover_pixels=cover_pixels,
        payload_bytes=payload,
        stego_key=key,
        block_size=16,
        threshold=0.35,
        max_iterations=3,
    )

    assert isinstance(report, FeedbackOptimizationReport)
    assert report.iterations_run >= 1
    assert report.iterations_run <= 3
    assert len(report.history) == report.iterations_run
    assert report.final_psnr >= 35.0
    assert report.final_ssim >= 0.90
    assert report.payload_bytes == len(payload)

    # Extract with correct key
    extracted, meta = FeedbackOptimizer.extract(stego_pixels, key, block_size=16)
    assert extracted == payload
    assert meta["crc_verified"] is True
    assert meta["blocks_traversed"] > 0


def test_feedback_extraction_wrong_key_fails(sample_cover_png_bytes):
    """Verifies that extraction fails when an invalid stego key is used."""
    cover_pixels, _ = ImageLoader.load_image(sample_cover_png_bytes)
    payload = b"TopSecretTestPayload"
    key = "CorrectKey123"

    stego_pixels, _ = FeedbackOptimizer.optimize(
        cover_pixels=cover_pixels,
        payload_bytes=payload,
        stego_key=key,
        block_size=16,
        max_iterations=2,
    )

    with pytest.raises((NoStegoPayloadFoundError, PayloadCorruptedError)):
        FeedbackOptimizer.extract(stego_pixels, "WrongKey456", block_size=16)


def test_feedback_capacity_exceeded(sample_cover_png_bytes):
    """Verifies that an oversized payload raises CapacityExceededError."""
    cover_pixels, _ = ImageLoader.load_image(sample_cover_png_bytes)
    oversized = b"X" * 100000  # Exceeds 64x64 capacity
    with pytest.raises(CapacityExceededError):
        FeedbackOptimizer.optimize(
            cover_pixels=cover_pixels,
            payload_bytes=oversized,
            stego_key="Key",
            block_size=16,
        )


# -----------------------------------------------------------------------------
# 3. FastAPI Route Integration Tests
# -----------------------------------------------------------------------------
def test_api_feedback_encode_and_decode(client, sample_cover_png_bytes):
    """Verifies full HTTP roundtrip: encode -> stego PNG -> decode -> verified."""
    secret = "IEEE-Feedback-Optimized-Secret-Message-2026"
    key = "PassphraseSecret99"

    # 1. Encode
    files = {"image": ("cover.png", sample_cover_png_bytes, "image/png")}
    data = {
        "message": secret,
        "stego_key": key,
        "block_size": "16",
        "threshold": "0.35",
        "max_iterations": "3",
    }
    res_encode = client.post("/ai-stego/feedback/encode", files=files, data=data)
    assert res_encode.status_code == 200
    assert res_encode.headers["content-type"] == "image/png"
    assert res_encode.headers["x-stego-method"] == "AI_Feedback_Optimized_LSB"
    assert "x-iterations-run" in res_encode.headers
    assert "x-metric-psnr" in res_encode.headers
    assert "x-metric-ssim" in res_encode.headers

    stego_png_bytes = res_encode.content

    # 2. Decode
    decode_files = {"image": ("stego.png", stego_png_bytes, "image/png")}
    decode_data = {"stego_key": key, "block_size": "16"}
    res_decode = client.post("/ai-stego/feedback/decode", files=decode_files, data=decode_data)
    assert res_decode.status_code == 200
    decoded_json = res_decode.json()
    assert decoded_json["payload_text"] == secret
    assert decoded_json["crc_verified"] is True
    assert decoded_json["blocks_traversed"] > 0


def test_api_feedback_dryrun(client, sample_cover_png_bytes):
    """Verifies POST /ai-stego/feedback/dryrun returns detailed trajectory report."""
    files = {"image": ("cover.png", sample_cover_png_bytes, "image/png")}
    data = {
        "message": "DryrunTestMessage",
        "stego_key": "DryrunKey",
        "block_size": "16",
        "threshold": "0.35",
        "max_iterations": "2",
    }
    res = client.post("/ai-stego/feedback/dryrun", files=files, data=data)
    assert res.status_code == 200
    report = res.json()
    assert "converged" in report
    assert "iterations_run" in report
    assert "initial_p_stego" in report
    assert "final_p_stego" in report
    assert "history" in report
    assert len(report["history"]) == report["iterations_run"]
    assert report["history"][0]["iteration"] == 1
