import base64
import math
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.image.loader import ImageLoader, ImageValidationError
from app.image.metrics import (
    compute_mse,
    compute_psnr,
    compute_ssim,
    evaluate_quality_rating,
)
from app.steganography.baseline_lsb import (
    BaselineLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
)
from app.steganography.payload_packer import PayloadCorruptedError

router = APIRouter(prefix="", tags=["Steganography"])

class CapacityResponse(BaseModel):
    width: int
    height: int
    channels: int
    total_pixels: int
    total_bits_available: int
    header_overhead_bytes: int
    max_payload_bytes: int
    max_payload_kb: float

class DecodeResponse(BaseModel):
    payload_text: Optional[str] = None
    payload_base64: str
    payload_bytes: int
    crc_verified: bool

@router.post("/capacity", response_model=CapacityResponse)
async def get_capacity(image: UploadFile = File(...)):
    """Calculates the maximum steganographic payload capacity of an uploaded image."""
    image_bytes = await image.read()
    try:
        pixel_array, _ = ImageLoader.load_image(image_bytes)
        cap = BaselineLSB.calculate_capacity(pixel_array)
        return CapacityResponse(
            width=cap.width,
            height=cap.height,
            channels=cap.channels,
            total_pixels=cap.total_pixels,
            total_bits_available=cap.total_bits_available,
            header_overhead_bytes=cap.header_overhead_bytes,
            max_payload_bytes=cap.max_payload_bytes,
            max_payload_kb=cap.max_payload_kb,
        )
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/encode")
async def encode_message(
    image: UploadFile = File(...),
    message: str = Form(None),
    payload_file: Optional[UploadFile] = File(None),
):
    """Embeds a secret message or payload into a cover PNG image using baseline LSB."""
    if not message and not payload_file:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'message' (text) or 'payload_file' (binary) must be provided.",
        )

    # Resolve payload bytes
    if payload_file:
        payload_bytes = await payload_file.read()
    else:
        payload_bytes = message.encode("utf-8")

    cover_bytes = await image.read()

    try:
        cover_pixels, (w, h) = ImageLoader.load_image(cover_bytes)
        stego_pixels, meta = BaselineLSB.embed(cover_pixels, payload_bytes)
        stego_png_bytes = ImageLoader.save_image_to_bytes(stego_pixels)

        # Compute empirical quality metrics
        mse_val = compute_mse(cover_pixels, stego_pixels)
        psnr_val = compute_psnr(cover_pixels, stego_pixels)
        ssim_res = compute_ssim(cover_pixels, stego_pixels)
        mean_ssim = ssim_res["ssim_mean"]
        quality_rating, is_imperceptible = evaluate_quality_rating(psnr_val, mean_ssim)

        psnr_header = "Infinity" if math.isinf(psnr_val) else str(round(psnr_val, 2))

        # Return PNG binary stream with metadata headers
        headers = {
            "Content-Disposition": 'attachment; filename="stego_image.png"',
            "X-Payload-Bytes": str(meta["payload_bytes"]),
            "X-Capacity-Total-Bytes": str(meta["capacity_total_bytes"]),
            "X-Capacity-Used-Percent": str(meta["capacity_used_percent"]),
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

@router.post("/decode", response_model=DecodeResponse)
async def decode_message(image: UploadFile = File(...)):
    """Extracts an embedded payload from a stego PNG image."""
    stego_bytes = await image.read()

    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
        extracted_bytes, meta = BaselineLSB.extract(stego_pixels)

        # Attempt UTF-8 decoding if text
        text_content: Optional[str] = None
        try:
            text_content = extracted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text_content = None

        return DecodeResponse(
            payload_text=text_content,
            payload_base64=base64.b64encode(extracted_bytes).decode("ascii"),
            payload_bytes=len(extracted_bytes),
            crc_verified=meta.get("crc_verified", True),
        )

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except NoStegoPayloadFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except PayloadCorruptedError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
