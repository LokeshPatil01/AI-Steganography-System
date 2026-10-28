"""FastAPI Endpoints for Phase 18 One-Click End-to-End Orchestration Pipeline.

Exposes REST APIs to perform unified RSA-4096-OAEP + AES-256-GCM + RF Region + PRNG Scatter +
SRM-CNN Closed-Loop Feedback Steganography in a single atomic transaction.
"""
import math
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from app.image.loader import ImageLoader
from app.pipeline.orchestrator import StegoPipelineOrchestrator
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError

router = APIRouter(prefix="/pipeline", tags=["One-Click End-to-End Pipeline"])


class PipelineDryrunResponse(BaseModel):
    success: bool
    cover_sha256: str
    stego_sha256: str
    raw_payload_bytes: int
    hybrid_envelope_bytes: int
    security_level: str
    recipient_fingerprint: str
    converged: bool
    iterations_run: int
    initial_p_stego: float
    final_p_stego: float
    p_stego_reduction: float
    psnr_db: float
    ssim: float
    mse: float
    quality_rating: str
    is_imperceptible: bool
    execution_time_ms: int


class PipelineDecodeResponse(BaseModel):
    success: bool
    payload_text: Optional[str]
    payload_bytes: int
    authenticated: bool
    recipient_fingerprint: str
    stego_sha256: str
    opt_iteration: int
    realloc_level: int
    execution_time_ms: int


@router.post("/encode-hybrid", summary="One-Click Hybrid Encryption + Feedback Steganography (Returns PNG)")
async def encode_hybrid_pipeline(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret text message payload"),
    payload_file: Optional[UploadFile] = File(None, description="Secret binary payload file"),
    recipient_public_key: str = Form(..., description="Recipient RSA-4096 Public Key PEM"),
    stego_passphrase: Optional[str] = Form(None, description="Optional custom stego passphrase"),
    security_level: str = Form("Balanced", description="Security profile: 'Quality', 'Balanced', 'Security'"),
    block_size: int = Form(16, description="Block partition size (default 16)"),
):
    """Atomically executes RSA-4096-OAEP + AES-256-GCM + RF + PRNG + CNN feedback steganography."""
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'payload_file' (binary) must be provided.",
        )

    if not recipient_public_key or not recipient_public_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Recipient RSA public key 'recipient_public_key' cannot be empty.",
        )

    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await image.read()

    try:
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        result = StegoPipelineOrchestrator.encode_hybrid(
            cover_pixels=cover_pixels,
            payload_data=payload_bytes,
            recipient_public_key_pem=recipient_public_key.strip(),
            stego_passphrase=stego_passphrase,
            security_level=security_level,
            block_size=block_size,
        )
        stego_png_bytes = ImageLoader.save_image_to_bytes(result.stego_pixels)

        psnr_header = "Infinity" if math.isinf(result.psnr_db) else str(round(result.psnr_db, 2))

        headers = {
            "Content-Disposition": 'attachment; filename="stego_hybrid_orchestrated.png"',
            "X-Stego-Method": "One_Click_Hybrid_AI_Pipeline",
            "X-Cover-SHA256": result.cover_sha256,
            "X-Stego-SHA256": result.stego_sha256,
            "X-Payload-Bytes": str(result.raw_payload_bytes),
            "X-Envelope-Bytes": str(result.hybrid_envelope_bytes),
            "X-Security-Level": result.security_level,
            "X-Recipient-Fingerprint": result.recipient_fingerprint,
            "X-Optimization-Converged": "true" if result.converged else "false",
            "X-Iterations-Run": str(result.iterations_run),
            "X-Initial-P-Stego": str(result.initial_p_stego),
            "X-Final-P-Stego": str(result.final_p_stego),
            "X-P-Stego-Reduction": str(result.p_stego_reduction),
            "X-Metric-PSNR": psnr_header,
            "X-Metric-SSIM": str(round(result.ssim, 6)),
            "X-Metric-MSE": str(round(result.mse, 6)),
            "X-Metric-Rating": result.quality_rating,
            "X-Metric-Imperceptible": "true" if result.is_imperceptible else "false",
            "X-Execution-Time-Ms": str(result.execution_time_ms),
        }

        return Response(content=stego_png_bytes, media_type="image/png", headers=headers)

    except CapacityExceededError as ce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ce))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline encoding failed: {str(e)}",
        )


