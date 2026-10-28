"""FastAPI endpoints for AI-Selected Adaptive Steganography (Phase 14).

Utilizes Random Forest machine learning to dynamically embed confidential payloads
strictly into high-complexity image blocks, leaving smooth/flat regions untouched.
"""
import base64
import math
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.image.loader import ImageLoader, ImageValidationError
from app.image.metrics import compute_mse, compute_psnr, compute_ssim, evaluate_quality_rating
from app.steganography.ai_stego import (
    AiAdaptiveLSB,
    AiPayloadPacker,
    CapacityExceededError,
    NoStegoPayloadFoundError,
    PayloadCorruptedError,
)

router = APIRouter(prefix="/ai-stego", tags=["AI-Selected Adaptive Steganography"])


class AiCapacityResponse(BaseModel):
    width: int
    height: int
    channels: int
    block_size: int
    total_blocks: int
    bits_per_block: int
    bytes_per_block: int
    header_overhead_bytes: int
    total_capacity_bytes: int
    max_payload_bytes: int
    ai_usable_blocks: int
    ai_preserved_capacity_bytes: int
    high_texture_blocks: int
    medium_texture_blocks: int
    smooth_blocks: int


class AiDecodeResponse(BaseModel):
    payload_text: Optional[str] = None
    payload_base64: str
    payload_bytes: int
    crc_verified: bool
    crc32: str
    blocks_traversed: int


class AiCompareResponse(BaseModel):
    payload_bytes: int
    baseline_lsb: Dict[str, Any]
    rule_adaptive_lsb: Dict[str, Any]
    ai_adaptive_lsb: Dict[str, Any]
    psnr_gain_vs_baseline_db: float
    psnr_gain_vs_rule_db: float
    ssim_gain_vs_baseline: float


@router.post("/capacity", response_model=AiCapacityResponse)
async def get_ai_stego_capacity(
    image: UploadFile = File(..., description="Cover PNG image"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Calculates total capacity and AI-preserved capacity (smooth blocks preserved untouched)."""
    image_bytes = await image.read()
    try:
        pixel_array, _ = ImageLoader.load_image(image_bytes)
        cap = AiAdaptiveLSB.calculate_capacity(pixel_array, block_size)
        return AiCapacityResponse(**cap)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/encode")
async def encode_ai_message(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret message text"),
    payload_file: Optional[UploadFile] = File(None, description="Binary payload file"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Embeds a secret payload selectively into the highest AI-ranked image blocks.

    Smooth and flat regions are protected to maximize human imperceptibility and minimize steganalytic detectability.
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
        stego_pixels, meta = AiAdaptiveLSB.embed(cover_pixels, payload_bytes, block_size)
        stego_png_bytes = ImageLoader.save_image_to_bytes(stego_pixels)

        # Compute empirical quality metrics
        mse_val = compute_mse(cover_pixels, stego_pixels)
        psnr_val = compute_psnr(cover_pixels, stego_pixels)
        ssim_res = compute_ssim(cover_pixels, stego_pixels)
        mean_ssim = ssim_res["ssim_mean"]
        quality_rating, is_imperceptible = evaluate_quality_rating(psnr_val, mean_ssim)

        psnr_header = "Infinity" if math.isinf(psnr_val) else str(round(psnr_val, 2))

        headers = {
            "Content-Disposition": 'attachment; filename="stego_ai_adaptive.png"',
            "X-Stego-Method": "AI_Random_Forest_Adaptive_LSB",
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


@router.post("/decode", response_model=AiDecodeResponse)
async def decode_ai_message(
    image: UploadFile = File(..., description="AI-Adaptive Stego PNG image"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Extracts an embedded payload from an AI-Adaptive stego PNG with zero coordinate transmission overhead."""
    stego_bytes = await image.read()

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        extracted_bytes, meta = AiAdaptiveLSB.extract(stego_pixels, block_size)

        text_content: Optional[str] = None
        try:
            text_content = extracted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None

        return AiDecodeResponse(
            payload_text=text_content,
            payload_base64=base64.b64encode(extracted_bytes).decode("ascii"),
            payload_bytes=len(extracted_bytes),
            crc_verified=meta.get("crc_verified", True),
            crc32=meta.get("crc32", "0x00000000"),
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


@router.post("/compare", response_model=AiCompareResponse)
async def compare_all_three_methods(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: str = Form(..., description="Secret test message"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Executes a 3-way empirical benchmark comparing Baseline Sequential vs. Rule-Based vs. AI-Adaptive
    on the exact same cover image and payload.
    """
    cover_bytes = await image.read()
    try:
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        payload_bytes = message.encode("utf-8")
        comparison = AiAdaptiveLSB.compare_all_methods(cover_pixels, payload_bytes, block_size)
        return AiCompareResponse(**comparison)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CapacityExceededError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
