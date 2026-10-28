"""Image Quality Metrics Module for Steganography Research.

Implements standard full-reference objective quality assessment metrics:
- Mean Squared Error (MSE)
- Peak Signal-to-Noise Ratio (PSNR)
- Structural Similarity Index Measure (SSIM) based on Wang et al. (2004)
- Bit Error Rate (BER) for secret payload and image LSB bit planes
- Bits Per Pixel (BPP) payload density
- High-precision execution latency timer
- Research experiment CSV logging
"""
import csv
import math
import os
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np


class MetricsDimensionMismatchError(ValueError):
    """Raised when comparing images of different spatial dimensions or channels."""
    pass


class ExecutionTimer:
    """High-precision execution timer using monotonic time.perf_counter()."""

    def __init__(self) -> None:
        self.start_time: float = 0.0
        self.end_time: float = 0.0
        self.elapsed_ms: float = 0.0

    def __enter__(self) -> "ExecutionTimer":
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end_time = time.perf_counter()
        self.elapsed_ms = (self.end_time - self.start_time) * 1000.0


def validate_image_pair(
    img1: np.ndarray,
    img2: np.ndarray,
) -> Tuple[int, int, int]:
    """Validates that two images have identical shapes and return (height, width, channels).

    Args:
        img1: First image array (Cover).
        img2: Second image array (Stego).

    Returns:
        Tuple of (height, width, channels).

    Raises:
        MetricsDimensionMismatchError: If shapes do not match.
    """
    if img1.shape != img2.shape:
        raise MetricsDimensionMismatchError(
            f"Image dimension mismatch: img1 has shape {img1.shape}, "
            f"while img2 has shape {img2.shape}."
        )

    height = img1.shape[0]
    width = img1.shape[1]
    channels = img1.shape[2] if img1.ndim == 3 else 1
    return height, width, channels


def compute_mse(img1: np.ndarray, img2: np.ndarray) -> float:
    """Computes the overall Mean Squared Error (MSE) between two images.

    Formula:
        MSE = (1 / (H * W * C)) * sum((img1 - img2)^2)

    Args:
        img1: Original reference/cover image.
        img2: Stego/distorted image.

    Returns:
        MSE value as a non-negative float. 0.0 indicates identical images.
    """
    validate_image_pair(img1, img2)
    diff = img1.astype(np.float64) - img2.astype(np.float64)
    return float(np.mean(diff ** 2))


def compute_channel_mse(img1: np.ndarray, img2: np.ndarray) -> Dict[str, float]:
    """Computes Mean Squared Error per individual color channel.

    Args:
        img1: Original reference/cover image (H, W, 3) or (H, W).
        img2: Stego/distorted image.

    Returns:
        Dictionary mapping channel name ("R", "G", "B" or "Grayscale") to MSE float.
    """
    validate_image_pair(img1, img2)
    diff = img1.astype(np.float64) - img2.astype(np.float64)
    diff_sq = diff ** 2

    if img1.ndim == 2 or img1.shape[2] == 1:
        return {"Grayscale": float(np.mean(diff_sq))}

    channel_names = ["R", "G", "B"] if img1.shape[2] == 3 else [f"C{i}" for i in range(img1.shape[2])]
    result: Dict[str, float] = {}
    for idx, name in enumerate(channel_names):
        result[name] = float(np.mean(diff_sq[:, :, idx]))
    return result


def compute_psnr(
    img1: np.ndarray,
    img2: np.ndarray,
    max_val: float = 255.0,
) -> float:
    """Computes the Peak Signal-to-Noise Ratio (PSNR) in decibels (dB).

    Formula:
        PSNR = 10 * log10(MAX_I^2 / MSE)

    Args:
        img1: Original reference/cover image.
        img2: Stego/distorted image.
        max_val: Maximum possible pixel intensity value (default 255.0 for 8-bit).

    Returns:
        PSNR value in dB. Returns float('inf') if images are identical (MSE == 0).
    """
    mse = compute_mse(img1, img2)
    if mse == 0.0:
        return float("inf")
    return float(10.0 * np.log10((max_val ** 2) / mse))


