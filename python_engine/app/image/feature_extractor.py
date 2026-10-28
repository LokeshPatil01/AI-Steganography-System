"""Spatial feature extraction module for image complexity and texture analysis.

Extracts statistical, gradient, texture, and edge metrics:
- Shannon Entropy (Informational randomness)
- First and second order statistics (Mean, Variance, Standard Deviation)
- Sobel Gradient Magnitude (Edge transition intensity)
- Canny Edge Density (Edge boundary concentration)
- Laplacian Variance (Texture roughness / sharpness)
- Color Channel Variance (Inter-channel dispersion)
- Noise Characteristics (High-pass residual standard deviation)
"""
from dataclasses import asdict, dataclass
from typing import Dict, List, Tuple
import cv2
import numpy as np

@dataclass
class BlockFeatures:
    """Statistical and texture features for an individual image block."""
    block_x: int
    block_y: int
    width: int
    height: int
    entropy: float
    mean_intensity: float
    variance: float
    std_dev: float
    sobel_gradient_mean: float
    canny_edge_density: float
    color_variance: float
    laplacian_variance: float
    noise_residual_std: float

    def to_dict(self) -> Dict:
        return asdict(self)

@dataclass
class ImageAnalysisResult:
    """Comprehensive analysis report for an image."""
    image_width: int
    image_height: int
    channels: int
    block_size: int
    total_blocks_x: int
    total_blocks_y: int
    total_blocks: int
    global_features: Dict[str, float]
    feature_summary: Dict[str, float]
    blocks: List[BlockFeatures]

    def to_dict(self) -> Dict:
        return {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "channels": self.channels,
            "block_size": self.block_size,
            "total_blocks_x": self.total_blocks_x,
            "total_blocks_y": self.total_blocks_y,
            "total_blocks": self.total_blocks,
            "global_features": self.global_features,
            "feature_summary": self.feature_summary,
            "blocks": [b.to_dict() for b in self.blocks],
        }

