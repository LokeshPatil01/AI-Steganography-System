"""FastAPI Route for Deep Learning Steganalyzer CNN (Phase 16).

Provides public endpoints:
- GET  /ai/steganalyzer/info   : Model architecture, parameter counts, and test metrics
- POST /ai/steganalyzer/detect : Upload image to receive detection report & P(stego)
- POST /detect                 : Architecture specification alias endpoint
"""
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from app.ai.steganalyzer_net import SteganalyzerDetector, StegoDetectionResult
from app.image.loader import ImageValidationError

router = APIRouter(prefix="", tags=["Steganalysis AI"])


class SteganalysisInfoResponse(BaseModel):
    model_name: str
    model_type: str
    framework: str
    decision_threshold: float
    parameters: dict
    training_samples: int
    validation_samples: int
    test_samples: int
    test_metrics: dict


class StegoDetectionResponse(BaseModel):
    is_stego: bool = Field(..., description="True if P(stego) >= decision_threshold")
    stego_probability: float = Field(..., description="Adversarial stego detection score in [0.0, 1.0]")
    confidence: float = Field(..., description="|P - 0.5| * 2 confidence metric")
    residual_energy: float = Field(..., description="Mean absolute SRM high-pass residual energy")
    risk_level: str = Field(..., description="LOW | MODERATE | HIGH | CRITICAL")
    decision_threshold: float = Field(..., description="Cutoff threshold tau (default 0.35)")
    recommendation: str = Field(..., description="Guidance for embedding or feedback loop")
    model_version: str


@router.get("/ai/steganalyzer/info", response_model=SteganalysisInfoResponse)
async def get_steganalyzer_info():
    """Returns architecture specifications, hyperparameters, and test benchmarks."""
    detector = SteganalyzerDetector.get_instance()
    meta = detector.metadata

    if not meta:
        return SteganalysisInfoResponse(
            model_name="SteganalyzerCNN",
            model_type="Spatial Rich Model (SRM) Convolutional Steganalyzer",
            framework="PyTorch",
            decision_threshold=detector.threshold,
            parameters={"total": 249580, "trainable": 249505, "fixed_srm": 75},
            training_samples=0,
            validation_samples=0,
            test_samples=0,
            test_metrics={"status": "Pre-initialization"},
        )

    return SteganalysisInfoResponse(
        model_name=meta.get("model_name", "SteganalyzerCNN"),
        model_type=meta.get("model_type", "Spatial Rich Model (SRM) Convolutional Steganalyzer"),
        framework=meta.get("framework", "PyTorch"),
        decision_threshold=meta.get("security_decision_threshold", detector.threshold),
        parameters=meta.get("parameters", {}),
        training_samples=meta.get("training_samples", 0),
        validation_samples=meta.get("validation_samples", 0),
        test_samples=meta.get("test_samples", 0),
        test_metrics=meta.get("test_metrics", {}),
    )


@router.post("/ai/steganalyzer/detect", response_model=StegoDetectionResponse)
async def detect_stego(
    image: UploadFile = File(..., description="Candidate cover or stego image"),
    threshold: Optional[float] = Form(None, description="Optional override for security threshold tau"),
):
    """Evaluates candidate image detectability through SRM High-Pass Filtering and CNN inference."""
    try:
        image_bytes = await image.read()
        detector = SteganalyzerDetector.get_instance()
        res: StegoDetectionResult = detector.predict(image_bytes, threshold=threshold)

        return StegoDetectionResponse(
            is_stego=res.is_stego,
            stego_probability=res.stego_probability,
            confidence=res.confidence,
            residual_energy=res.residual_energy,
            risk_level=res.risk_level,
            decision_threshold=res.decision_threshold,
            recommendation=res.recommendation,
            model_version=res.model_version,
        )

    except ImageValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Steganalysis inference failed: {str(e)}",
        )


@router.post("/detect", response_model=StegoDetectionResponse)
async def detect_stego_alias(
    image: UploadFile = File(..., description="Candidate image"),
    threshold: Optional[float] = Form(None),
):
    """Alias for /ai/steganalyzer/detect adhering to PROJECT_ARCHITECTURE.md route table."""
    return await detect_stego(image, threshold)
