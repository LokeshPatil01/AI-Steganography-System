"""Tests for Image Quality Metrics module (Phase 9).

Validates MSE, PSNR, SSIM, BER, BPP, execution timers, CSV audit logs,
and the /metrics/compare and /metrics/history REST endpoints.
"""
import io
import math
import os
import tempfile
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.image.loader import ImageLoader
from app.image.metrics import (
    ExecutionTimer,
    MetricsDimensionMismatchError,
    compute_all_metrics,
    compute_bpp,
    compute_channel_mse,
    compute_image_lsb_ber,
    compute_mse,
    compute_payload_ber,
    compute_psnr,
    compute_ssim,
    evaluate_quality_rating,
    record_metrics_to_csv,
)
from app.main import app
from app.steganography.baseline_lsb import BaselineLSB


@pytest.fixture
def clean_cover_img():
    """Generates a synthetic 64x64 RGB gradient image."""
    h, w = 64, 64
    x = np.linspace(0, 255, w, dtype=np.uint8)
    y = np.linspace(0, 255, h, dtype=np.uint8)
    xx, yy = np.meshgrid(x, y)
    zz = ((xx.astype(int) + yy.astype(int)) // 2).astype(np.uint8)
    return np.stack([xx, yy, zz], axis=2)


@pytest.fixture
def clean_png_bytes(clean_cover_img):
    """Encodes clean cover image to lossless PNG bytes."""
    return ImageLoader.save_image_to_bytes(clean_cover_img)


class TestMetricsCalculations:
    """Unit tests for individual mathematical quality assessment metrics."""

    def test_validate_image_pair_mismatch(self, clean_cover_img):
        mismatched_img = np.zeros((32, 64, 3), dtype=np.uint8)
        with pytest.raises(MetricsDimensionMismatchError) as exc_info:
            compute_mse(clean_cover_img, mismatched_img)
        assert "Image dimension mismatch" in str(exc_info.value)

    def test_compute_mse_identical(self, clean_cover_img):
        mse = compute_mse(clean_cover_img, clean_cover_img)
        assert mse == 0.0

    def test_compute_mse_uniform_difference(self, clean_cover_img):
        modified = clean_cover_img.astype(np.float64) + 2.0
        modified = np.clip(modified, 0, 255).astype(np.uint8)
        mse = compute_mse(clean_cover_img, modified)
        # Difference of 2 on each pixel -> 2^2 = 4
        # Since not clipped at boundary, MSE should be very close to 4.0
        assert 3.8 <= mse <= 4.1

    def test_compute_channel_mse(self, clean_cover_img):
        modified = clean_cover_img.copy()
        modified[:, :, 0] = (modified[:, :, 0].astype(int) + 5).clip(0, 255).astype(np.uint8)
        channel_mse = compute_channel_mse(clean_cover_img, modified)
        assert "R" in channel_mse
        assert "G" in channel_mse
        assert "B" in channel_mse
        assert channel_mse["R"] > 20.0
        assert channel_mse["G"] == 0.0
        assert channel_mse["B"] == 0.0

    def test_compute_psnr_identical(self, clean_cover_img):
        psnr = compute_psnr(clean_cover_img, clean_cover_img)
        assert math.isinf(psnr)
        assert psnr > 0

    def test_compute_psnr_theoretical_value(self, clean_cover_img):
        # A uniform difference of 1 on each pixel produces MSE = 1.0
        # Theoretical PSNR = 10 * log10(255^2 / 1) = 20 * log10(255) = 48.130803... dB
        uniform_1 = np.clip(clean_cover_img.astype(int) + 1, 0, 255).astype(np.uint8)
        psnr = compute_psnr(clean_cover_img, uniform_1)
        assert 47.0 <= psnr <= 49.0

    def test_compute_ssim_identical(self, clean_cover_img):
        result = compute_ssim(clean_cover_img, clean_cover_img)
        assert "ssim_mean" in result
        assert "ssim_channels" in result
        assert pytest.approx(result["ssim_mean"], rel=1e-5) == 1.0
        for channel, val in result["ssim_channels"].items():
            assert pytest.approx(val, rel=1e-5) == 1.0

    def test_compute_ssim_subtle_vs_inverted(self, clean_cover_img):
        # Subtle modification: 1 LSB flip on small region
        subtle = clean_cover_img.copy()
        subtle[:8, :8, 0] ^= 1
        subtle_ssim = compute_ssim(clean_cover_img, subtle)["ssim_mean"]
        assert subtle_ssim > 0.9999

        # Inverted image: severe degradation compared to cover
        inverted = 255 - clean_cover_img
        inv_ssim = compute_ssim(clean_cover_img, inverted)["ssim_mean"]
        assert inv_ssim < 0.1  # Virtually zero structural correlation (severe degradation)

    def test_compute_payload_ber_exact_and_corrupt(self):
        msg = "Secret Research Data 2026"
        # Exact match
        assert compute_payload_ber(msg, msg) == 0.0

        # Inverted byte (8 bit errors in 1 byte of 1 byte payload)
        assert compute_payload_ber(bytes([0b00000000]), bytes([0b11111111])) == 1.0

        # Exactly 1 bit flipped out of 8 bits
        assert compute_payload_ber(bytes([0b00000000]), bytes([0b00000001])) == 0.125

        # Empty
        assert compute_payload_ber("", "") == 0.0

        # Length mismatch
        ber_mismatch = compute_payload_ber("AAAA", "AA")
        assert 0.0 < ber_mismatch <= 1.0

    def test_compute_image_lsb_ber(self, clean_cover_img):
        # Identical
        assert compute_image_lsb_ber(clean_cover_img, clean_cover_img) == 0.0

        # Invert all LSBs
        inverted_lsb = clean_cover_img ^ 1
        assert compute_image_lsb_ber(clean_cover_img, inverted_lsb) == 1.0

    def test_compute_bpp(self):
        # 1024 bytes in 512x512 image: (1024 * 8) / (512 * 512) = 8192 / 262144 = 0.03125 bpp
        bpp = compute_bpp(1024, 512, 512)
        assert pytest.approx(bpp, rel=1e-5) == 0.03125

    def test_quality_rating_tiers(self):
        rating, imperceptible = evaluate_quality_rating(float("inf"), 1.0)
        assert rating == "EXCELLENT" and imperceptible is True

        rating, imperceptible = evaluate_quality_rating(52.0, 0.998)
        assert rating == "EXCELLENT" and imperceptible is True

        rating, imperceptible = evaluate_quality_rating(42.5, 0.985)
        assert rating == "GOOD" and imperceptible is True

        rating, imperceptible = evaluate_quality_rating(36.0, 0.955)
        assert rating == "ACCEPTABLE" and imperceptible is False

        rating, imperceptible = evaluate_quality_rating(25.0, 0.850)
        assert rating == "DEGRADED" and imperceptible is False

    def test_execution_timer(self):
        with ExecutionTimer() as timer:
            _ = sum(i ** 2 for i in range(10000))
        assert timer.elapsed_ms > 0.0


class TestReportAndLogging:
    """Tests for full report generation and CSV persistence."""

    def test_compute_all_metrics_report(self, clean_cover_img):
        modified = clean_cover_img.copy()
        modified[0, 0, 0] ^= 1  # 1 bit modification

        report = compute_all_metrics(
            cover_img=clean_cover_img,
            stego_img=modified,
            original_payload="test_payload",
            recovered_payload="test_payload",
            payload_bytes=12,
            latency_ms=1.45,
        )

        assert report.mse > 0
        assert report.psnr_db > 80.0
        assert report.ssim > 0.9999
        assert report.payload_ber == 0.0
        assert report.is_imperceptible is True
        assert report.quality_rating == "EXCELLENT"

        # Check JSON-serializable dict
        d = report.to_dict()
        assert isinstance(d["psnr_db"], float)
        assert d["is_psnr_infinite"] is False
        assert d["payload_ber"] == 0.0
        assert d["bpp"] > 0

    def test_record_metrics_to_csv(self, clean_cover_img):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, "test_metrics.csv")
            report = compute_all_metrics(clean_cover_img, clean_cover_img)
            logged_path = record_metrics_to_csv(report, output_path=csv_path, method_name="Unit_Test")

            assert os.path.exists(logged_path)
            with open(logged_path, "r", encoding="utf-8") as f:
                content = f.read()
                assert "timestamp,method,dimensions,mse,psnr_db,ssim" in content
                assert "Unit_Test" in content
                assert "EXCELLENT" in content


