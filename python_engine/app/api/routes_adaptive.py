"""FastAPI endpoints for Rule-Based Content-Adaptive Steganography (Phase 10)."""
import base64
import math
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.image.loader import ImageLoader, ImageValidationError
from app.image.metrics import compute_mse, compute_psnr, compute_ssim, evaluate_quality_rating
from app.steganography.adaptive_rules import (
    AdaptivePayloadPacker,
    AdaptiveRulesLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
    PayloadCorruptedError,
)

router = APIRouter(prefix="/adaptive", tags=["Adaptive Steganography (Rule-Based)"])


class AdaptiveCapacityResponse(BaseModel):
    width: int
    height: int
    channels: int
    block_size: int
    total_blocks: int
    bits_per_block: int
    bytes_per_block: int
    header_overhead_bytes: int
    max_payload_bytes: int
    max_payload_kb: float


class AdaptiveDecodeResponse(BaseModel):
    payload_text: Optional[str] = None
    payload_base64: str
    payload_bytes: int
    crc_verified: bool
    blocks_traversed: int


class AdaptiveCompareResponse(BaseModel):
    payload_bytes: int
    baseline_lsb: Dict[str, Any]
    adaptive_lsb: Dict[str, Any]
    psnr_improvement_db: float
    ssim_difference: float


@router.post("/capacity", response_model=AdaptiveCapacityResponse)
async def get_adaptive_capacity(
    image: UploadFile = File(..., description="Cover PNG image"),
    block_size: int = Form(16, description="Spatial block partition dimension (default 16)"),
):
    """Calculates maximum payload capacity and block layout under adaptive embedding."""
    image_bytes = await image.read()
    try:
        pixel_array, _ = ImageLoader.load_image(image_bytes)
        cap = AdaptiveRulesLSB.calculate_capacity(pixel_array, block_size)
        return AdaptiveCapacityResponse(**cap)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/encode")
async def encode_adaptive_message(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret message text"),
    payload_file: Optional[UploadFile] = File(None, description="Binary payload file"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Embeds a secret message strictly into the highest-complexity image blocks (Adaptive LSB).

    Smooth, flat, low-entropy regions are preserved untouched to maximize imperceptibility.
    """
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'payload_file' (binary) must be provided.",
        )

    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await image.read()

    try:
        cover_pixels, (w, h) = ImageLoader.load_image(cover_bytes)
        stego_pixels, meta = AdaptiveRulesLSB.embed(cover_pixels, payload_bytes, block_size)
        stego_png_bytes = ImageLoader.save_image_to_bytes(stego_pixels)

        # Compute empirical quality metrics
        mse_val = compute_mse(cover_pixels, stego_pixels)
        psnr_val = compute_psnr(cover_pixels, stego_pixels)
        ssim_res = compute_ssim(cover_pixels, stego_pixels)
        mean_ssim = ssim_res["ssim_mean"]
        quality_rating, is_imperceptible = evaluate_quality_rating(psnr_val, mean_ssim)

        psnr_header = "Infinity" if math.isinf(psnr_val) else str(round(psnr_val, 2))

        headers = {
            "Content-Disposition": 'attachment; filename="stego_adaptive.png"',
            "X-Stego-Method": "Adaptive_Rule_Based_LSB",
            "X-Payload-Bytes": str(meta["payload_bytes"]),
            "X-Capacity-Total-Bytes": str(meta["capacity_total_bytes"]),
            "X-Capacity-Used-Percent": str(meta["capacity_used_percent"]),
            "X-Blocks-Utilized": str(meta["blocks_utilized"]),
            "X-Blocks-Preserved": str(meta["blocks_preserved_smooth"]),
            "X-Bits-Per-Pixel": str(meta["bpp"]),
            "X-Metric-MSE": str(round(mse_val, 6)),
            "X-Metric-PSNR": psnr_header,
            "X-Metric-SSIM": str(round(mean_ssim, 6)),
            "X-Metric-Rating": quality_rating,
            "X-Metric-Imperceptible": "true" if is_imperceptible else "false",
        }

        return Response(content=stego_png_bytes, media_type="image/png", headers=headers)

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CapacityExceededError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/decode", response_model=AdaptiveDecodeResponse)
async def decode_adaptive_message(
    image: UploadFile = File(..., description="Adaptive Stego PNG image"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Extracts an embedded payload from an adaptive stego PNG image with CRC-32 integrity check."""
    stego_bytes = await image.read()

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        extracted_bytes, meta = AdaptiveRulesLSB.extract(stego_pixels, block_size)

        text_content: Optional[str] = None
        try:
            text_content = extracted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None

        return AdaptiveDecodeResponse(
            payload_text=text_content,
            payload_base64=base64.b64encode(extracted_bytes).decode("ascii"),
            payload_bytes=len(extracted_bytes),
            crc_verified=meta.get("crc_verified", True),
            blocks_traversed=meta.get("blocks_traversed", 0),
        )

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NoStegoPayloadFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PayloadCorruptedError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/compare", response_model=AdaptiveCompareResponse)
async def compare_baseline_vs_adaptive(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: str = Form(..., description="Secret test message"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Executes a direct empirical comparison between Baseline Sequential LSB and Adaptive Rule-Based LSB
    on the exact same cover image and payload.
    """
    cover_bytes = await image.read()
    try:
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        payload_bytes = message.encode("utf-8")
        comparison = AdaptiveRulesLSB.compare_with_baseline(cover_pixels, payload_bytes, block_size)
        return AdaptiveCompareResponse(**comparison)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CapacityExceededError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
