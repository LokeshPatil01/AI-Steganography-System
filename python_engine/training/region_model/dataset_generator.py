"""Dataset Generation Module for AI Region Suitability Model (Phase 11).

Generates a balanced, diverse corpus of image blocks across three texture classes:
- Class 0: Smooth / Low Texture (Flat regions, sky, uniform surfaces - poor visual masking)
- Class 1: Medium Texture (Gentle gradients, mild natural variations - moderate masking)
- Class 2: High Texture / Complex Edges (High gradient boundaries, dense patterns - high masking)

Extracts 8 spatial complexity and texture features per 16x16 block:
1. Shannon Entropy
2. Luminance Variance
3. Standard Deviation
4. Sobel Gradient Magnitude Mean
5. Canny Edge Density
6. Laplacian Variance (Sharpness/Curvature)
7. Color Channel Variance
8. High-Pass Noise Residual Standard Deviation

Exports balanced feature vectors to CSV for Random Forest training in Phase 12.
"""
import csv
import math
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import cv2
import numpy as np

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

LABEL_COLUMN = "suitability_label"


@dataclass
class RegionFeatureSample:
    """Feature vector and ground-truth suitability label for a single 16x16 image block."""
    entropy: float
    variance: float
    std_dev: float
    sobel_gradient_mean: float
    canny_edge_density: float
    laplacian_variance: float
    color_variance: float
    noise_residual_std: float
    suitability_label: int  # 0: Smooth, 1: Medium, 2: High Texture

    def to_dict(self) -> Dict:
        return asdict(self)

    def to_feature_list(self) -> List[float]:
        return [
            self.entropy,
            self.variance,
            self.std_dev,
            self.sobel_gradient_mean,
            self.canny_edge_density,
            self.laplacian_variance,
            self.color_variance,
            self.noise_residual_std,
        ]


