"""FastAPI routes for Robustness & Noise Perturbation Profiling (Phase 19)."""
import json
import math
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, File, Form, HTTPException, Response, UploadFile, status
from pydantic import BaseModel

from app.image.loader import ImageLoader, ImageValidationError
from app.image.perturbation import NoisePerturbationEngine
from app.steganography.robustness_profiler import RobustnessProfiler, RobustnessReport

router = APIRouter(prefix="/robustness", tags=["Robustness & Channel Perturbation"])


class RobustnessProfileResponse(BaseModel):
    attack_type: str
    attack_params: Dict[str, Any]
    attack_intensity: float
    degraded_psnr_db: float
    degraded_ssim: float
    degraded_mse: float
    cover_psnr_db: Optional[float] = None
    cover_ssim: Optional[float] = None
    lsb_ber: float
    quality_rating: str
    is_imperceptible: bool
    extraction_attempted: bool
    extraction_succeeded: bool
    survival_status: str
    tamper_detected: bool
    integrity_message: str
    recovered_payload_size: int
    payload_ber: Optional[float] = None
    execution_time_ms: int


class SweepResponse(BaseModel):
    attack_type: str
    points_count: int
    sweep_results: List[RobustnessProfileResponse]


@router.post("/perturb")
async def perturb_image(
    image: UploadFile = File(..., description="Stego PNG image to perturb"),
    attack_type: str = Form("gaussian", description="Attack type: gaussian, salt_pepper, jpeg, blur, speckle"),
    std: float = Form(2.0, description="Noise std dev for gaussian/speckle attacks"),
    mean: float = Form(0.0, description="Mean for gaussian noise"),
    density: float = Form(0.01, description="Density for salt & pepper noise"),
    salt_vs_pepper: float = Form(0.5, description="Salt vs pepper ratio"),
    quality: int = Form(85, description="JPEG compression quality (1-100)"),
    kernel_size: int = Form(3, description="Kernel size for blur attack"),
    sigma: float = Form(1.0, description="Sigma for blur attack"),
    seed: Optional[int] = Form(None, description="Random seed"),
):
    """Applies a channel noise or compression perturbation attack and returns the perturbed PNG."""
    image_bytes = await image.read()
    try:
        pixels, (w, h) = ImageLoader.load_image(image_bytes)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    params: Dict[str, Any] = {
        "std": std,
        "mean": mean,
        "density": density,
        "salt_vs_pepper": salt_vs_pepper,
        "quality": quality,
        "kernel_size": kernel_size,
        "sigma": sigma,
        "seed": seed,
    }

    try:
        perturbed_pixels, report = RobustnessProfiler.profile_attack(
            stego_img=pixels,
            attack_type=attack_type,
            attack_params=params,
            extraction_method=None,
        )

        perturbed_png_bytes = ImageLoader.save_image_to_bytes(perturbed_pixels)

        psnr_header = "Infinity" if math.isinf(report.degraded_psnr_db) else str(report.degraded_psnr_db)

        headers = {
            "Content-Disposition": f'attachment; filename="perturbed_{attack_type}.png"',
            "X-Attack-Type": str(report.attack_type),
            "X-Attack-Intensity": str(report.attack_intensity),
            "X-Degraded-PSNR": psnr_header,
            "X-Degraded-SSIM": str(report.degraded_ssim),
            "X-Degraded-MSE": str(report.degraded_mse),
            "X-LSB-BER": str(report.lsb_ber),
            "X-Quality-Rating": report.quality_rating,
        }

        return Response(content=perturbed_png_bytes, media_type="image/png", headers=headers)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/difference-map")
