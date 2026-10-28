"""FastAPI Route for Feedback Optimization Loop (Phase 17).

Provides endpoints:
- POST /ai-stego/feedback/encode  : Runs closed-loop feedback optimization and downloads stego PNG.
- POST /ai-stego/feedback/decode  : Extracts secret payload from feedback-optimized stego PNG.
- POST /ai-stego/feedback/dryrun  : Executes optimization without binary stream, returning full JSON trajectory report.
"""
import base64
import math
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from app.ai.feedback_optimizer import (
    FeedbackOptimizationReport,
    FeedbackOptimizer,
    IterationHistory,
)
from app.image.loader import ImageLoader, ImageValidationError
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError

router = APIRouter(prefix="/ai-stego/feedback", tags=["Feedback-Driven Adaptive Steganography"])


class IterationStatDto(BaseModel):
    iteration: int
    p_stego: float
    is_detected: bool
    psnr: float
    ssim: float
    mse: float
    residual_energy: float
    objective_loss: float
    action_taken: str
    textured_blocks_used: int
    candidate_pool_size: int


class FeedbackOptimizationReportDto(BaseModel):
    converged: bool
    iterations_run: int
    initial_p_stego: float
    final_p_stego: float
    p_stego_reduction: float
    initial_psnr: float
    final_psnr: float
    psnr_improvement: float
    final_ssim: float
    final_mse: float
    decision_threshold: float
    quality_rating: str
    is_imperceptible: bool
    best_iteration_selected: int
    key_fingerprint: str
    payload_bytes: int
    duration_seconds: float
    history: List[IterationStatDto]


class FeedbackDecodeResponse(BaseModel):
    payload_text: Optional[str]
    payload_base64: str
    payload_bytes: int
    crc_verified: bool
    crc32: str
    opt_iteration: int
    realloc_level: int
    blocks_traversed: int
    key_fingerprint: str


@router.post("/encode")
async def encode_feedback_stego(
    image: UploadFile = File(..., description="Clean cover PNG image"),
    message: Optional[str] = Form(None, description="Confidential text message"),
    payload_file: Optional[UploadFile] = File(None, description="Optional binary payload file"),
    stego_key: str = Form(..., description="Secret steganographic key / passphrase"),
    block_size: int = Form(16, description="Block partition size (default 16)"),
    threshold: float = Form(0.35, description="Stego detection threshold cutoff tau"),
    max_iterations: int = Form(5, description="Maximum feedback iterations k_max"),
):
    """Executes closed-loop adversarial feedback optimization and returns lossless stego PNG."""
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'payload_file' (binary) must be provided.",
        )

    if not stego_key or not stego_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Steganographic key 'stego_key' cannot be empty.",
        )

    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await image.read()

    try:
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        stego_pixels, report = FeedbackOptimizer.optimize(
            cover_pixels=cover_pixels,
            payload_bytes=payload_bytes,
            stego_key=stego_key.strip(),
            block_size=block_size,
            threshold=threshold,
            max_iterations=max_iterations,
        )
        stego_png_bytes = ImageLoader.save_image_to_bytes(stego_pixels)

        psnr_header = "Infinity" if math.isinf(report.final_psnr) else str(round(report.final_psnr, 2))

        headers = {
            "Content-Disposition": 'attachment; filename="stego_feedback_optimized.png"',
            "X-Stego-Method": "AI_Feedback_Optimized_LSB",
            "X-Optimization-Converged": "true" if report.converged else "false",
            "X-Iterations-Run": str(report.iterations_run),
            "X-Initial-P-Stego": str(report.initial_p_stego),
            "X-Final-P-Stego": str(report.final_p_stego),
            "X-P-Stego-Reduction": str(report.p_stego_reduction),
            "X-Metric-PSNR": psnr_header,
            "X-Metric-SSIM": str(round(report.final_ssim, 6)),
            "X-Metric-MSE": str(round(report.final_mse, 6)),
            "X-Metric-Rating": report.quality_rating,
            "X-Metric-Imperceptible": "true" if report.is_imperceptible else "false",
            "X-Key-Fingerprint": report.key_fingerprint,
            "X-Payload-Bytes": str(report.payload_bytes),
            "X-Best-Iteration": str(report.best_iteration_selected),
        }

        return Response(content=stego_png_bytes, media_type="image/png", headers=headers)

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CapacityExceededError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/dryrun", response_model=FeedbackOptimizationReportDto)
async def dryrun_feedback_stego(
    image: UploadFile = File(..., description="Clean cover PNG image"),
    message: Optional[str] = Form(None, description="Confidential text message"),
    payload_file: Optional[UploadFile] = File(None, description="Optional binary payload file"),
    stego_key: str = Form(..., description="Secret steganographic key / passphrase"),
    block_size: int = Form(16, description="Block partition size (default 16)"),
    threshold: float = Form(0.35, description="Stego detection threshold cutoff tau"),
    max_iterations: int = Form(5, description="Maximum feedback iterations k_max"),
):
    """Executes optimization loop and returns full trajectory report without binary payload."""
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' or 'payload_file' must be provided.",
        )

    if not stego_key or not stego_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Steganographic key cannot be empty.",
        )

    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await image.read()

    try:
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        _, report = FeedbackOptimizer.optimize(
            cover_pixels=cover_pixels,
            payload_bytes=payload_bytes,
            stego_key=stego_key.strip(),
            block_size=block_size,
            threshold=threshold,
            max_iterations=max_iterations,
        )
        return report.to_dict()

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except CapacityExceededError as e:
        raise HTTPException(status_code=413, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/decode", response_model=FeedbackDecodeResponse)
async def decode_feedback_stego(
    image: UploadFile = File(..., description="Feedback-optimized stego PNG image"),
    stego_key: str = Form(..., description="Secret steganographic key used during encoding"),
    block_size: int = Form(16, description="Block partition size (default 16)"),
):
    """Extracts confidential payload from feedback-optimized stego PNG with blind self-synchronization."""
    if not stego_key or not stego_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Steganographic key cannot be empty.",
        )

    stego_bytes = await image.read()

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        extracted_bytes, meta = FeedbackOptimizer.extract(
            stego_pixels=stego_pixels,
            stego_key=stego_key.strip(),
            block_size=block_size,
        )

        text_content: Optional[str] = None
        try:
            text_content = extracted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None

        return FeedbackDecodeResponse(
            payload_text=text_content,
            payload_base64=base64.b64encode(extracted_bytes).decode("ascii"),
            payload_bytes=len(extracted_bytes),
            crc_verified=meta.get("crc_verified", True),
            crc32=meta.get("crc32", "0x00000000"),
            opt_iteration=meta.get("opt_iteration", 1),
            realloc_level=meta.get("realloc_level", 0),
            blocks_traversed=meta.get("blocks_traversed", 0),
            key_fingerprint=meta.get("key_fingerprint", "Unknown"),
        )

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NoStegoPayloadFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction failed: Incorrect key or no feedback payload found. ({str(e)})",
        )
    except PayloadCorruptedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Integrity check failed: Incorrect key or bitstream corrupted. ({str(e)})",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