class RegionDatasetGenerator:
    """Synthesizes varied visual patterns and extracts standardized spatial features."""

    FEATURE_NAMES = FEATURE_NAMES
    LABEL_COLUMN = LABEL_COLUMN

    def __init__(self, block_size: int = 16, random_seed: int = 42):
        self.block_size = block_size
        self.rng = np.random.RandomState(random_seed)

    # -------------------------------------------------------------------------
    # Spatial Feature Extraction
    # -------------------------------------------------------------------------
    @staticmethod
    def extract_features(rgb_block: np.ndarray) -> Dict[str, float]:
        """Extracts the 8 standardized spatial and texture features from a single RGB block.

        Uses the upper 7 bits (pixel & 0xFE) to preserve MSB-plane invariance.
        """
        if rgb_block.ndim != 3 or rgb_block.shape[2] != 3:
            raise ValueError(f"Expected 3-channel RGB block, got shape {rgb_block.shape}")

        # MSB invariance: bit 0 ignored so features match between cover and stego
        msb_block = (rgb_block & 0xFE).astype(np.uint8)
        gray = cv2.cvtColor(msb_block, cv2.COLOR_RGB2GRAY)

        # 1. Shannon Entropy
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        total_p = gray.size
        p = hist[hist > 0] / total_p
        entropy = float(round(-np.sum(p * np.log2(p)), 4)) if len(p) > 0 else 0.0

        # 2 & 3. Mean, Variance, Standard Deviation
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

        # 6. Laplacian Variance (Texture Roughness)
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        lap_var = float(round(float(np.var(lap)), 4))

        # 7. Color Variance (Inter-channel variance sum)
        var_r = float(np.var(msb_block[:, :, 0]))
        var_g = float(np.var(msb_block[:, :, 1]))
        var_b = float(np.var(msb_block[:, :, 2]))
        color_var = float(round(var_r + var_g + var_b, 4))

        # 8. High-Pass Noise Residual Standard Deviation
        ksize = 3
        if gray.shape[0] >= ksize and gray.shape[1] >= ksize:
            median = cv2.medianBlur(gray, ksize)
            residual = np.abs(gray.astype(np.float64) - median.astype(np.float64))
            noise_std = float(round(float(np.std(residual)), 4))
        else:
            noise_std = 0.0

        return {
            "entropy": entropy,
            "variance": variance,
            "std_dev": std_dev,
            "sobel_gradient_mean": sobel_mean,
            "canny_edge_density": edge_density,
            "laplacian_variance": lap_var,
            "color_variance": color_var,
            "noise_residual_std": noise_std,
        }

    # -------------------------------------------------------------------------
    # Synthetic Block Generators by Visual Archetype
    # -------------------------------------------------------------------------
    def generate_smooth_block(self) -> np.ndarray:
        """Synthesizes a Class 0 (Smooth) image block:
        Solid uniform tone, ultra-low gradient ramp, or faint micro-noise (< 2.0 std).
        """
        b = self.block_size
        mode = self.rng.choice(["solid", "faint_ramp", "faint_noise"])

        base_color = self.rng.randint(20, 235, size=(3,), dtype=np.int32)

        if mode == "solid":
            block = np.full((b, b, 3), base_color, dtype=np.float64)
        elif mode == "faint_ramp":
            # Subtle ramp with delta <= 3 levels across entire 16px
            ramp_x = np.linspace(0, self.rng.uniform(0.5, 3.0), b)
            ramp_y = np.linspace(0, self.rng.uniform(0.5, 3.0), b)
            grid = ramp_x[None, :] + ramp_y[:, None]
            block = base_color[None, None, :] + grid[:, :, None]
        else:  # faint_noise
            noise = self.rng.normal(0, 1.2, size=(b, b, 3))
            block = base_color[None, None, :] + noise

        block = np.clip(block, 0, 255).astype(np.uint8)
        return block

    def generate_medium_block(self) -> np.ndarray:
        """Synthesizes a Class 1 (Medium Texture) image block:
        Soft harmonic wave, gentle diagonal gradient, organic low-frequency noise.
        """
        b = self.block_size
        mode = self.rng.choice(["sine_wave", "medium_gradient", "soft_texture", "checker_soft"])

        base_color = self.rng.randint(40, 215, size=(3,), dtype=np.int32).astype(np.float64)

        if mode == "sine_wave":
            freq = self.rng.uniform(0.2, 0.6)
            phase = self.rng.uniform(0, 2 * math.pi)
            x = np.arange(b)
            wave = np.sin(x * freq + phase) * self.rng.uniform(8.0, 22.0)
            wave_2d = np.tile(wave[None, :, None], (b, 1, 1))
            block = base_color[None, None, :] + wave_2d
        elif mode == "medium_gradient":
            dx = self.rng.uniform(10.0, 35.0)
            dy = self.rng.uniform(10.0, 35.0)
            ramp_x = np.linspace(-dx / 2, dx / 2, b)
            ramp_y = np.linspace(-dy / 2, dy / 2, b)
            grid = ramp_x[None, :] + ramp_y[:, None]
            block = base_color[None, None, :] + grid[:, :, None]
        elif mode == "checker_soft":
            sq = self.rng.choice([4, 8])
            check = np.indices((b, b)).sum(axis=0) // sq % 2
            contrast = self.rng.uniform(10.0, 25.0)
            mod = (check * 2 - 1) * contrast
            block = base_color[None, None, :] + mod[:, :, None]
        else:  # soft_texture
            noise = self.rng.normal(0, self.rng.uniform(8.0, 18.0), size=(b, b, 3))
            # Blur slightly to maintain medium frequency rather than harsh edges
            blurred = cv2.GaussianBlur(noise.astype(np.float32), (3, 3), 0.8)
            block = base_color[None, None, :] + blurred

        block = np.clip(block, 0, 255).astype(np.uint8)
        return block

    def generate_high_texture_block(self) -> np.ndarray:
        """Synthesizes a Class 2 (High Texture / Complex Edge) image block:
        Sharp edge step, dense high-frequency noise, fine grid, diagonal slash, or sharp checkerboard.
        """
        b = self.block_size
        mode = self.rng.choice(["sharp_edge", "high_freq_noise", "checker_dense", "diagonal_slash", "dense_points"])

        c1 = self.rng.randint(20, 100, size=(3,), dtype=np.int32).astype(np.float64)
        c2 = self.rng.randint(160, 240, size=(3,), dtype=np.int32).astype(np.float64)

        if mode == "sharp_edge":
            split = self.rng.randint(4, 12)
            horizontal = self.rng.choice([True, False])
            block = np.zeros((b, b, 3), dtype=np.float64)
            if horizontal:
                block[:split, :, :] = c1
                block[split:, :, :] = c2
            else:
                block[:, :split, :] = c1
                block[:, split:, :] = c2
            # Add fine boundary jitter
            block += self.rng.normal(0, 5.0, size=(b, b, 3))

        elif mode == "diagonal_slash":
            xx, yy = np.meshgrid(np.arange(b), np.arange(b))
            mask = (xx + yy) > self.rng.randint(10, 22)
            block = np.where(mask[:, :, None], c2, c1).astype(np.float64)
            block += self.rng.normal(0, 6.0, size=(b, b, 3))

        elif mode == "checker_dense":
            sq = 2  # tight 2x2 squares produce heavy gradient crossings
            check = np.indices((b, b)).sum(axis=0) // sq % 2
            block = np.where(check[:, :, None] == 1, c2, c1).astype(np.float64)

        elif mode == "dense_points":
            base = self.rng.randint(80, 160, size=(3,), dtype=np.int32).astype(np.float64)
            block = np.full((b, b, 3), base, dtype=np.float64)
            pts_x = self.rng.randint(0, b, size=24)
            pts_y = self.rng.randint(0, b, size=24)
            block[pts_y, pts_x, :] = c2

        else:  # high_freq_noise
            base = self.rng.randint(60, 180, size=(3,), dtype=np.int32).astype(np.float64)
            noise = self.rng.normal(0, self.rng.uniform(25.0, 50.0), size=(b, b, 3))
            block = base[None, None, :] + noise

        block = np.clip(block, 0, 255).astype(np.uint8)
        return block

    # -------------------------------------------------------------------------
    # Label Verification & Refinement
    # -------------------------------------------------------------------------
    @staticmethod
    def classify_by_hvs_rules(features: Dict[str, float]) -> int:
        """Determines ground-truth suitability class using empirical Human Visual System (HVS) criteria.

        Score = 0.25*Norm(H) + 0.25*Norm(G) + 0.25*Norm(E) + 0.15*Norm(V) + 0.10*Norm(L)
        Class 0: Score < 0.22 and Variance < 80.0
        Class 2: Score > 0.55 or Canny Density > 0.15 or Gradient > 35.0
        Class 1: Everything in between
        """
        h_norm = min(1.0, features["entropy"] / 7.5)
        g_norm = min(1.0, features["sobel_gradient_mean"] / 60.0)
        e_norm = min(1.0, features["canny_edge_density"] / 0.30)
        v_norm = min(1.0, features["variance"] / 800.0)
        l_norm = min(1.0, features["laplacian_variance"] / 500.0)

        composite_score = 0.25 * h_norm + 0.25 * g_norm + 0.25 * e_norm + 0.15 * v_norm + 0.10 * l_norm

        if composite_score < 0.22 and features["variance"] < 80.0 and features["canny_edge_density"] < 0.05:
            return 0
        if composite_score > 0.52 or features["canny_edge_density"] > 0.15 or features["sobel_gradient_mean"] > 35.0:
            return 2
        return 1

    # -------------------------------------------------------------------------
    # Full Balanced Dataset Generation Pipeline
    # -------------------------------------------------------------------------
    def generate_balanced_dataset(
        self, samples_per_class: int = 1000
    ) -> List[RegionFeatureSample]:
        """Generates a strictly balanced list of RegionFeatureSample records across classes [0, 1, 2]."""
        dataset: List[RegionFeatureSample] = []
        counts = {0: 0, 1: 0, 2: 0}

        # Targeted generator loop with verification ensuring pure, verified samples
        max_attempts_per_class = samples_per_class * 5

        for target_label in [0, 1, 2]:
            attempts = 0
            while counts[target_label] < samples_per_class and attempts < max_attempts_per_class:
                attempts += 1
                if target_label == 0:
                    block = self.generate_smooth_block()
                elif target_label == 1:
                    block = self.generate_medium_block()
                else:
                    block = self.generate_high_texture_block()

                features = self.extract_features(block)
                actual_label = self.classify_by_hvs_rules(features)

                # Only accept if it strictly satisfies the target class definition
                if actual_label == target_label:
                    sample = RegionFeatureSample(
                        entropy=features["entropy"],
                        variance=features["variance"],
                        std_dev=features["std_dev"],
                        sobel_gradient_mean=features["sobel_gradient_mean"],
                        canny_edge_density=features["canny_edge_density"],
                        laplacian_variance=features["laplacian_variance"],
                        color_variance=features["color_variance"],
                        noise_residual_std=features["noise_residual_std"],
                        suitability_label=target_label,
                    )
                    dataset.append(sample)
                    counts[target_label] += 1

        # Shuffle dataset cleanly
        indices = np.arange(len(dataset))
        self.rng.shuffle(indices)
        shuffled_dataset = [dataset[i] for i in indices]
        return shuffled_dataset

    # -------------------------------------------------------------------------
    # CSV Serialization & Deserialization
    # -------------------------------------------------------------------------
    @classmethod
    def save_to_csv(cls, samples: List[RegionFeatureSample], output_path: str) -> str:
        """Serializes samples to CSV with header schema."""
        dest = Path(output_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        fieldnames = FEATURE_NAMES + [LABEL_COLUMN]
        with open(dest, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in samples:
                writer.writerow(s.to_dict())

        return str(dest.resolve())

    @classmethod
    def load_from_csv(
        cls, csv_path: str
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Reads CSV and returns (X features, y labels, feature_names).

        Returns:
            X: np.ndarray of shape (N, 8), dtype float32
            y: np.ndarray of shape (N,), dtype int64
            feature_names: list of column names
        """
        path = Path(csv_path)
        if not path.is_file():
            raise FileNotFoundError(f"Dataset CSV not found at: {csv_path}")

        features: List[List[float]] = []
        labels: List[int] = []

        with open(path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                feat_vec = [float(row[k]) for k in FEATURE_NAMES]
                label = int(row[LABEL_COLUMN])
                features.append(feat_vec)
                labels.append(label)

        x_arr = np.array(features, dtype=np.float32)
        y_arr = np.array(labels, dtype=np.int64)
        return x_arr, y_arr, FEATURE_NAMES

    @classmethod
    def summarize_dataset(cls, csv_path: str) -> Dict[str, any]:
        """Calculates dataset distribution and validation diagnostics."""
        X, y, feats = cls.load_from_csv(csv_path)
        total_samples = len(y)

        unique, counts = np.unique(y, return_counts=True)
        class_dist = {int(cls_id): int(cnt) for cls_id, cnt in zip(unique, counts)}

        # Statistical summary
        feature_stats = {}
        for idx, name in enumerate(feats):
            vals = X[:, idx]
            feature_stats[name] = {
                "min": float(np.min(vals)),
                "max": float(np.max(vals)),
                "mean": float(round(float(np.mean(vals)), 4)),
                "std": float(round(float(np.std(vals)), 4)),
            }

        has_nans = bool(np.isnan(X).any() or np.isnan(y).any())
        has_infs = bool(np.isinf(X).any() or np.isinf(y).any())

        return {
            "total_samples": total_samples,
            "feature_count": len(feats),
            "class_distribution": class_dist,
            "feature_statistics": feature_stats,
            "is_valid": not has_nans and not has_infs,
            "has_nans": has_nans,
            "has_infs": has_infs,
        }