class TestApiQualityEndpoints:
    """Integration tests for FastAPI /metrics endpoints."""

    def test_api_metrics_compare_endpoint(self, clean_png_bytes):
        client = TestClient(app)

        # Upload cover image and identical image
        response = client.post(
            "/metrics/compare",
            files={
                "cover_image": ("cover.png", clean_png_bytes, "image/png"),
                "stego_image": ("stego.png", clean_png_bytes, "image/png"),
            },
            data={
                "original_payload": "TopSecretPassword123",
                "recovered_payload": "TopSecretPassword123",
                "record_experiment": "false",
                "method_name": "API_Test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["mse"] == 0.0
        assert data["is_psnr_infinite"] is True
        assert data["psnr_db"] == 100.0  # Capped benchmark value
        assert data["ssim"] == 1.0
        assert data["payload_ber"] == 0.0
        assert data["is_imperceptible"] is True
        assert data["quality_rating"] == "EXCELLENT"

    def test_api_metrics_history_endpoint(self):
        client = TestClient(app)
        response = client.get("/metrics/history")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_end_to_end_stego_lsb_pipeline_metrics(self, clean_cover_img, clean_png_bytes):
        """End-to-end test: Embed secret payload -> Extract -> Compare metrics."""
        client = TestClient(app)
        secret_text = "Adaptive Steganography Research 2026 - Final Year B.Tech"

        # 1. Encode payload via API
        enc_res = client.post(
            "/encode",
            files={"image": ("cover.png", clean_png_bytes, "image/png")},
            data={"message": secret_text},
        )
        assert enc_res.status_code == 200
        stego_png_bytes = enc_res.content

        # Verify custom quality headers returned by /encode
        assert "x-metric-psnr" in enc_res.headers
        assert "x-metric-ssim" in enc_res.headers
        assert "x-metric-mse" in enc_res.headers
        assert enc_res.headers["x-metric-imperceptible"] == "true"

        # 2. Decode payload via API
        dec_res = client.post(
            "/decode",
            files={"image": ("stego.png", stego_png_bytes, "image/png")},
        )
        assert dec_res.status_code == 200
        decoded_text = dec_res.json()["payload_text"]
        assert decoded_text == secret_text

        # 3. Compare Cover and Stego images via /metrics/compare
        metric_res = client.post(
            "/metrics/compare",
            files={
                "cover_image": ("cover.png", clean_png_bytes, "image/png"),
                "stego_image": ("stego.png", stego_png_bytes, "image/png"),
            },
            data={
                "original_payload": secret_text,
                "recovered_payload": decoded_text,
                "record_experiment": "true",
                "method_name": "Baseline_LSB_E2E",
            },
        )
        assert metric_res.status_code == 200
        metrics = metric_res.json()

        # Stego metrics validation
        assert metrics["psnr_db"] >= 50.0, f"Expected PSNR >= 50 dB, got {metrics['psnr_db']}"
        assert metrics["ssim"] >= 0.999, f"Expected SSIM >= 0.999, got {metrics['ssim']}"
        assert metrics["payload_ber"] == 0.0, f"Expected BER = 0.0, got {metrics['payload_ber']}"
        assert metrics["is_imperceptible"] is True
        assert metrics["quality_rating"] == "EXCELLENT"