@router.post("/dryrun-hybrid", response_model=PipelineDryrunResponse, summary="Simulate One-Click Pipeline (Audit Report)")
async def dryrun_hybrid_pipeline(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret text message payload"),
    payload_file: Optional[UploadFile] = File(None, description="Secret binary payload file"),
    recipient_public_key: str = Form(..., description="Recipient RSA-4096 Public Key PEM"),
    stego_passphrase: Optional[str] = Form(None, description="Optional custom stego passphrase"),
    security_level: str = Form("Balanced", description="Security profile: 'Quality', 'Balanced', 'Security'"),
    block_size: int = Form(16, description="Block partition size (default 16)"),
):
    """Executes pipeline and returns comprehensive JSON audit metrics."""
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
        cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        result = StegoPipelineOrchestrator.encode_hybrid(
            cover_pixels=cover_pixels,
            payload_data=payload_bytes,
            recipient_public_key_pem=recipient_public_key.strip(),
            stego_passphrase=stego_passphrase,
            security_level=security_level,
            block_size=block_size,
        )

        return PipelineDryrunResponse(
            success=True,
            cover_sha256=result.cover_sha256,
            stego_sha256=result.stego_sha256,
            raw_payload_bytes=result.raw_payload_bytes,
            hybrid_envelope_bytes=result.hybrid_envelope_bytes,
            security_level=result.security_level,
            recipient_fingerprint=result.recipient_fingerprint,
            converged=result.converged,
            iterations_run=result.iterations_run,
            initial_p_stego=result.initial_p_stego,
            final_p_stego=result.final_p_stego,
            p_stego_reduction=result.p_stego_reduction,
            psnr_db=result.psnr_db,
            ssim=result.ssim,
            mse=result.mse,
            quality_rating=result.quality_rating,
            is_imperceptible=result.is_imperceptible,
            execution_time_ms=result.execution_time_ms,
        )
    except CapacityExceededError as ce:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ce))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Dryrun failed: {str(e)}",
        )


@router.post("/decode-hybrid", response_model=PipelineDecodeResponse, summary="One-Click Extraction & Decryption")
async def decode_hybrid_pipeline(
    image: UploadFile = File(..., description="Stego PNG image"),
    recipient_private_key: str = Form(..., description="Recipient RSA-4096 Private Key PEM"),
    stego_passphrase: Optional[str] = Form(None, description="Stego passphrase (optional if derived from key)"),
    private_key_passphrase: Optional[str] = Form(None, description="Private key passphrase if encrypted"),
    block_size: int = Form(16, description="Block partition size (default 16)"),
):
    """Extracts concealed envelope and decrypts payload with authenticated integrity verification."""
    stego_bytes = await image.read()

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        result = StegoPipelineOrchestrator.decode_hybrid(
            stego_pixels=stego_pixels,
            recipient_private_key_pem=recipient_private_key.strip(),
            stego_passphrase=stego_passphrase,
            private_key_passphrase=private_key_passphrase,
            block_size=block_size,
        )

        return PipelineDecodeResponse(
            success=True,
            payload_text=result.decrypted_text,
            payload_bytes=result.payload_size_bytes,
            authenticated=result.authenticated,
            recipient_fingerprint=result.recipient_fingerprint,
            stego_sha256=result.stego_sha256,
            opt_iteration=result.opt_iteration,
            realloc_level=result.realloc_level,
            execution_time_ms=result.execution_time_ms,
        )

    except (NoStegoPayloadFoundError, PayloadCorruptedError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payload extraction failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Decryption failed or invalid key: {str(e)}",
        )
