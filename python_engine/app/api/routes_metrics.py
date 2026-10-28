"""FastAPI routes for Image Quality Assessment, PSNR/SSIM Metrics, and Experiment Audits."""
import csv
import os
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel

from app.image.loader import ImageLoader, ImageValidationError
from app.image.metrics import (
    MetricsDimensionMismatchError,
    compute_all_metrics,
    record_metrics_to_csv,
)

router = APIRouter(prefix="/metrics", tags=["Quality Metrics"])


class ChannelMetrics(BaseModel):
    R: Optional[float] = None
    G: Optional[float] = None
    B: Optional[float] = None
    Grayscale: Optional[float] = None


class CompareMetricsResponse(BaseModel):
    mse: float
    mse_channels: Dict[str, float]
    psnr_db: float
    is_psnr_infinite: bool
    psnr_display: str
    ssim: float
    ssim_channels: Dict[str, float]
    image_lsb_ber: float
    payload_ber: Optional[float] = None
    payload_bytes: Optional[int] = None
    bpp: Optional[float] = None
    latency_ms: Optional[float] = None
    is_imperceptible: bool
    quality_rating: str
    width: int
    height: int
    channels: int
    timestamp: str


@router.post("/compare", response_model=CompareMetricsResponse)
async def compare_images(
    cover_image: UploadFile = File(..., description="Original reference cover image PNG"),
    stego_image: UploadFile = File(..., description="Stego image PNG to compare"),
    original_payload: Optional[str] = Form(None, description="Original secret message plaintext"),
    recovered_payload: Optional[str] = Form(None, description="Recovered message plaintext"),
    record_experiment: bool = Form(True, description="Whether to append this run to results/tables/quality_metrics.csv"),
    method_name: str = Form("Baseline_LSB", description="Steganographic embedding method tag"),
):
    """Compares Cover and Stego images across full-reference objective quality metrics:
    MSE, PSNR, SSIM (Wang et al.), LSB bit error rate, and payload BER.
    """
    cover_bytes = await cover_image.read()
    stego_bytes = await stego_image.read()

    try:
        cover_pixels, (w1, h1) = ImageLoader.load_image(cover_bytes)
    except ImageValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid cover image: {e}",
        )

    try:
        stego_pixels, (w2, h2) = ImageLoader.load_image(stego_bytes)
    except ImageValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid stego image: {e}",
        )

    try:
        payload_bytes_len = len(original_payload.encode("utf-8")) if original_payload else None

        report = compute_all_metrics(
            cover_img=cover_pixels,
            stego_img=stego_pixels,
            original_payload=original_payload,
            recovered_payload=recovered_payload,
            payload_bytes=payload_bytes_len,
        )

        if record_experiment:
            csv_target = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "results",
                "tables",
                "quality_metrics.csv",
            )
            record_metrics_to_csv(report, output_path=csv_target, method_name=method_name)

        return CompareMetricsResponse(**report.to_dict())

    except MetricsDimensionMismatchError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Metric calculation failed: {e}",
        )


@router.get("/history", response_model=List[Dict[str, Any]])
def get_metrics_history(limit: int = 50):
    """Retrieves recent experimental quality benchmarks from the persisted CSV table."""
    csv_target = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "results",
        "tables",
        "quality_metrics.csv",
    )

    if not os.path.exists(csv_target):
        return []

    records: List[Dict[str, Any]] = []
    try:
        with open(csv_target, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                records.append(row)
        # Return most recent first up to limit
        return list(reversed(records))[:limit]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read experiment history: {e}",
        )
