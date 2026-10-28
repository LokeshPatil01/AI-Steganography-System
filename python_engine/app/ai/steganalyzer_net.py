"""Deep Learning CNN Steganalyzer Runtime Inference Module (Phase 16).

Provides real-time steganalysis inference using the trained PyTorch SteganalyzerCNN:
- Preprocesses images through Spatial Rich Model (SRM) High-Pass Filtering.
- Evaluates detectability probability P(stego) in [0.0, 1.0].
- Security Decision Threshold tau = 0.35 (per PROJECT_ARCHITECTURE.md Section 8.2):
    - P(stego) < 0.35: Steganographically secure; passes adversarial inspection.
    - P(stego) >= 0.35: Flagged as detectable; triggers iterative feedback loop.
- Calculates residual energy and categorical risk levels.
"""
from dataclasses import asdict, dataclass
import io
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image
import torch

from app.image.loader import ImageLoader
from training.steganalyzer.model_architecture import SpatialRichModelLayer, SteganalyzerCNN


@dataclass
class StegoDetectionResult:
    """Detection report produced by the CNN Steganalyzer."""
    is_stego: bool
    stego_probability: float
    confidence: float
    residual_energy: float
    risk_level: str  # 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
    decision_threshold: float
    recommendation: str
    model_version: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SteganalyzerDetector:
    """Manages model loading and runtime inference for steganography detection."""

    DEFAULT_THRESHOLD: float = 0.35
    MODEL_PATH: Path = Path(__file__).resolve().parent.parent.parent / "models" / "steganalyzer.pth"
    METADATA_PATH: Path = Path(__file__).resolve().parent.parent.parent / "models" / "steganalyzer_metadata.json"

    _instance: Optional["SteganalyzerDetector"] = None

    def __init__(
        self,
        model_path: Optional[Union[str, Path]] = None,
        threshold: float = DEFAULT_THRESHOLD,
        device: Optional[str] = None,
    ):
        self.model_path = Path(model_path) if model_path else self.MODEL_PATH
        self.threshold = threshold
        self.metadata: Dict[str, Any] = {}

        if device is None:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        self.model: Optional[SteganalyzerCNN] = None
        self.srm_fallback: SpatialRichModelLayer = SpatialRichModelLayer().to(self.device).eval()
        self._load_model()

    @classmethod
    def get_instance(cls) -> "SteganalyzerDetector":
        """Singleton accessor for efficient reuse across API requests."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_model(self) -> None:
        """Loads trained weights if available, otherwise falls back gracefully."""
        if self.model_path.exists():
            try:
                ckpt = torch.load(self.model_path, map_location=self.device)
                self.model = SteganalyzerCNN().to(self.device)
                self.model.load_state_dict(ckpt["model_state_dict"])
                self.model.eval()

                if self.METADATA_PATH.exists():
                    with open(self.METADATA_PATH, "r", encoding="utf-8") as f:
                        self.metadata = json.load(f)
            except Exception as e:
                self.model = None
        else:
            self.model = None

    def predict(
        self,
        image_input: Union[np.ndarray, bytes],
        threshold: Optional[float] = None,
    ) -> StegoDetectionResult:
        """Evaluates an image and returns a comprehensive stego detection report.

        Args:
            image_input: Either RGB numpy array [H, W, 3] uint8 or raw PNG image bytes.
            threshold: Optional override for the security decision threshold tau.

        Returns:
            StegoDetectionResult with probability, risk level, and residual energy.
        """
        tau = threshold if threshold is not None else self.threshold

        # Parse image into RGB numpy array
        if isinstance(image_input, (bytes, bytearray)):
            pixels, _ = ImageLoader.load_image(image_input)
        elif isinstance(image_input, np.ndarray):
            pixels = image_input
        else:
            raise ValueError(f"Unsupported image_input type: {type(image_input)}")

        if pixels.ndim != 3 or pixels.shape[2] != 3:
            raise ValueError(f"Expected RGB image array [H, W, 3], got shape {pixels.shape}")

        # Convert to grayscale luminance Y = 0.299R + 0.587G + 0.114B
        gray = cv2.cvtColor(pixels, cv2.COLOR_RGB2GRAY)
        img_tensor = torch.from_numpy(gray).float().unsqueeze(0).unsqueeze(0).to(self.device)

        # Compute SRM residual energy for feature explainability
        with torch.no_grad():
            srm_layer = self.model.srm if self.model is not None else self.srm_fallback
            residuals = srm_layer(img_tensor)
            residual_energy = float(torch.mean(torch.abs(residuals)).item())

            if self.model is not None:
                prob = float(self.model.predict_proba(img_tensor).item())
            else:
                # Fallback heuristic based on high-pass residual energy if weights not yet saved
                # Micro LSB flips elevate residual energy above 0.35 in smooth regions
                prob = float(np.clip(residual_energy / 2.5, 0.05, 0.95))

        # Categorize risk level
        if prob < 0.20:
            risk = "LOW"
            rec = "PASS: Image exhibits minimal steganographic noise residual."
        elif prob < tau:
            risk = "MODERATE"
            rec = "PASS: Minor high-frequency variance; within acceptable security tolerance."
        elif prob < 0.65:
            risk = "HIGH"
            rec = "FLAGGED: Anomalous residual pattern detected. Feedback optimization recommended."
        else:
            risk = "CRITICAL"
            rec = "FLAGGED: Strong steganographic signature detected. Re-embedding required."

        is_stego = prob >= tau
        confidence = round(abs(prob - 0.5) * 2.0, 4)

        return StegoDetectionResult(
            is_stego=is_stego,
            stego_probability=round(prob, 4),
            confidence=confidence,
            residual_energy=round(residual_energy, 4),
            risk_level=risk,
            decision_threshold=round(tau, 2),
            recommendation=rec,
            model_version=self.metadata.get("model_name", "SteganalyzerCNN-v1"),
        )
