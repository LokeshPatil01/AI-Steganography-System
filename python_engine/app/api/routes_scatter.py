"""FastAPI endpoints for PRNG Key-Based Random Block Scatter Steganography (Phase 15).

Combines Random Forest AI region selection with cryptographic HKDF-SHA256 block scattering.
Requires the exact steganographic key to extract concealed payloads.
"""
import base64
import math
from typing import Any, Dict, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.crypto.scatter_prng import PrngKeyDeriver
from app.image.loader import ImageLoader, ImageValidationError
from app.image.metrics import compute_mse, compute_psnr, compute_ssim, evaluate_quality_rating
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError
from app.steganography.scatter_stego import KeyScatteredAiLSB

router = APIRouter(prefix="/scatter", tags=["PRNG Key-Scattered Steganography"])


class ScatterCapacityResponse(BaseModel):
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
    method: str


class ScatterDecodeResponse(BaseModel):
    payload_text: Optional[str] = None
    payload_base64: str
    payload_bytes: int
    crc_verified: bool
    crc32: str
    key_fingerprint: str
    blocks_traversed: int


class KeyVerificationResponse(BaseModel):
    valid_key: bool
    payload_bytes: Optional[int] = None
    key_fingerprint: str
    detail: str


@router.post("/capacity", response_model=ScatterCapacityResponse)
async def get_scatter_capacity(
    image: UploadFile = File(..., description="Cover PNG image"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Calculates maximum payload capacity for PRNG key-scattered AI steganography."""
    image_bytes = await image.read()
    try:
        pixel_array, _ = ImageLoader.load_image(image_bytes)
        cap = KeyScatteredAiLSB.calculate_capacity(pixel_array, block_size)
        return ScatterCapacityResponse(**cap)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/encode")
async def encode_scatter_message(
    image: UploadFile = File(..., description="Cover PNG image"),
    message: Optional[str] = Form(None, description="Secret message text"),
    payload_file: Optional[UploadFile] = File(None, description="Binary payload file"),
    stego_key: str = Form(..., description="Secret steganographic password/key used to seed PRNG scatter"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Embeds a secret payload into AI-selected image blocks in a pseudorandom order keyed by `stego_key`.

    Without `stego_key`, an adversary cannot determine which blocks contain data or the bit sequence.
    """
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
        cover_pixels, (w, h) = ImageLoader.load_image(cover_bytes)
        stego_pixels, meta = KeyScatteredAiLSB.embed(
            cover_pixels, payload_bytes, stego_key.strip(), block_size
        )
        stego_png_bytes = ImageLoader.save_image_to_bytes(stego_pixels)

        # Compute empirical quality metrics
        mse_val = compute_mse(cover_pixels, stego_pixels)
        psnr_val = compute_psnr(cover_pixels, stego_pixels)
        ssim_res = compute_ssim(cover_pixels, stego_pixels)
        mean_ssim = ssim_res["ssim_mean"]
        quality_rating, is_imperceptible = evaluate_quality_rating(psnr_val, mean_ssim)

        psnr_header = "Infinity" if math.isinf(psnr_val) else str(round(psnr_val, 2))

        headers = {
            "Content-Disposition": 'attachment; filename="stego_prng_scattered.png"',
            "X-Stego-Method": "Key_Scattered_AI_Adaptive_LSB",
            "X-Key-Fingerprint": meta["key_fingerprint"],
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


@router.post("/decode", response_model=ScatterDecodeResponse)
async def decode_scatter_message(
    image: UploadFile = File(..., description="Key-scattered Stego PNG image"),
    stego_key: str = Form(..., description="Secret steganographic password/key used during encoding"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Extracts an embedded payload from a key-scattered stego PNG using receiver's `stego_key`."""
    if not stego_key or not stego_key.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Steganographic key 'stego_key' cannot be empty.",
        )

    stego_bytes = await image.read()

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        extracted_bytes, meta = KeyScatteredAiLSB.extract(
            stego_pixels, stego_key.strip(), block_size
        )

        text_content: Optional[str] = None
        try:
            text_content = extracted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None

        return ScatterDecodeResponse(
            payload_text=text_content,
            payload_base64=base64.b64encode(extracted_bytes).decode("ascii"),
            payload_bytes=len(extracted_bytes),
            crc_verified=meta.get("crc_verified", True),
            crc32=meta.get("crc32", "0x00000000"),
            key_fingerprint=meta.get("key_fingerprint", "Unknown"),
            blocks_traversed=meta.get("blocks_traversed", 0),
        )

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NoStegoPayloadFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Extraction failed: Incorrect steganographic key or no valid payload found. ({str(e)})",
        )
    except PayloadCorruptedError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Integrity check failed: Incorrect key or corrupted bitstream. ({str(e)})",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/verify-key", response_model=KeyVerificationResponse)
async def verify_stego_key(
    image: UploadFile = File(..., description="Key-scattered Stego PNG image"),
    stego_key: str = Form(..., description="Candidate steganographic key to verify"),
    block_size: int = Form(16, description="Block partition dimension (default 16)"),
):
    """Verifies whether a candidate steganographic key correctly uncovers valid payload wire framing."""
    stego_bytes = await image.read()
    fingerprint = PrngKeyDeriver.compute_key_fingerprint(stego_key)

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        extracted_bytes, meta = KeyScatteredAiLSB.extract(
            stego_pixels, stego_key.strip(), block_size
        )
        return KeyVerificationResponse(
            valid_key=True,
            payload_bytes=len(extracted_bytes),
            key_fingerprint=fingerprint,
            detail="Key successfully authenticated: valid wire frame and CRC-32 verified.",
        )
    except (NoStegoPayloadFoundError, PayloadCorruptedError):
        return KeyVerificationResponse(
            valid_key=False,
            payload_bytes=None,
            key_fingerprint=fingerprint,
            detail="Invalid key: wire frame magic or CRC-32 integrity failed.",
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
