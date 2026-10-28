"""Unit and integration tests for AI Region Suitability Classifier & Endpoints (Phase 13)."""
import io
import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sklearn.ensemble import RandomForestClassifier

from app.ai.region_classifier import BlockClassification, ImageRegionAnalysisResult, RegionClassifier
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_png_bytes():
    """Generates an in-memory 64x64 PNG image combining smooth and textured areas."""
    img_arr = np.zeros((64, 64, 3), dtype=np.uint8)
    # Top half: Smooth solid blue
    img_arr[:32, :, :] = [30, 80, 180]
    # Bottom half: High contrast textured checkerboard
    check = np.indices((32, 64)).sum(axis=0) // 2 % 2
    img_arr[32:, :, :] = np.where(check[:, :, None] == 1, 240, 20).astype(np.uint8)

    buf = io.BytesIO()
    Image.fromarray(img_arr, mode="RGB").save(buf, format="PNG")
    return buf.getvalue()


def test_region_classifier_model_loading():
    model = RegionClassifier.get_model()
    assert isinstance(model, RandomForestClassifier)
    assert model.n_features_in_ == 8


def test_classify_single_smooth_block():
    smooth_block = np.full((16, 16, 3), 150, dtype=np.uint8)
    res = RegionClassifier.classify_block(smooth_block, block_x=0, block_y=0)

    assert isinstance(res, BlockClassification)
    assert res.predicted_class == 0
    assert res.class_name == "Smooth"
    assert res.probabilities["Smooth"] > 0.50
    assert res.suitability_score >= 0.0


def test_classify_single_texture_block():
    check = np.indices((16, 16)).sum(axis=0) // 2 % 2
    texture_block = np.repeat(np.where(check[:, :, None] == 1, 230, 20).astype(np.uint8), 3, axis=2)
    res = RegionClassifier.classify_block(texture_block, block_x=1, block_y=1)

    assert isinstance(res, BlockClassification)
    assert res.predicted_class == 2
    assert res.class_name == "HighTexture"
    assert res.probabilities["HighTexture"] > 0.50
    assert res.suitability_score > 1.0


def test_analyze_image_grid_and_ranking():
    # 64x64 image with 16x16 blocks = 4x4 = 16 blocks total
    img_arr = np.zeros((64, 64, 3), dtype=np.uint8)
    img_arr[:32, :, :] = [100, 100, 100]  # 8 smooth blocks
    check = np.indices((32, 64)).sum(axis=0) // 2 % 2
    img_arr[32:, :, :] = np.repeat(np.where(check[:, :, None] == 1, 240, 20).astype(np.uint8), 3, axis=2)

    res = RegionClassifier.analyze_image(img_arr, block_size=16)

    assert isinstance(res, ImageRegionAnalysisResult)
    assert res.total_blocks == 16
    assert res.grid_blocks_x == 4
    assert res.grid_blocks_y == 4
    assert res.smooth_blocks == 8
    assert res.high_texture_blocks == 8
    assert len(res.ranked_blocks) == 16

    # Verify ranking order: First block has higher or equal suitability than last block
    assert res.ranked_blocks[0]["suitability_score"] >= res.ranked_blocks[-1]["suitability_score"]
    assert res.recommended_capacity_bytes > 0


def test_generate_heatmap_overlay_shape():
    img_arr = np.full((64, 64, 3), 120, dtype=np.uint8)
    heatmap = RegionClassifier.generate_heatmap_overlay(img_arr, block_size=16, alpha=0.4)

    assert isinstance(heatmap, np.ndarray)
    assert heatmap.shape == (64, 64, 3)
    assert heatmap.dtype == np.uint8


def test_endpoint_ai_info(client):
    response = client.get("/ai/region/info")
    assert response.status_code == 200

    data = response.json()
    assert data["model_type"] == "RandomForestClassifier"
    assert data["status"] == "active_ready"
    assert data["feature_count"] == 8
    assert "entropy" in data["features"]
    assert data["training_accuracy"] >= 0.95


def test_endpoint_ai_analyze(client, test_png_bytes):
    files = {"image": ("test_cover.png", test_png_bytes, "image/png")}
    data = {"block_size": "16"}

    response = client.post("/ai/region/analyze", files=files, data=data)
    assert response.status_code == 200

    body = response.json()
    assert body["image_width"] == 64
    assert body["image_height"] == 64
    assert body["total_blocks"] == 16
    assert body["high_texture_blocks"] > 0
    assert body["smooth_blocks"] > 0
    assert len(body["top_recommended_blocks"]) > 0


def test_endpoint_ai_heatmap(client, test_png_bytes):
    files = {"image": ("test_cover.png", test_png_bytes, "image/png")}
    data = {"block_size": "16", "alpha": "0.40"}

    response = client.post("/ai/region/heatmap", files=files, data=data)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "x-total-blocks" in response.headers
    assert "x-high-texture-blocks" in response.headers
    assert "x-recommended-capacity-bytes" in response.headers

    # Validate that returned payload is a valid PNG
    img = Image.open(io.BytesIO(response.content))
    assert img.size == (64, 64)
    assert img.format == "PNG"


def test_health_check_includes_ai_classifier(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["components"]["ai_region_classifier"] == "available"