def compute_ssim(
    img1: np.ndarray,
    img2: np.ndarray,
    window_size: int = 11,
    sigma: float = 1.5,
    k1: float = 0.01,
    k2: float = 0.03,
    l_max: float = 255.0,
) -> Dict[str, Any]:
    """Computes the Mean Structural Similarity Index Measure (MSSIM).

    Implements the standard formulation of Wang et al. (2004):
        SSIM(x, y) = ((2 * mu_x * mu_y + C1) * (2 * sigma_xy + C2)) /
                     ((mu_x^2 + mu_y^2 + C1) * (sigma_x^2 + sigma_y^2 + C2))

    Using an 11x11 circular-symmetric Gaussian weighting window (sigma=1.5).

    Args:
        img1: Original reference/cover image.
        img2: Stego/distorted image.
        window_size: Gaussian kernel window size (default 11).
        sigma: Gaussian standard deviation (default 1.5).
        k1: Algorithm constant (default 0.01).
        k2: Algorithm constant (default 0.03).
        l_max: Dynamic range of pixel values (default 255.0).

    Returns:
        Dictionary containing:
        - "ssim_mean": Overall mean SSIM across all channels in [-1.0, 1.0].
        - "ssim_channels": Dict of per-channel SSIM values.
        - "window_size": Kernel size used.
        - "sigma": Gaussian sigma used.
    """
    height, width, channels = validate_image_pair(img1, img2)

    c1 = (k1 * l_max) ** 2
    c2 = (k2 * l_max) ** 2

    # Adapt window size for very small images
    min_dim = min(height, width)
    actual_win = min(window_size, min_dim)
    if actual_win % 2 == 0:
        actual_win -= 1

    img1_float = img1.astype(np.float64)
    img2_float = img2.astype(np.float64)

    if img1_float.ndim == 2:
        img1_float = img1_float[:, :, np.newaxis]
        img2_float = img2_float[:, :, np.newaxis]

    num_channels = img1_float.shape[2]
    channel_names = ["R", "G", "B"] if num_channels == 3 else [f"C{i}" for i in range(num_channels)]
    channel_ssims: Dict[str, float] = {}

    for c in range(num_channels):
        i1 = img1_float[:, :, c]
        i2 = img2_float[:, :, c]

        if actual_win >= 3:
            # Gaussian weighted local statistics
            kernel = (actual_win, actual_win)
            mu1 = cv2.GaussianBlur(i1, kernel, sigma, borderType=cv2.BORDER_REFLECT)
            mu2 = cv2.GaussianBlur(i2, kernel, sigma, borderType=cv2.BORDER_REFLECT)

            mu1_sq = mu1 ** 2
            mu2_sq = mu2 ** 2
            mu1_mu2 = mu1 * mu2

            sigma1_sq = cv2.GaussianBlur(i1 ** 2, kernel, sigma, borderType=cv2.BORDER_REFLECT) - mu1_sq
            sigma2_sq = cv2.GaussianBlur(i2 ** 2, kernel, sigma, borderType=cv2.BORDER_REFLECT) - mu2_sq
            sigma12 = cv2.GaussianBlur(i1 * i2, kernel, sigma, borderType=cv2.BORDER_REFLECT) - mu1_mu2
        else:
            # Fallback for 1-2 pixel micro images: global scalar statistics
            mu1 = float(np.mean(i1))
            mu2 = float(np.mean(i2))
            mu1_sq = mu1 ** 2
            mu2_sq = mu2 ** 2
            mu1_mu2 = mu1 * mu2

            sigma1_sq = float(np.var(i1))
            sigma2_sq = float(np.var(i2))
            sigma12 = float(np.mean((i1 - mu1) * (i2 - mu2)))

        numerator = (2.0 * mu1_mu2 + c1) * (2.0 * sigma12 + c2)
        denominator = (mu1_sq + mu2_sq + c1) * (sigma1_sq + sigma2_sq + c2)

        ssim_map = numerator / denominator
        mssim_val = float(np.mean(ssim_map))
        channel_ssims[channel_names[c]] = mssim_val

    mean_ssim = float(np.mean(list(channel_ssims.values())))

    return {
        "ssim_mean": mean_ssim,
        "ssim_channels": channel_ssims,
        "window_size": actual_win,
        "sigma": sigma,
    }


