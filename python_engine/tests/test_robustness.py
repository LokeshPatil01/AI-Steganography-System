"""Automated Tests for Phase 19: Robustness & Noise Perturbation Profiling Suite."""
import io
import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.image.loader import ImageLoader
from app.image.perturbation import NoisePerturbationEngine
from app.main import app
from app.steganography.baseline_lsb import BaselineLSB
from app.steganography.robustness_profiler import RobustnessProfiler
from app.steganography.scatter_stego import KeyScatteredAiLSB


@pytest.fixture
def synthetic_image() -> np.ndarray:
    """Returns a deterministic 64x64 RGB image."""
    rng = np.random.default_rng(42)
    return rng.integers(30, 225, (64, 64, 3), dtype=np.uint8)


@pytest.fixture
def stego_scatter_pair(synthetic_image: np.ndarray):
    """Embeds a known payload into synthetic image using KeyScatteredAiLSB."""
    payload = b"CRITICAL_RESEARCH_PAYLOAD_FOR_NOISE_TESTING_2026"
    stego_key = "RobustTestKey#2026"
    stego_pixels, meta = KeyScatteredAiLSB.embed(
        cover_pixels=synthetic_image,
        payload=payload,
        stego_key=stego_key,
        block_size=16,
    )
    return synthetic_image, stego_pixels, payload, stego_key


class TestPerturbationEngine:
    """Unit tests for NoisePerturbationEngine."""

    def test_gaussian_noise_preserves_shape_and_bounds(self, synthetic_image: np.ndarray):
        noisy = NoisePerturbationEngine.add_gaussian_noise(synthetic_image, mean=0.0, std=3.0, seed=123)
        assert noisy.shape == synthetic_image.shape
        assert noisy.dtype == np.uint8
        assert np.all(noisy >= 0) and np.all(noisy <= 255)
        # Verify noise actually modified some pixels
        assert not np.array_equal(synthetic_image, noisy)

    def test_gaussian_noise_zero_std(self, synthetic_image: np.ndarray):
        noisy = NoisePerturbationEngine.add_gaussian_noise(synthetic_image, mean=0.0, std=0.0)
        assert np.array_equal(synthetic_image, noisy)

    def test_salt_and_pepper_noise_introduces_extremes(self, synthetic_image: np.ndarray):
        noisy = NoisePerturbationEngine.add_salt_and_pepper_noise(
            synthetic_image, density=0.05, salt_vs_pepper=0.5, seed=42
        )
        assert noisy.shape == synthetic_image.shape
        assert np.any(noisy == 255)
        assert np.any(noisy == 0)

    def test_jpeg_compression_simulation(self, synthetic_image: np.ndarray):
        jpeg_95 = NoisePerturbationEngine.simulate_jpeg_compression(synthetic_image, quality=95)
        jpeg_50 = NoisePerturbationEngine.simulate_jpeg_compression(synthetic_image, quality=50)
        assert jpeg_95.shape == synthetic_image.shape
        assert jpeg_50.shape == synthetic_image.shape
        # Lower quality should introduce higher distortion
        diff_95 = np.mean(np.abs(synthetic_image.astype(float) - jpeg_95.astype(float)))
        diff_50 = np.mean(np.abs(synthetic_image.astype(float) - jpeg_50.astype(float)))
        assert diff_50 >= diff_95

    def test_gaussian_blur(self, synthetic_image: np.ndarray):
        blurred = NoisePerturbationEngine.add_gaussian_blur(synthetic_image, kernel_size=3, sigma=1.0)
        assert blurred.shape == synthetic_image.shape
        assert blurred.dtype == np.uint8

    def test_speckle_noise(self, synthetic_image: np.ndarray):
        speckled = NoisePerturbationEngine.add_speckle_noise(synthetic_image, std=0.05, seed=42)
        assert speckled.shape == synthetic_image.shape
        assert not np.array_equal(synthetic_image, speckled)

    def test_difference_map_amplification(self, synthetic_image: np.ndarray):
        noisy = NoisePerturbationEngine.add_gaussian_noise(synthetic_image, std=1.0, seed=42)
        diff_1x = NoisePerturbationEngine.compute_difference_map(synthetic_image, noisy, amplification=1.0)
        diff_10x = NoisePerturbationEngine.compute_difference_map(synthetic_image, noisy, amplification=10.0)
        assert diff_1x.shape == synthetic_image.shape
        assert diff_10x.shape == synthetic_image.shape
        assert np.mean(diff_10x) >= np.mean(diff_1x)

    def test_difference_map_shape_mismatch_raises(self, synthetic_image: np.ndarray):
        smaller = synthetic_image[:32, :32]
        with pytest.raises(ValueError, match="Image shape mismatch"):
            NoisePerturbationEngine.compute_difference_map(synthetic_image, smaller)


