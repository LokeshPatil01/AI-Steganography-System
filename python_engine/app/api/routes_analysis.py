"""FastAPI endpoint for image spatial feature extraction and texture analysis."""
from typing import Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.image.feature_extractor import FeatureExtractor
from app.image.loader import ImageLoader, ImageValidationError

router = APIRouter(prefix="", tags=["Analysis"])

class BlockFeatureDto(BaseModel):
    block_x: int
    block_y: int
    width: int
    height: int
    entropy: float
    mean_intensity: float
    variance: float
    std_dev: float
    sobel_gradient_mean: float
    canny_edge_density: float
    color_variance: float
    laplacian_variance: float
    noise_residual_std: float

class AnalysisResponseDto(BaseModel):
    image_width: int
    image_height: int
    channels: int
    block_size: int
    total_blocks_x: int
    total_blocks_y: int
    total_blocks: int
    global_features: Dict[str, float]
    feature_summary: Dict[str, float]
    blocks: List[BlockFeatureDto]

@router.post("/analyze", response_model=AnalysisResponseDto)
async def analyze_image(
    image: UploadFile = File(...),
    block_size: int = Form(16),
):
    """Analyzes an image and computes spatial features (Shannon entropy, Sobel gradients,
    Canny edges, variance, texture) globally and across N x N blocks.
    """
    if block_size not in {8, 16, 32, 64}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="block_size must be one of [8, 16, 32, 64].",
        )

    image_bytes = await image.read()
    try:
        pixel_array, _ = ImageLoader.load_image(image_bytes)
        result = FeatureExtractor.analyze_image(pixel_array, block_size=block_size)
        return result.to_dict()

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image analysis failed: {e}",
        )