async def get_difference_map(
    original_image: UploadFile = File(..., description="Original image PNG"),
    perturbed_image: UploadFile = File(..., description="Perturbed image PNG"),
    amplification: float = Form(10.0, description="Residual amplification multiplier (e.g. 5x to 20x)"),
):
    """Generates an amplified absolute difference heatmap PNG showing exact residual noise."""
    orig_bytes = await original_image.read()
    pert_bytes = await perturbed_image.read()

    try:
        orig_pixels, _ = ImageLoader.load_image(orig_bytes)
        pert_pixels, _ = ImageLoader.load_image(pert_bytes)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    try:
        diff_pixels = NoisePerturbationEngine.compute_difference_map(
            orig_image=orig_pixels,
            perturbed_image=pert_pixels,
            amplification=amplification,
        )
        diff_png_bytes = ImageLoader.save_image_to_bytes(diff_pixels)
        return Response(
            content=diff_png_bytes,
            media_type="image/png",
            headers={"Content-Disposition": 'attachment; filename="difference_heatmap.png"'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/profile", response_model=RobustnessProfileResponse)
async def profile_robustness(
    stego_image: UploadFile = File(..., description="Stego PNG image to test"),
    cover_image: Optional[UploadFile] = File(None, description="Optional original cover image for reference"),
    attack_type: str = Form("gaussian", description="Attack type: gaussian, salt_pepper, jpeg, blur, speckle"),
    std: float = Form(2.0, description="Gaussian/speckle std dev"),
    mean: float = Form(0.0, description="Gaussian mean"),
    density: float = Form(0.01, description="Salt & Pepper density"),
    salt_vs_pepper: float = Form(0.5, description="Salt vs pepper balance"),
    quality: int = Form(85, description="JPEG Quality (1-100)"),
    kernel_size: int = Form(3, description="Blur kernel size"),
    sigma: float = Form(1.0, description="Blur sigma"),
    seed: Optional[int] = Form(None, description="Random seed"),
    extraction_method: str = Form("scatter", description="Extraction strategy: scatter, ai_adaptive, adaptive, baseline, pipeline_hybrid, none"),
    stego_key: Optional[str] = Form("", description="Steganographic key passphrase"),
    recipient_private_key_pem: Optional[str] = Form("", description="Recipient RSA private key for hybrid pipeline"),
    block_size: int = Form(16, description="Block partition size"),
    original_payload: Optional[str] = Form(None, description="Original secret message for payload BER calculation"),
):
    """Executes a forensic channel attack, measures visual & LSB fidelity, and tests tamper detection."""
    stego_bytes = await stego_image.read()
    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    cover_pixels = None
    if cover_image:
        cover_bytes = await cover_image.read()
        try:
            cover_pixels, _ = ImageLoader.load_image(cover_bytes)
        except ImageValidationError:
            cover_pixels = None

    params: Dict[str, Any] = {
        "std": std,
        "mean": mean,
        "density": density,
        "salt_vs_pepper": salt_vs_pepper,
        "quality": quality,
        "kernel_size": kernel_size,
        "sigma": sigma,
        "seed": seed,
    }

    credentials = {
        "stego_key": stego_key or "",
        "stego_passphrase": stego_key or "",
        "recipient_private_key_pem": recipient_private_key_pem or "",
    }

    try:
        _, report = RobustnessProfiler.profile_attack(
            stego_img=stego_pixels,
            attack_type=attack_type,
            attack_params=params,
            cover_img=cover_pixels,
            original_payload=original_payload,
            extraction_method=extraction_method if extraction_method != "none" else None,
            credentials=credentials,
            block_size=block_size,
        )
        return RobustnessProfileResponse(**report.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/sweep", response_model=SweepResponse)
async def run_parameter_sweep(
    stego_image: UploadFile = File(..., description="Stego PNG image to sweep"),
    attack_type: str = Form("gaussian", description="Attack type to sweep: gaussian, salt_pepper, jpeg, blur, speckle"),
    intensities: Optional[str] = Form(None, description="Comma-separated float intensities (e.g. '0.5,1.0,2.0,3.0,5.0')"),
    extraction_method: str = Form("scatter", description="Extraction strategy: scatter, ai_adaptive, adaptive, baseline, pipeline_hybrid, none"),
    stego_key: Optional[str] = Form("", description="Steganographic key passphrase"),
    recipient_private_key_pem: Optional[str] = Form("", description="Recipient RSA private key for hybrid pipeline"),
    block_size: int = Form(16, description="Block partition size"),
    original_payload: Optional[str] = Form(None, description="Original secret message for payload BER calculation"),
):
    """Executes a multi-point parameter degradation sweep across noise/compression levels."""
    stego_bytes = await stego_image.read()
    try:
        stego_pixels, _ = ImageLoader.load_image(stego_bytes)
    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    intensity_list: Optional[List[float]] = None
    if intensities and intensities.strip():
        try:
            intensity_list = [float(x.strip()) for x in intensities.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid intensities list. Provide comma-separated numbers (e.g. '0.5,1.0,2.0').",
            )

    credentials = {
        "stego_key": stego_key or "",
        "stego_passphrase": stego_key or "",
        "recipient_private_key_pem": recipient_private_key_pem or "",
    }

    try:
        sweep_data = RobustnessProfiler.run_sweep(
            stego_img=stego_pixels,
            attack_type=attack_type,
            intensities=intensity_list,
            extraction_method=extraction_method if extraction_method != "none" else None,
            credentials=credentials,
            block_size=block_size,
            original_payload=original_payload,
        )

        typed_results = [RobustnessProfileResponse(**item) for item in sweep_data]
        return SweepResponse(
            attack_type=attack_type,
            points_count=len(typed_results),
            sweep_results=typed_results,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
