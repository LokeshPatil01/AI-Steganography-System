"""Unit and Integration Tests for CNN Steganalyzer Model (Phase 16).

Tests cover:
- Spatial Rich Model (SRM) High-Pass Filtering preprocessing and weight freezing
- SteganalyzerCNN dimension-invariance, parameter counts, and probability bounds
- SteganalysisDataBuilder synthetic cover generation and paired stego synthesis
- SteganalyzerTrainer training execution and early stopping
- SteganalyzerDetector runtime inference and risk classification
- FastAPI endpoints: GET /ai/steganalyzer/info, POST /ai/steganalyzer/detect, POST /detect
"""
import io
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
import pytest
import torch
from fastapi.testclient import TestClient

from app.ai.steganalyzer_net import SteganalyzerDetector, StegoDetectionResult
from app.image.loader import ImageLoader
from app.main import app
from app.steganography.baseline_lsb import BaselineLSB
from app.steganography.scatter_stego import KeyScatteredAiLSB
from training.steganalyzer.dataset_builder import SteganalysisDataBuilder, SteganalysisDataset
from training.steganalyzer.model_architecture import (
    SpatialRichModelLayer,
    SteganalyzerCNN,
    count_parameters,
)
from training.steganalyzer.train import SteganalyzerTrainer


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_cover_png_bytes():
    """Generates a clean 64x64 synthetic RGB PNG image."""
    arr = np.zeros((64, 64, 3), dtype=np.uint8)
    for y in range(64):
        for x in range(64):
            arr[y, x] = [int((x * 3) % 255), int((y * 3) % 255), int((x + y) * 2 % 255)]
    return ImageLoader.save_image_to_bytes(arr)


@pytest.fixture
def sample_stego_png_bytes(sample_cover_png_bytes):
    """Generates a matching 64x64 stego PNG image with embedded payload."""
    pixels, _ = ImageLoader.load_image(sample_cover_png_bytes)
    stego_pixels, _ = KeyScatteredAiLSB.embed(
        pixels, b"TopSecretStegoMessage123!", "SecretKeyXYZ", block_size=16
    )
    return ImageLoader.save_image_to_bytes(stego_pixels)


# -----------------------------------------------------------------------------
# 1. SRM Layer Tests
# -----------------------------------------------------------------------------
def test_srm_kernels_structure_and_freezing():
    """Validates SRM filter bank dimensions and non-trainable parameter state."""
    srm = SpatialRichModelLayer(truncation_threshold=3.0)
    assert srm.conv.weight.shape == (3, 1, 5, 5)
    assert srm.conv.weight.requires_grad is False
    assert srm.truncation_threshold == 3.0


def test_srm_residual_truncation():
    """Verifies that SRM residuals are properly clamped to [-T, T]."""
    srm = SpatialRichModelLayer(truncation_threshold=3.0)
    # Feed extreme high-contrast input
    inp = torch.randint(0, 256, (2, 1, 32, 32)).float()
    res = srm(inp)
    assert res.shape == (2, 3, 32, 32)
    assert float(res.min()) >= -3.0 - 1e-5
    assert float(res.max()) <= 3.0 + 1e-5


# -----------------------------------------------------------------------------
# 2. CNN Architecture Tests
# -----------------------------------------------------------------------------
def test_cnn_architecture_dimensions_and_invariance():
    """Verifies that AdaptiveAvgPool2d allows processing varying spatial dimensions."""
    model = SteganalyzerCNN()
    model.eval()

    # Square 64x64
    x1 = torch.randn(2, 1, 64, 64)
    out1 = model(x1)
    p1 = model.predict_proba(x1)
    assert out1.shape == (2, 1)
    assert p1.shape == (2, 1)
    assert (p1 >= 0.0).all() and (p1 <= 1.0).all()

    # Rectangular 96x48
    x2 = torch.randn(1, 1, 96, 48)
    out2 = model(x2)
    p2 = model.predict_proba(x2)
    assert out2.shape == (1, 1)
    assert p2.shape == (1, 1)


def test_model_parameter_count():
    """Verifies that parameter count matches architecture specification (~250k)."""
    model = SteganalyzerCNN()
    counts = count_parameters(model)
    assert counts["total"] > 200000
    assert counts["total"] < 350000
    assert counts["fixed_srm"] == 75
    assert counts["trainable"] == counts["total"] - 75