def compute_payload_ber(
    original: Union[bytes, bytearray, str],
    recovered: Union[bytes, bytearray, str],
) -> float:
    """Computes the Bit Error Rate (BER) between original and recovered payload bits.

    Formula:
        BER = mismatched_bits / total_bits
        where total_bits = 8 * max(len(original), len(recovered))

    Args:
        original: Original secret message payload (bytes or str).
        recovered: Extracted payload after steganographic recovery.

    Returns:
        BER value in range [0.0, 1.0]. 0.0 denotes 100% perfect lossless recovery.
    """
    b1 = original.encode("utf-8") if isinstance(original, str) else bytes(original)
    b2 = recovered.encode("utf-8") if isinstance(recovered, str) else bytes(recovered)

    if len(b1) == 0 and len(b2) == 0:
        return 0.0

    min_len = min(len(b1), len(b2))
    max_len = max(len(b1), len(b2))

    bit_errors = 0
    for i in range(min_len):
        xor_val = b1[i] ^ b2[i]
        bit_errors += bin(xor_val).count("1")

    # Length discrepancies count as full 8-bit mismatches per missing byte
    bit_errors += (max_len - min_len) * 8
    total_bits = max_len * 8

    return float(bit_errors / total_bits)


def compute_image_lsb_ber(img1: np.ndarray, img2: np.ndarray) -> float:
    """Computes the Bit Error Rate strictly across the least significant bit (LSB) plane.

    Evaluates the fraction of pixel LSBs altered by steganographic embedding.

    Args:
        img1: Original reference/cover image.
        img2: Stego image.

    Returns:
        LSB BER float in range [0.0, 1.0].
    """
    validate_image_pair(img1, img2)
    lsb1 = img1 & 1
    lsb2 = img2 & 1
    mismatches = int(np.count_nonzero(lsb1 != lsb2))
    total_lsb_bits = img1.size
    return float(mismatches / total_lsb_bits) if total_lsb_bits > 0 else 0.0


def compute_bpp(payload_bytes: int, width: int, height: int) -> float:
    """Calculates embedding payload density in Bits Per Pixel (BPP).

    Formula:
        BPP = (payload_bytes * 8) / (width * height)

    Args:
        payload_bytes: Embedded payload size in bytes.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        Embedding density in bits per pixel (BPP).
    """
    total_pixels = width * height
    if total_pixels <= 0:
        return 0.0
    return float((payload_bytes * 8.0) / total_pixels)


def evaluate_quality_rating(psnr: float, ssim: float) -> Tuple[str, bool]:
    """Evaluates the perceptual imperceptibility and quality rating tier.

    Categories based on academic steganography thresholds:
    - EXCELLENT: PSNR >= 50 dB and SSIM >= 0.995 (Indistinguishable)
    - GOOD: PSNR >= 40 dB and SSIM >= 0.980 (Imperceptible to human vision)
    - ACCEPTABLE: PSNR >= 35 dB and SSIM >= 0.950 (Minor artifacts)
    - DEGRADED: PSNR < 35 dB or SSIM < 0.950 (Visible distortion)

    Returns:
        Tuple of (rating: str, is_imperceptible: bool).
    """
    if psnr == float("inf") or (psnr >= 50.0 and ssim >= 0.995):
        return "EXCELLENT", True
    if psnr >= 40.0 and ssim >= 0.980:
        return "GOOD", True
    if psnr >= 35.0 and ssim >= 0.950:
        return "ACCEPTABLE", False
    return "DEGRADED", False


@dataclass
class QualityMetricsReport:
    """Consolidated steganographic quality and benchmarking report."""
    mse: float
    mse_channels: Dict[str, float]
    psnr_db: float
    psnr_display: str
    ssim: float
    ssim_channels: Dict[str, float]
    image_lsb_ber: float
    payload_ber: Optional[float]
    payload_bytes: Optional[int]
    bpp: Optional[float]
    latency_ms: Optional[float]
    is_imperceptible: bool
    quality_rating: str
    width: int
    height: int
    channels: int
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        """Converts report to a JSON-serializable dictionary."""
        d = asdict(self)
        # Handle float('inf') for JSON compliance
        if math.isinf(self.psnr_db):
            d["psnr_db"] = 100.0  # Capped benchmark representation
            d["is_psnr_infinite"] = True
        else:
            d["psnr_db"] = round(self.psnr_db, 4)
            d["is_psnr_infinite"] = False

        d["mse"] = round(self.mse, 6)
        d["ssim"] = round(self.ssim, 6)
        d["image_lsb_ber"] = round(self.image_lsb_ber, 6)
        if self.payload_ber is not None:
            d["payload_ber"] = round(self.payload_ber, 6)
        if self.bpp is not None:
            d["bpp"] = round(self.bpp, 6)
        if self.latency_ms is not None:
            d["latency_ms"] = round(self.latency_ms, 2)
        return d