class FeatureExtractor:
    """Extracts spatial complexity, gradient, and texture features."""

    @staticmethod
    def compute_entropy(channel_or_gray: np.ndarray) -> float:
        """Computes Shannon informational entropy in bits (range [0.0, 8.0])."""
        hist, _ = np.histogram(channel_or_gray, bins=256, range=(0, 256))
        total_pixels = channel_or_gray.size
        if total_pixels == 0:
            return 0.0

        p = hist / total_pixels
        non_zero_p = p[p > 0]
        entropy = -np.sum(non_zero_p * np.log2(non_zero_p))
        return float(round(entropy, 4))

    @staticmethod
    def compute_sobel_gradient(gray: np.ndarray) -> Tuple[float, float]:
        """Computes Sobel gradient magnitude: mean and max."""
        gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        magnitude = np.sqrt(gx**2 + gy**2)
        mean_grad = float(round(np.mean(magnitude), 4))
        max_grad = float(round(np.max(magnitude), 4))
        return mean_grad, max_grad

    @staticmethod
    def compute_canny_edge_density(
        gray: np.ndarray, low_thresh: int = 50, high_thresh: int = 150
    ) -> float:
        """Computes ratio of Canny edge pixels to total pixels (range [0.0, 1.0])."""
        edges = cv2.Canny(gray, low_thresh, high_thresh)
        density = np.count_nonzero(edges) / gray.size
        return float(round(density, 4))

    @staticmethod
    def compute_laplacian_variance(gray: np.ndarray) -> float:
        """Computes variance of the Laplacian (texture roughness/sharpness)."""
        lap = cv2.Laplacian(gray, cv2.CV_64F)
        var = float(round(np.var(lap), 4))
        return var

    @staticmethod
    def compute_color_variance(rgb_block: np.ndarray) -> float:
        """Computes cumulative variance across R, G, B color channels."""
        var_r = np.var(rgb_block[:, :, 0])
        var_g = np.var(rgb_block[:, :, 1])
        var_b = np.var(rgb_block[:, :, 2])
        return float(round(var_r + var_g + var_b, 4))

    @staticmethod
    def compute_noise_residual_std(gray: np.ndarray) -> float:
        """Estimates high-frequency noise standard deviation using median filtering."""
        # Median filter residual isolates micro-noise and local fluctuations
        ksize = 3
        if gray.shape[0] < ksize or gray.shape[1] < ksize:
            return 0.0

        median = cv2.medianBlur(gray, ksize)
        residual = np.abs(gray.astype(np.float64) - median.astype(np.float64))
        return float(round(np.std(residual), 4))

    @classmethod
    def extract_block_features(
        cls, rgb_block: np.ndarray, block_x: int, block_y: int
    ) -> BlockFeatures:
        """Extracts complete feature tuple from a single RGB block."""
        bh, bw, _ = rgb_block.shape
        gray_block = cv2.cvtColor(rgb_block, cv2.COLOR_RGB2GRAY)

        entropy = cls.compute_entropy(gray_block)
        mean_intensity = float(round(np.mean(gray_block), 4))
        variance = float(round(np.var(gray_block), 4))
        std_dev = float(round(np.std(gray_block), 4))
        grad_mean, _ = cls.compute_sobel_gradient(gray_block)
        edge_density = cls.compute_canny_edge_density(gray_block)
        color_var = cls.compute_color_variance(rgb_block)
        lap_var = cls.compute_laplacian_variance(gray_block)
        noise_std = cls.compute_noise_residual_std(gray_block)

        return BlockFeatures(
            block_x=block_x,
            block_y=block_y,
            width=bw,
            height=bh,
            entropy=entropy,
            mean_intensity=mean_intensity,
            variance=variance,
            std_dev=std_dev,
            sobel_gradient_mean=grad_mean,
            canny_edge_density=edge_density,
            color_variance=color_var,
            laplacian_variance=lap_var,
            noise_residual_std=noise_std,
        )

    @classmethod
    def analyze_image(
        cls, pixel_array: np.ndarray, block_size: int = 16
    ) -> ImageAnalysisResult:
        """Partitions image into N x N non-overlapping blocks, extracts features for each block,
        and computes global image complexity metrics.
        """
        h, w, c = pixel_array.shape
        gray_full = cv2.cvtColor(pixel_array, cv2.COLOR_RGB2GRAY)

        # 1. Global image features
        global_entropy = cls.compute_entropy(gray_full)
        global_grad_mean, _ = cls.compute_sobel_gradient(gray_full)
        global_edge_density = cls.compute_canny_edge_density(gray_full)
        global_var = float(round(np.var(gray_full), 4))
        global_color_var = cls.compute_color_variance(pixel_array)

        global_features = {
            "entropy": global_entropy,
            "variance": global_var,
            "mean_intensity": float(round(np.mean(gray_full), 4)),
            "std_dev": float(round(np.std(gray_full), 4)),
            "sobel_gradient_mean": global_grad_mean,
            "canny_edge_density": global_edge_density,
            "color_variance": global_color_var,
            "laplacian_variance": cls.compute_laplacian_variance(gray_full),
            "noise_residual_std": cls.compute_noise_residual_std(gray_full),
        }

        # 2. Block grid partitioning
        blocks_x = w // block_size
        blocks_y = h // block_size
        total_blocks = blocks_x * blocks_y

        block_list: List[BlockFeatures] = []

        for by in range(blocks_y):
            for bx in range(blocks_x):
                y_start = by * block_size
                y_end = y_start + block_size
                x_start = bx * block_size
                x_end = x_start + block_size

                block_rgb = pixel_array[y_start:y_end, x_start:x_end]
                feat = cls.extract_block_features(block_rgb, bx, by)
                block_list.append(feat)

        # 3. Statistical summary across blocks
        if block_list:
            summary = {
                "mean_block_entropy": float(round(np.mean([b.entropy for b in block_list]), 4)),
                "mean_block_variance": float(round(np.mean([b.variance for b in block_list]), 4)),
                "mean_block_gradient": float(round(np.mean([b.sobel_gradient_mean for b in block_list]), 4)),
                "mean_block_edge_density": float(round(np.mean([b.canny_edge_density for b in block_list]), 4)),
                "mean_block_color_variance": float(round(np.mean([b.color_variance for b in block_list]), 4)),
                "mean_block_laplacian_variance": float(round(np.mean([b.laplacian_variance for b in block_list]), 4)),
            }
        else:
            summary = {}

        return ImageAnalysisResult(
            image_width=w,
            image_height=h,
            channels=c,
            block_size=block_size,
            total_blocks_x=blocks_x,
            total_blocks_y=blocks_y,
            total_blocks=total_blocks,
            global_features=global_features,
            feature_summary=summary,
            blocks=block_list,
        )
