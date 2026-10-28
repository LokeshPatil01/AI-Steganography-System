"""Noise Perturbation and Channel Distortion Engine for Steganography Research (Phase 19).

Simulates standard real-world transmission noise, lossy compression, and image processing attacks:
1. Additive Gaussian Noise: N(mu, sigma^2)
2. Salt & Pepper (Impulse) Noise: random pixel saturation (0 or 255)
3. Lossy JPEG Recompression: DCT quantization at specified Quality factor (Q)
4. Gaussian Blur / Spatial Filtering: smoothing low-pass filter
5. Speckle / Multiplicative Noise: I' = I * (1 + N(0, sigma^2))
6. High-Contrast Difference Map: amplified visualization of residual noise
"""
import io
from typing import Optional, Tuple
import cv2
import numpy as np
from PIL import Image


class NoisePerturbationEngine:
    """Provides standard image perturbation attacks for robustness profiling."""

    @staticmethod
    def add_gaussian_noise(
        image: np.ndarray,
        mean: float = 0.0,
        std: float = 2.0,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """Applies additive Gaussian white noise to an image array.

        Args:
            image: uint8 numpy array of shape (H, W, C) or (H, W).
            mean: Mean of the Gaussian distribution (default 0.0).
            std: Standard deviation (noise intensity) in pixel units (e.g. 1.0 to 15.0).
            seed: Optional random seed for reproducible experiments.

        Returns:
            Perturbed uint8 numpy array with values strictly clipped to [0, 255].
        """
        if std <= 0.0:
            return image.copy()

        rng = np.random.default_rng(seed)
        noise = rng.normal(loc=mean, scale=std, size=image.shape)
        noisy = np.clip(image.astype(np.float64) + noise, 0.0, 255.0)
        return noisy.astype(np.uint8)

    @staticmethod
    def add_salt_and_pepper_noise(
        image: np.ndarray,
        density: float = 0.01,
        salt_vs_pepper: float = 0.5,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """Applies Salt and Pepper (impulse) noise to an image array.

        Args:
            image: uint8 numpy array of shape (H, W, C) or (H, W).
            density: Fraction of affected pixels, e.g. 0.01 = 1% of pixels.
            salt_vs_pepper: Proportion of salt (255) vs pepper (0), default 0.5.
            seed: Optional random seed for reproducibility.

        Returns:
            Perturbed uint8 numpy array.
        """
        if density <= 0.0:
            return image.copy()

        density = min(max(density, 0.0), 1.0)
        salt_vs_pepper = min(max(salt_vs_pepper, 0.0), 1.0)

        rng = np.random.default_rng(seed)
        noisy = image.copy()

        # Generate random mask across spatial coordinates (H, W)
        h, w = image.shape[:2]
        rand_matrix = rng.random((h, w))

        # Salt mask: pixels set to 255
        salt_threshold = density * salt_vs_pepper
        salt_mask = rand_matrix < salt_threshold

        # Pepper mask: pixels set to 0
        pepper_mask = (rand_matrix >= salt_threshold) & (rand_matrix < density)

        if image.ndim == 3:
            for c in range(image.shape[2]):
                noisy[salt_mask, c] = 255
                noisy[pepper_mask, c] = 0
        else:
            noisy[salt_mask] = 255
            noisy[pepper_mask] = 0

        return noisy

    @staticmethod
    def simulate_jpeg_compression(
        image: np.ndarray,
        quality: int = 85,
    ) -> np.ndarray:
        """Simulates JPEG DCT lossy compression and decompression cycle.

        Args:
            image: uint8 numpy array in RGB format.
            quality: JPEG Quality factor from 1 to 100 (default 85).

        Returns:
            uint8 numpy array reflecting JPEG quantization artifacts.
        """
        quality = int(min(max(quality, 1), 100))

        # Convert array to PIL Image in RGB mode
        if image.ndim == 2:
            pil_img = Image.fromarray(image, mode="L")
        else:
            pil_img = Image.fromarray(image, mode="RGB")

        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        reloaded = Image.open(buffer)
        if image.ndim == 3 and reloaded.mode != "RGB":
            reloaded = reloaded.convert("RGB")
        elif image.ndim == 2 and reloaded.mode != "L":
            reloaded = reloaded.convert("L")

        return np.array(reloaded, dtype=np.uint8)

    @staticmethod
    def add_gaussian_blur(
        image: np.ndarray,
        kernel_size: int = 3,
        sigma: float = 1.0,
    ) -> np.ndarray:
        """Applies spatial Gaussian smoothing filter.

        Args:
            image: uint8 numpy array.
            kernel_size: Odd integer (e.g. 3, 5, 7).
            sigma: Gaussian kernel standard deviation.

        Returns:
            Blurred uint8 numpy array.
        """
        # Ensure odd kernel size >= 3
        k = max(int(kernel_size), 3)
        if k % 2 == 0:
            k += 1

        sig = max(float(sigma), 0.1)
        return cv2.GaussianBlur(image, (k, k), sig)

    @staticmethod
    def add_speckle_noise(
        image: np.ndarray,
        std: float = 0.05,
        seed: Optional[int] = None,
    ) -> np.ndarray:
        """Applies multiplicative speckle noise: I' = I * (1 + N(0, std^2)).

        Args:
            image: uint8 numpy array.
            std: Noise standard deviation (fractional, e.g. 0.05 = 5%).
            seed: Optional random seed.

        Returns:
            Perturbed uint8 numpy array.
        """
        if std <= 0.0:
            return image.copy()

        rng = np.random.default_rng(seed)
        noise = rng.normal(0.0, std, size=image.shape)
        noisy = image.astype(np.float64) * (1.0 + noise)
        noisy = np.clip(noisy, 0.0, 255.0)
        return noisy.astype(np.uint8)

    @staticmethod
    def compute_difference_map(
        orig_image: np.ndarray,
        perturbed_image: np.ndarray,
        amplification: float = 10.0,
    ) -> np.ndarray:
        """Computes an amplified absolute difference heatmap for visual inspection.

        Args:
            orig_image: Original pristine array (uint8).
            perturbed_image: Perturbed array (uint8).
            amplification: Multiplier to make subtle pixel residuals visible (default 10.0x).

        Returns:
            uint8 RGB image representing the amplified error residual.
        """
        if orig_image.shape != perturbed_image.shape:
            raise ValueError(
                f"Image shape mismatch: {orig_image.shape} vs {perturbed_image.shape}"
            )

        diff = np.abs(orig_image.astype(np.float64) - perturbed_image.astype(np.float64))
        amplified = np.clip(diff * amplification, 0.0, 255.0).astype(np.uint8)

        # If 3 channels, return as RGB heatmap
        return amplified