def compute_all_metrics(
    cover_img: np.ndarray,
    stego_img: np.ndarray,
    original_payload: Optional[Union[bytes, str]] = None,
    recovered_payload: Optional[Union[bytes, str]] = None,
    payload_bytes: Optional[int] = None,
    latency_ms: Optional[float] = None,
) -> QualityMetricsReport:
    """Computes a complete battery of quality and fidelity metrics.

    Args:
        cover_img: Original reference cover image.
        stego_img: Resulting stego image.
        original_payload: Embedded payload (optional for BER).
        recovered_payload: Recovered payload (optional for BER).
        payload_bytes: Total payload size in bytes (optional for BPP).
        latency_ms: Measured elapsed time in milliseconds.

    Returns:
        QualityMetricsReport instance containing all evaluations.
    """
    height, width, channels = validate_image_pair(cover_img, stego_img)

    mse = compute_mse(cover_img, stego_img)
    mse_channels = compute_channel_mse(cover_img, stego_img)
    psnr = compute_psnr(cover_img, stego_img)

    if math.isinf(psnr):
        psnr_display = "Infinity dB (Identical)"
    else:
        psnr_display = f"{psnr:.2f} dB"

    ssim_result = compute_ssim(cover_img, stego_img)
    mean_ssim = ssim_result["ssim_mean"]
    ssim_channels = ssim_result["ssim_channels"]

    image_lsb_ber = compute_image_lsb_ber(cover_img, stego_img)

    payload_ber = None
    if original_payload is not None and recovered_payload is not None:
        payload_ber = compute_payload_ber(original_payload, recovered_payload)

    bpp = None
    if payload_bytes is not None:
        bpp = compute_bpp(payload_bytes, width, height)

    quality_rating, is_imperceptible = evaluate_quality_rating(psnr, mean_ssim)
    timestamp = datetime.now(timezone.utc).isoformat()

    return QualityMetricsReport(
        mse=mse,
        mse_channels=mse_channels,
        psnr_db=psnr,
        psnr_display=psnr_display,
        ssim=mean_ssim,
        ssim_channels=ssim_channels,
        image_lsb_ber=image_lsb_ber,
        payload_ber=payload_ber,
        payload_bytes=payload_bytes,
        bpp=bpp,
        latency_ms=latency_ms,
        is_imperceptible=is_imperceptible,
        quality_rating=quality_rating,
        width=width,
        height=height,
        channels=channels,
        timestamp=timestamp,
    )


def record_metrics_to_csv(
    report: QualityMetricsReport,
    output_path: str = "results/tables/quality_metrics.csv",
    method_name: str = "Baseline_LSB",
) -> str:
    """Appends experiment quality metrics to a structured CSV file for research logs.

    Args:
        report: Computed QualityMetricsReport.
        output_path: Target CSV file path.
        method_name: Steganography method tag.

    Returns:
        Absolute path to the updated CSV file.
    """
    # Ensure directory exists
    dir_name = os.path.dirname(output_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    file_exists = os.path.exists(output_path)

    fieldnames = [
        "timestamp",
        "method",
        "dimensions",
        "mse",
        "psnr_db",
        "ssim",
        "image_lsb_ber",
        "payload_bytes",
        "bpp",
        "payload_ber",
        "latency_ms",
        "is_imperceptible",
        "quality_rating",
    ]

    with open(output_path, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()

        psnr_val = 100.0 if math.isinf(report.psnr_db) else round(report.psnr_db, 4)

        writer.writerow({
            "timestamp": report.timestamp,
            "method": method_name,
            "dimensions": f"{report.width}x{report.height}x{report.channels}",
            "mse": round(report.mse, 6),
            "psnr_db": psnr_val,
            "ssim": round(report.ssim, 6),
            "image_lsb_ber": round(report.image_lsb_ber, 6),
            "payload_bytes": report.payload_bytes if report.payload_bytes is not None else "",
            "bpp": round(report.bpp, 6) if report.bpp is not None else "",
            "payload_ber": round(report.payload_ber, 6) if report.payload_ber is not None else "",
            "latency_ms": round(report.latency_ms, 2) if report.latency_ms is not None else "",
            "is_imperceptible": report.is_imperceptible,
            "quality_rating": report.quality_rating,
        })

    return os.path.abspath(output_path)