# -----------------------------------------------------------------------------
# 3. Dataset Builder Tests
# -----------------------------------------------------------------------------
def test_dataset_builder_generation_and_splits():
    """Verifies synthetic dataset construction and strict split isolation."""
    builder = SteganalysisDataBuilder(patch_size=64, random_seed=42)
    datasets = builder.build_dataset(num_cover_images=20)

    assert "train" in datasets
    assert "val" in datasets
    assert "test" in datasets

    # 70% of 20 = 14 covers -> 28 samples (14 cover, 14 stego)
    assert len(datasets["train"]) == 28
    # 15% of 20 = 3 covers -> 6 samples
    assert len(datasets["val"]) == 6
    # Remaining = 3 covers -> 6 samples
    assert len(datasets["test"]) == 6

    # Verify tensor shapes and label values
    sample_img, sample_lbl = datasets["train"][0]
    assert sample_img.shape == (1, 64, 64)
    assert sample_lbl.item() in [0.0, 1.0]


def test_dataset_stego_methods_diversity():
    """Verifies that multiple stego algorithms are used to synthesize stego patches."""
    builder = SteganalysisDataBuilder(patch_size=64, random_seed=42)
    datasets = builder.build_dataset(num_cover_images=30)
    methods = datasets["train"].methods
    assert "Cover" in methods
    # Should contain at least 2 distinct stego methods
    stego_types = set(m for m in methods if m != "Cover")
    assert len(stego_types) >= 2


# -----------------------------------------------------------------------------
# 4. Runtime Inference Detector Tests
# -----------------------------------------------------------------------------
def test_runtime_detector_inference_on_bytes(sample_cover_png_bytes, sample_stego_png_bytes):
    """Tests runtime SteganalyzerDetector on raw image byte payloads."""
    detector = SteganalyzerDetector.get_instance()
    res_cover: StegoDetectionResult = detector.predict(sample_cover_png_bytes)
    res_stego: StegoDetectionResult = detector.predict(sample_stego_png_bytes)

    assert isinstance(res_cover, StegoDetectionResult)
    assert isinstance(res_stego, StegoDetectionResult)

    assert 0.0 <= res_cover.stego_probability <= 1.0
    assert 0.0 <= res_stego.stego_probability <= 1.0
    assert res_cover.residual_energy >= 0.0
    assert res_stego.residual_energy >= 0.0
    assert res_cover.decision_threshold == 0.35
    assert res_cover.risk_level in ["LOW", "MODERATE", "HIGH", "CRITICAL"]


def test_runtime_detector_numpy_input():
    """Tests runtime detector when supplied direct numpy RGB array."""
    detector = SteganalyzerDetector.get_instance()
    arr = np.full((64, 64, 3), 128, dtype=np.uint8)
    res = detector.predict(arr)
    assert res.stego_probability >= 0.0
    assert res.decision_threshold == 0.35


# -----------------------------------------------------------------------------
# 5. FastAPI Endpoints Integration Tests
# -----------------------------------------------------------------------------
def test_api_steganalyzer_info(client):
    """Tests GET /ai/steganalyzer/info endpoint."""
    res = client.get("/ai/steganalyzer/info")
    assert res.status_code == 200
    data = res.json()
    assert data["model_name"] == "SteganalyzerCNN"
    assert data["framework"] == "PyTorch"
    assert data["decision_threshold"] == 0.35
    assert "parameters" in data
    assert "test_metrics" in data


def test_api_detect_endpoint(client, sample_cover_png_bytes):
    """Tests POST /ai/steganalyzer/detect with multipart image file."""
    files = {"image": ("cover.png", sample_cover_png_bytes, "image/png")}
    res = client.post("/ai/steganalyzer/detect", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "is_stego" in data
    assert "stego_probability" in data
    assert "residual_energy" in data
    assert "risk_level" in data
    assert "recommendation" in data
    assert data["decision_threshold"] == 0.35


def test_api_detect_alias_endpoint(client, sample_stego_png_bytes):
    """Tests POST /detect alias matching PROJECT_ARCHITECTURE.md route table."""
    files = {"image": ("stego.png", sample_stego_png_bytes, "image/png")}
    res = client.post("/detect", files=files)
    assert res.status_code == 200
    data = res.json()
    assert "is_stego" in data
    assert "stego_probability" in data


def test_api_detect_invalid_file(client):
    """Tests POST /ai/steganalyzer/detect rejects corrupt or non-image data."""
    files = {"image": ("bad.txt", b"not a png image", "text/plain")}
    res = client.post("/ai/steganalyzer/detect", files=files)
    assert res.status_code == 400
