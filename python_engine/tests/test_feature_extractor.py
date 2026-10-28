"""Unit and API integration tests for spatial feature extraction and image analysis."""
import io
import numpy as np
from PIL import Image
import pytest
from httpx import ASGITransport, AsyncClient

from app.image.feature_extractor import FeatureExtractor
from app.main import app

def create_flat_image(size: int = 64, fill_value: int = 128) -> np.ndarray:
    """Creates a completely flat/smooth image."""
    return np.full((size, size, 3), fill_value, dtype=np.uint8)

def create_checkerboard_image(size: int = 64, square_size: int = 8) -> np.ndarray:
    """Creates a high-contrast checkerboard image with dense edges."""
    img = np.zeros((size, size, 3), dtype=np.uint8)
    for y in range(size):
        for x in range(size):
            if ((x // square_size) + (y // square_size)) % 2 == 0:
                img[y, x] = [255, 255, 255]
    return img

def create_random_noise_image(size: int = 64) -> np.ndarray:
    """Creates a high-entropy random noise image."""
    return np.random.randint(0, 256, (size, size, 3), dtype=np.uint8)

def numpy_to_png_bytes(arr: np.ndarray) -> bytes:
    """Converts a numpy array into PNG bytes."""
    img = Image.fromarray(arr, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def test_entropy_calculation_smooth_vs_noisy():
    flat_arr = create_flat_image(64, 128)[:, :, 0]
    noisy_arr = create_random_noise_image(64)[:, :, 0]

    flat_entropy = FeatureExtractor.compute_entropy(flat_arr)
    noisy_entropy = FeatureExtractor.compute_entropy(noisy_arr)

    assert flat_entropy == 0.0, "A constant uniform image must have 0 Shannon entropy"
    assert noisy_entropy > 7.0, f"Random noise must have high Shannon entropy (~8.0), got {noisy_entropy}"

def test_sobel_gradient_magnitude():
    flat_gray = create_flat_image(64)[:, :, 0]
    checker_gray = create_checkerboard_image(64)[:, :, 0]

    flat_grad, _ = FeatureExtractor.compute_sobel_gradient(flat_gray)
    checker_grad, checker_max = FeatureExtractor.compute_sobel_gradient(checker_gray)

    assert flat_grad == 0.0, "Flat image must have zero gradient"
    assert checker_grad > 50.0, f"Checkerboard image must have strong gradient, got {checker_grad}"
    assert checker_max > checker_grad

def test_canny_edge_density():
    flat_gray = create_flat_image(64)[:, :, 0]
    checker_gray = create_checkerboard_image(64)[:, :, 0]

    flat_edges = FeatureExtractor.compute_canny_edge_density(flat_gray)
    checker_edges = FeatureExtractor.compute_canny_edge_density(checker_gray)

    assert flat_edges == 0.0, "Flat image must have 0 edge density"
    assert checker_edges > 0.05, f"Checkerboard must have non-zero edge density, got {checker_edges}"

def test_laplacian_variance():
    flat_gray = create_flat_image(64)[:, :, 0]
    noisy_gray = create_random_noise_image(64)[:, :, 0]

    flat_lap = FeatureExtractor.compute_laplacian_variance(flat_gray)
    noisy_lap = FeatureExtractor.compute_laplacian_variance(noisy_gray)

    assert flat_lap == 0.0
    assert noisy_lap > 100.0, "Noisy high-texture image must have high Laplacian variance"

def test_analyze_image_block_partitioning():
    # 64x64 image with block_size=16 produces exactly 4x4=16 blocks
    checker = create_checkerboard_image(64)
    result = FeatureExtractor.analyze_image(checker, block_size=16)

    assert result.image_width == 64
    assert result.image_height == 64
    assert result.block_size == 16
    assert result.total_blocks_x == 4
    assert result.total_blocks_y == 4
    assert result.total_blocks == 16
    assert len(result.blocks) == 16

    # Verify block coordinates
    coords = [(b.block_x, b.block_y) for b in result.blocks]
    assert (0, 0) in coords
    assert (3, 3) in coords

    # Verify global features exist
    assert "entropy" in result.global_features
    assert "sobel_gradient_mean" in result.global_features
    assert "canny_edge_density" in result.global_features

    # Verify feature summary exists
    assert "mean_block_entropy" in result.feature_summary
    assert "mean_block_gradient" in result.feature_summary

# --- FastAPI /analyze Endpoint Tests ---

@pytest.mark.anyio
async def test_fastapi_analyze_endpoint():
    checker = create_checkerboard_image(64)
    png_bytes = numpy_to_png_bytes(checker)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("checker.png", png_bytes, "image/png")}
        data = {"block_size": "16"}
        response = await client.post("/analyze", files=files, data=data)

    assert response.status_code == 200
    res_data = response.json()

    assert res_data["image_width"] == 64
    assert res_data["image_height"] == 64
    assert res_data["block_size"] == 16
    assert res_data["total_blocks"] == 16
    assert len(res_data["blocks"]) == 16

    first_block = res_data["blocks"][0]
    assert "entropy" in first_block
    assert "sobel_gradient_mean" in first_block
    assert "canny_edge_density" in first_block
    assert "laplacian_variance" in first_block

@pytest.mark.anyio
async def test_fastapi_analyze_rejects_invalid_block_size():
    flat = create_flat_image(64)
    png_bytes = numpy_to_png_bytes(flat)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("flat.png", png_bytes, "image/png")}
        data = {"block_size": "15"}  # Invalid: not in [8, 16, 32, 64]
        response = await client.post("/analyze", files=files, data=data)

    assert response.status_code == 400
    assert "block_size must be one of" in response.json()["detail"]
