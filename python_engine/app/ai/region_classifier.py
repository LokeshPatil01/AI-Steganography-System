"""AI Region Suitability Classifier Service (Phase 13).

Integrates the trained Random Forest model (Phase 12) into the FastAPI runtime.
Classifies 16x16 image blocks by steganographic embedding suitability:
- Class 0: Smooth / Low Texture (Preserved untouched; lowest HVS masking)
- Class 1: Medium Texture (Moderate embedding capacity)
- Class 2: High Texture / Complex Edges (High capacity; maximum HVS masking)

Provides:
- Single-block and batch-image spatial classification
- Deterministic MSB-invariant block ranking
- Visual color-coded heatmap generation for UI overlay
"""
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import joblib
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODEL_PATH = BASE_DIR / "models" / "region_model.joblib"
METADATA_PATH = BASE_DIR / "models" / "region_model_metadata.json"

FEATURE_NAMES = [
    "entropy",
    "variance",
    "std_dev",
    "sobel_gradient_mean",
    "canny_edge_density",
    "laplacian_variance",
    "color_variance",
    "noise_residual_std",
]

CLASS_NAMES = {
    0: "Smooth",
    1: "Medium",
    2: "HighTexture",
}


@dataclass
class BlockClassification:
    """Prediction result for a single image block."""
    block_x: int
    block_y: int
    predicted_class: int
    class_name: str
    probabilities: Dict[str, float]
    suitability_score: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ImageRegionAnalysisResult:
    """Comprehensive region suitability report for an entire image."""
    image_width: int
    image_height: int
    block_size: int
    total_blocks: int
    grid_blocks_x: int
    grid_blocks_y: int
    class_counts: Dict[str, int]
    class_percentages: Dict[str, float]
    high_texture_blocks: int
    medium_texture_blocks: int
    smooth_blocks: int
    recommended_capacity_bytes: int
    ranked_blocks: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RegionClassifier:
    """Inference engine for block-level AI region suitability classification."""

    _model_instance = None
    _metadata_cache = None

    @classmethod
    def get_model(cls):
        """Loads and caches the Random Forest model artifact."""
        if cls._model_instance is None:
            if not MODEL_PATH.is_file():
                raise FileNotFoundError(
                    f"AI Region model artifact not found at: {MODEL_PATH}. "
                    "Run training/region_model/train.py first."
                )
            cls._model_instance = joblib.load(MODEL_PATH)
        return cls._model_instance

    @classmethod
    def get_metadata(cls) -> Dict[str, Any]:
        """Loads and caches model training metadata."""
        if cls._metadata_cache is None:
            if METADATA_PATH.is_file():
                with open(METADATA_PATH, "r", encoding="utf-8") as f:
                    cls._metadata_cache = json.load(f)
            else:
                cls._metadata_cache = {"status": "metadata_not_found"}
        return cls._metadata_cache

    @staticmethod
    def extract_features_msb(rgb_block: np.ndarray) -> List[float]:
        """Extracts the 8 standardized features on upper 7 bits (pixel & 0xFE) for MSB invariance."""
        msb_block = (rgb_block & 0xFE).astype(np.uint8)
        gray = cv2.cvtColor(msb_block, cv2.COLOR_RGB2GRAY)

        # 1. Shannon Entropy
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        total_p = gray.size
        p = hist[hist > 0] / total_p
        entropy = float(round(-np.sum(p * np.log2(p)), 4)) if len(p) > 0 else 0.0

        # 2 & 3. Variance & Std Dev
        variance = float(round(float(np.var(gray)), 4))
        std_dev = float(round(float(np.std(gray)), 4))

        # 4. Sobel Gradient Magnitude Mean
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        mag = np.sqrt(gx**2 + gy**2)
        sobel_mean = float(round(float(np.mean(mag)), 4))

        # 5. Canny Edge Density
        edges = cv2.Canny(gray, 50, 150)
        edge_density = float(round(float(np.count_nonzero(edges) / gray.size), 4))

        # 6. Laplacian Variance
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = float(round(float(np.var(lap)), 4))

        # 7. Color Variance
        var_r = float(np.var(msb_block[:, :, 0]))
        var_g = float(np.var(msb_block[:, :, 1]))
        var_b = float(np.var(msb_block[:, :, 2]))
        color_var = float(round(var_r + var_g + var_b, 4))

        # 8. High-Pass Noise Residual Std
        ksize = 3
        if gray.shape[0] >= ksize and gray.shape[1] >= ksize:
            median = cv2.medianBlur(gray, ksize)
            residual = np.abs(gray.astype(np.float64) - median.astype(np.float64))
            noise_std = float(round(float(np.std(residual)), 4))
        else:
            noise_std = 0.0

        return [
            entropy,
            variance,
            std_dev,
            sobel_mean,
            edge_density,
            lap_var,
            color_var,
            noise_std,
        ]

    @classmethod
    def classify_block(cls, rgb_block: np.ndarray, block_x: int = 0, block_y: int = 0) -> BlockClassification:
        """Classifies a single RGB image block."""
        model = cls.get_model()
        feat_vec = cls.extract_features_msb(rgb_block)
        feat_matrix = np.array([feat_vec], dtype=np.float32)

        pred_class = int(model.predict(feat_matrix)[0])
        probs = model.predict_proba(feat_matrix)[0]

        prob_dict = {
            "Smooth": float(round(float(probs[0]), 4)),
            "Medium": float(round(float(probs[1]), 4)),
            "HighTexture": float(round(float(probs[2]), 4)),
        }

        # Composite suitability score: Higher = better for embedding
        suitability_score = float(round(float(probs[2] * 2.0 + probs[1] * 1.0), 4))

        return BlockClassification(
            block_x=block_x,
            block_y=block_y,
            predicted_class=pred_class,
            class_name=CLASS_NAMES[pred_class],
            probabilities=prob_dict,
            suitability_score=suitability_score,
        )

    @classmethod
    def analyze_image(cls, pixel_array: np.ndarray, block_size: int = 16) -> ImageRegionAnalysisResult:
        """Splits image into non-overlapping N x N blocks and performs vectorized batch classification."""
        model = cls.get_model()
        h, w, c = pixel_array.shape

        grid_y = h // block_size
        grid_x = w // block_size
        total_blocks = grid_y * grid_x

        if total_blocks == 0:
            raise ValueError(f"Image dimensions ({w}x{h}) smaller than block size ({block_size}x{block_size})")

        # 1. Batch extract feature vectors
        feature_rows: List[List[float]] = []
        block_coords: List[Tuple[int, int]] = []

        for by in range(grid_y):
            y_start = by * block_size
            y_end = y_start + block_size
            for bx in range(grid_x):
                x_start = bx * block_size
                x_end = x_start + block_size

                block = pixel_array[y_start:y_end, x_start:x_end, :]
                feats = cls.extract_features_msb(block)
                feature_rows.append(feats)
                block_coords.append((bx, by))

        # 2. Vectorized parallel inference
        X_matrix = np.array(feature_rows, dtype=np.float32)
        predictions = model.predict(X_matrix)
        probabilities = model.predict_proba(X_matrix)

        # 3. Aggregate class statistics
        class_counts = {0: 0, 1: 0, 2: 0}
        ranked_blocks: List[Dict[str, Any]] = []

        for idx, (bx, by) in enumerate(block_coords):
            p_class = int(predictions[idx])
            probs = probabilities[idx]
            class_counts[p_class] += 1

            p_smooth = float(round(float(probs[0]), 4))
            p_med = float(round(float(probs[1]), 4))
            p_high = float(round(float(probs[2]), 4))
            suitability = float(round(float(p_high * 2.0 + p_med * 1.0), 4))

            ranked_blocks.append({
                "block_index": idx,
                "block_x": bx,
                "block_y": by,
                "predicted_class": p_class,
                "class_name": CLASS_NAMES[p_class],
                "suitability_score": suitability,
                "prob_high_texture": p_high,
                "prob_medium": p_med,
                "prob_smooth": p_smooth,
            })

        # Sort ranked blocks descending by suitability score, then by index for deterministic order
        ranked_blocks.sort(key=lambda b: (-b["suitability_score"], b["block_y"], b["block_x"]))

        # Capacity recommendation:
        # High texture = 3 bits/channel * 3 channels * block_size^2
        # Medium = 1 bit/channel * 3 channels * block_size^2
        # Smooth = 0 bits (100% preserved)
        pixels_per_block = block_size * block_size
        high_cap_bits = class_counts[2] * pixels_per_block * 3  # 1 bit per RGB channel (or up to 2-3)
        med_cap_bits = class_counts[1] * pixels_per_block * 3
        rec_capacity_bytes = (high_cap_bits + med_cap_bits) // 8

        class_percentages = {
            "Smooth": float(round((class_counts[0] / total_blocks) * 100, 2)),
            "Medium": float(round((class_counts[1] / total_blocks) * 100, 2)),
            "HighTexture": float(round((class_counts[2] / total_blocks) * 100, 2)),
        }

        counts_dict = {
            "Smooth": class_counts[0],
            "Medium": class_counts[1],
            "HighTexture": class_counts[2],
        }

        return ImageRegionAnalysisResult(
            image_width=w,
            image_height=h,
            block_size=block_size,
            total_blocks=total_blocks,
            grid_blocks_x=grid_x,
            grid_blocks_y=grid_y,
            class_counts=counts_dict,
            class_percentages=class_percentages,
            high_texture_blocks=class_counts[2],
            medium_texture_blocks=class_counts[1],
            smooth_blocks=class_counts[0],
            recommended_capacity_bytes=rec_capacity_bytes,
            ranked_blocks=ranked_blocks,
        )

    @classmethod
    def generate_heatmap_overlay(
        cls,
        pixel_array: np.ndarray,
        block_size: int = 16,
        alpha: float = 0.40,
    ) -> np.ndarray:
        """Generates a color-coded visual heatmap overlay indicating AI region suitability:
        - Emerald Green: High Texture (Class 2 - Ideal for steganography)
        - Amber Yellow: Medium Texture (Class 1 - Moderate capacity)
        - Sapphire Blue: Smooth / Flat (Class 0 - Preserved untouched)
        """
        analysis = cls.analyze_image(pixel_array, block_size)
        h, w, c = pixel_array.shape

        overlay = pixel_array.copy().astype(np.float32)
        color_map = {
            2: np.array([16, 185, 129], dtype=np.float32),   # HighTexture: Vibrant Emerald Green
            1: np.array([245, 158, 11], dtype=np.float32),   # Medium: Amber Yellow
            0: np.array([14, 116, 144], dtype=np.float32),   # Smooth: Deep Cyan / Blue
        }

        for block_info in analysis.ranked_blocks:
            bx = block_info["block_x"]
            by = block_info["block_y"]
            cls_id = block_info["predicted_class"]

            y_start = by * block_size
            y_end = y_start + block_size
            x_start = bx * block_size
            x_end = x_start + block_size

            tint = color_map[cls_id]
            region = overlay[y_start:y_end, x_start:x_end, :]
            blended = region * (1.0 - alpha) + tint * alpha
            overlay[y_start:y_end, x_start:x_end, :] = blended

        # Draw subtle grid boundary lines
        grid_img = np.clip(overlay, 0, 255).astype(np.uint8)
        grid_color = (255, 255, 255)
        for y in range(0, (h // block_size) * block_size + 1, block_size):
            cv2.line(grid_img, (0, y), ((w // block_size) * block_size, y), grid_color, 1, lineType=cv2.LINE_AA)
        for x in range(0, (w // block_size) * block_size + 1, block_size):
            cv2.line(grid_img, (x, 0), (x, (h // block_size) * block_size), grid_color, 1, lineType=cv2.LINE_AA)

        return grid_img