class TestRobustnessProfiler:
    """Unit tests for RobustnessProfiler."""

    def test_compute_lsb_ber_identical(self, synthetic_image: np.ndarray):
        ber = RobustnessProfiler.compute_lsb_ber(synthetic_image, synthetic_image)
        assert ber == 0.0

    def test_compute_lsb_ber_flipped(self, synthetic_image: np.ndarray):
        flipped = synthetic_image ^ 1
        ber = RobustnessProfiler.compute_lsb_ber(synthetic_image, flipped)
        assert ber == 1.0

    def test_profile_intact_under_zero_noise(self, stego_scatter_pair):
        cover, stego, payload, stego_key = stego_scatter_pair
        _, report = RobustnessProfiler.profile_attack(
            stego_img=stego,
            attack_type="gaussian",
            attack_params={"std": 0.0},
            cover_img=cover,
            original_payload=payload,
            extraction_method="scatter",
            credentials={"stego_key": stego_key},
            block_size=16,
        )
        assert report.extraction_succeeded is True
        assert report.survival_status == "INTACT"
        assert report.tamper_detected is False
        assert report.payload_ber == 0.0
        assert report.lsb_ber == 0.0

    def test_profile_tamper_detection_under_heavy_noise(self, stego_scatter_pair):
        cover, stego, payload, stego_key = stego_scatter_pair
        _, report = RobustnessProfiler.profile_attack(
            stego_img=stego,
            attack_type="gaussian",
            attack_params={"std": 8.0, "seed": 42},
            cover_img=cover,
            original_payload=payload,
            extraction_method="scatter",
            credentials={"stego_key": stego_key},
            block_size=16,
        )
        assert report.extraction_succeeded is False
        assert report.tamper_detected is True
        assert report.survival_status in ("TAMPER_DETECTED", "CORRUPTED_CRC", "FATAL_DESYNC")
        assert report.lsb_ber > 0.05
        assert any(
            w in report.integrity_message.lower()
            for w in ("tamper", "crc", "synchronization", "desync", "failed", "unable")
        )

    def test_profile_sweep_gaussian(self, stego_scatter_pair):
        cover, stego, payload, stego_key = stego_scatter_pair
        sweep_data = RobustnessProfiler.run_sweep(
            stego_img=stego,
            attack_type="gaussian",
            intensities=[0.5, 2.0, 5.0],
            extraction_method="scatter",
            credentials={"stego_key": stego_key},
            block_size=16,
            original_payload=payload,
        )
        assert len(sweep_data) == 3
        # Degraded PSNR decreases and MSE increases monotonically with noise intensity
        assert sweep_data[0]["attack_intensity"] == 0.5
        assert sweep_data[1]["attack_intensity"] == 2.0
        assert sweep_data[2]["attack_intensity"] == 5.0
        assert sweep_data[0]["degraded_psnr_db"] > sweep_data[2]["degraded_psnr_db"]
        assert sweep_data[2]["degraded_mse"] > sweep_data[0]["degraded_mse"]


class TestFastAPIRobustnessRoutes:
    """Integration tests for FastAPI /robustness endpoints."""

    client = TestClient(app)

    def test_perturb_endpoint_returns_png_and_headers(self, synthetic_image: np.ndarray):
        png_bytes = ImageLoader.save_image_to_bytes(synthetic_image)
        response = self.client.post(
            "/robustness/perturb",
            files={"image": ("test.png", png_bytes, "image/png")},
            data={"attack_type": "gaussian", "std": 3.0},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["x-attack-type"] == "gaussian"
        assert float(response.headers["x-attack-intensity"]) == 3.0
        assert "x-degraded-psnr" in response.headers
        assert "x-lsb-ber" in response.headers

    def test_difference_map_endpoint(self, synthetic_image: np.ndarray):
        orig_bytes = ImageLoader.save_image_to_bytes(synthetic_image)
        noisy = NoisePerturbationEngine.add_gaussian_noise(synthetic_image, std=2.0, seed=1)
        noisy_bytes = ImageLoader.save_image_to_bytes(noisy)

        response = self.client.post(
            "/robustness/difference-map",
            files={
                "original_image": ("orig.png", orig_bytes, "image/png"),
                "perturbed_image": ("pert.png", noisy_bytes, "image/png"),
            },
            data={"amplification": 15.0},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    def test_profile_endpoint(self, stego_scatter_pair):
        cover, stego, payload, stego_key = stego_scatter_pair
        stego_bytes = ImageLoader.save_image_to_bytes(stego)
        cover_bytes = ImageLoader.save_image_to_bytes(cover)

        response = self.client.post(
            "/robustness/profile",
            files={
                "stego_image": ("stego.png", stego_bytes, "image/png"),
                "cover_image": ("cover.png", cover_bytes, "image/png"),
            },
            data={
                "attack_type": "jpeg",
                "quality": 85,
                "extraction_method": "scatter",
                "stego_key": stego_key,
                "block_size": 16,
                "original_payload": payload.decode("utf-8"),
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["attack_type"] == "jpeg"
        assert data["attack_intensity"] == 85.0
        assert "degraded_psnr_db" in data
        assert "degraded_ssim" in data
        assert "lsb_ber" in data
        assert "tamper_detected" in data
        assert "survival_status" in data

    def test_sweep_endpoint(self, stego_scatter_pair):
        cover, stego, payload, stego_key = stego_scatter_pair
        stego_bytes = ImageLoader.save_image_to_bytes(stego)

        response = self.client.post(
            "/robustness/sweep",
            files={"stego_image": ("stego.png", stego_bytes, "image/png")},
            data={
                "attack_type": "gaussian",
                "intensities": "0.5, 1.5, 3.0",
                "extraction_method": "scatter",
                "stego_key": stego_key,
                "block_size": 16,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["attack_type"] == "gaussian"
        assert data["points_count"] == 3
        assert len(data["sweep_results"]) == 3
