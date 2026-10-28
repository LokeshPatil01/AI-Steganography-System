"""Forensic Robustness and Channel Distortion Profiler (Phase 19).

Systematically evaluates steganographic payload survivability, image fidelity degradation,
spatial LSB alteration rates, and cryptographic tamper detection across diverse noise
and compression perturbation attacks.
"""
from dataclasses import asdict, dataclass
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np

from app.image.metrics import (
    compute_mse,
    compute_payload_ber,
    compute_psnr,
    compute_ssim,
    evaluate_quality_rating,
)
from app.image.perturbation import NoisePerturbationEngine
from app.pipeline.orchestrator import StegoPipelineOrchestrator
from app.steganography.adaptive_rules import AdaptiveRulesLSB
from app.steganography.ai_stego import AiAdaptiveLSB
from app.steganography.baseline_lsb import (
    BaselineLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
)
from app.steganography.payload_packer import PayloadCorruptedError
from app.steganography.scatter_stego import KeyScatteredAiLSB


@dataclass
class RobustnessReport:
    """Detailed forensic evaluation report for a perturbation attack."""
    attack_type: str
    attack_params: Dict[str, Any]
    attack_intensity: float
    degraded_psnr_db: float
    degraded_ssim: float
    degraded_mse: float
    cover_psnr_db: Optional[float]
    cover_ssim: Optional[float]
    lsb_ber: float
    quality_rating: str
    is_imperceptible: bool
    extraction_attempted: bool
    extraction_succeeded: bool
    survival_status: str  # "INTACT", "TAMPER_DETECTED", "CORRUPTED_CRC", "FATAL_DESYNC", "NOT_ATTEMPTED"
    tamper_detected: bool
    integrity_message: str
    recovered_payload_size: int
    payload_ber: Optional[float]
    execution_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        """Converts the dataclass report to a JSON-serializable dictionary."""
        return asdict(self)


class RobustnessProfiler:
    """Profiles steganographic resilience and cryptographic tamper detection."""

    @staticmethod
    def compute_lsb_ber(orig_img: np.ndarray, perturbed_img: np.ndarray) -> float:
        """Computes the bit error rate of the least significant bit plane."""
        orig_lsb = orig_img & 1
        pert_lsb = perturbed_img & 1
        total_bits = orig_lsb.size
        if total_bits == 0:
            return 0.0
        flipped = np.count_nonzero(orig_lsb != pert_lsb)
        return float(flipped / total_bits)

    @classmethod
    def apply_attack(
        cls,
        image: np.ndarray,
        attack_type: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Tuple[np.ndarray, float]:
        """Applies a selected perturbation attack using NoisePerturbationEngine.

        Returns:
            Tuple of (perturbed_image_array, intensity_scalar).
        """
        params = params or {}
        atk = attack_type.lower().strip()

        if atk in ("gaussian", "gaussian_noise"):
            std = float(params.get("std", 2.0))
            mean = float(params.get("mean", 0.0))
            seed = params.get("seed", None)
            noisy = NoisePerturbationEngine.add_gaussian_noise(image, mean=mean, std=std, seed=seed)
            return noisy, std

        elif atk in ("salt_pepper", "salt_and_pepper", "impulse"):
            density = float(params.get("density", 0.01))
            salt_vs_pepper = float(params.get("salt_vs_pepper", 0.5))
            seed = params.get("seed", None)
            noisy = NoisePerturbationEngine.add_salt_and_pepper_noise(
                image, density=density, salt_vs_pepper=salt_vs_pepper, seed=seed
            )
            return noisy, density

        elif atk in ("jpeg", "jpeg_compression"):
            quality = int(params.get("quality", 85))
            noisy = NoisePerturbationEngine.simulate_jpeg_compression(image, quality=quality)
            return noisy, float(quality)

        elif atk in ("blur", "gaussian_blur"):
            ksize = int(params.get("kernel_size", 3))
            sigma = float(params.get("sigma", 1.0))
            noisy = NoisePerturbationEngine.add_gaussian_blur(image, kernel_size=ksize, sigma=sigma)
            return noisy, sigma

        elif atk in ("speckle", "multiplicative"):
            std = float(params.get("std", 0.05))
            seed = params.get("seed", None)
            noisy = NoisePerturbationEngine.add_speckle_noise(image, std=std, seed=seed)
            return noisy, std

        else:
            raise ValueError(f"Unsupported attack type '{attack_type}'.")

    @classmethod
    def attempt_extraction(
        cls,
        stego_pixels: np.ndarray,
        method: str,
        credentials: Optional[Dict[str, Any]] = None,
        block_size: int = 16,
    ) -> Tuple[bool, Optional[bytes], str, bool, str]:
        """Attempts to extract and verify payload from candidate stego pixels.

        Returns:
            Tuple of:
            - extraction_succeeded (bool)
            - recovered_bytes (Optional[bytes])
            - survival_status (str: INTACT, TAMPER_DETECTED, CORRUPTED_CRC, FATAL_DESYNC)
            - tamper_detected (bool)
            - integrity_message (str)
        """
        credentials = credentials or {}
        method_norm = method.lower().strip()

        try:
            if method_norm in ("scatter", "prng_scatter"):
                stego_key = credentials.get("stego_key", "")
                recovered_bytes, meta = KeyScatteredAiLSB.extract(
                    stego_pixels=stego_pixels,
                    stego_key=stego_key,
                    block_size=block_size,
                )
                return True, recovered_bytes, "INTACT", False, "Payload recovered with verified CRC-32 integrity."

            elif method_norm in ("ai_adaptive", "ai"):
                recovered_bytes, meta = AiAdaptiveLSB.extract(
                    stego_pixels=stego_pixels,
                    block_size=block_size,
                )
                return True, recovered_bytes, "INTACT", False, "AI-adaptive payload recovered with verified CRC-32."

            elif method_norm in ("adaptive", "rule"):
                recovered_bytes, meta = AdaptiveRulesLSB.extract(
                    stego_pixels=stego_pixels,
                    block_size=block_size,
                )
                return True, recovered_bytes, "INTACT", False, "Rule-adaptive payload recovered with verified CRC-32."

            elif method_norm in ("baseline", "lsb"):
                recovered_bytes, meta = BaselineLSB.extract(stego_pixels=stego_pixels)
                return True, recovered_bytes, "INTACT", False, "Baseline LSB payload recovered with verified CRC-32."

            elif method_norm in ("pipeline_hybrid", "hybrid", "pipeline"):
                priv_key_pem = credentials.get("recipient_private_key_pem", "")
                stego_passphrase = credentials.get("stego_passphrase", "")
                if not priv_key_pem:
                    return (
                        False,
                        None,
                        "NOT_ATTEMPTED",
                        False,
                        "Recipient private key is required for hybrid pipeline extraction.",
                    )

                result = StegoPipelineOrchestrator.decode_hybrid(
                    stego_pixels=stego_pixels,
                    recipient_private_key_pem=priv_key_pem,
                    stego_passphrase=stego_passphrase,
                    block_size=block_size,
                )
                return True, result.decrypted_bytes, "INTACT", False, "Authenticated RSA+AES-GCM payload verified and recovered losslessly."

            else:
                return (
                    False,
                    None,
                    "NOT_ATTEMPTED",
                    False,
                    f"Unknown extraction method: '{method}'.",
                )

        except PayloadCorruptedError as e:
            err_msg = str(e)
            is_tamper = "tamper" in err_msg.lower() or "tag" in err_msg.lower() or "integrity" in err_msg.lower() or "crc" in err_msg.lower()
            status = "TAMPER_DETECTED" if is_tamper else "CORRUPTED_CRC"
            return (
                False,
                None,
                status,
                True,
                f"Tamper detected: {err_msg}",
            )

        except NoStegoPayloadFoundError as e:
            return (
                False,
                None,
                "FATAL_DESYNC",
                True,
                f"Payload synchronization destroyed: {e}",
            )

        except Exception as e:
            return (
                False,
                None,
                "FATAL_DESYNC",
                True,
                f"Extraction failed under attack: {type(e).__name__} - {e}",
            )

    @classmethod
    def profile_attack(
        cls,
        stego_img: np.ndarray,
        attack_type: str,
        attack_params: Optional[Dict[str, Any]] = None,
        cover_img: Optional[np.ndarray] = None,
        original_payload: Optional[Union[str, bytes]] = None,
        extraction_method: Optional[str] = "scatter",
        credentials: Optional[Dict[str, Any]] = None,
        block_size: int = 16,
    ) -> Tuple[np.ndarray, RobustnessReport]:
        """Runs a complete robustness analysis for a given attack.

        Returns:
            Tuple of (perturbed_image_array, RobustnessReport).
        """
        start_time = time.perf_counter()
        attack_params = attack_params or {}

        # 1. Apply perturbation attack
        perturbed_img, intensity = cls.apply_attack(stego_img, attack_type, attack_params)

        # 2. Image Degradation Metrics (Stego vs Perturbed)
        deg_mse = compute_mse(stego_img, perturbed_img)
        deg_psnr = compute_psnr(stego_img, perturbed_img)
        deg_ssim_res = compute_ssim(stego_img, perturbed_img)
        deg_ssim = float(deg_ssim_res["ssim_mean"])
        quality_rating, is_imperceptible = evaluate_quality_rating(deg_psnr, deg_ssim)

        # 3. Spatial LSB alteration rate
        lsb_ber = cls.compute_lsb_ber(stego_img, perturbed_img)

        # 4. Cover image comparison (if provided)
        cov_psnr = None
        cov_ssim = None
        if cover_img is not None and cover_img.shape == perturbed_img.shape:
            cov_psnr = compute_psnr(cover_img, perturbed_img)
            cov_ssim_res = compute_ssim(cover_img, perturbed_img)
            cov_ssim = float(cov_ssim_res["ssim_mean"])

        # 5. Extraction & Cryptographic Integrity Check
        extract_attempted = extraction_method is not None and extraction_method.strip() != ""
        extract_succeeded = False
        survival_status = "NOT_ATTEMPTED"
        tamper_detected = False
        integrity_msg = "Extraction was not requested."
        rec_size = 0
        payload_ber = None

        if extract_attempted:
            (
                extract_succeeded,
                rec_bytes,
                survival_status,
                tamper_detected,
                integrity_msg,
            ) = cls.attempt_extraction(
                stego_pixels=perturbed_img,
                method=extraction_method,
                credentials=credentials,
                block_size=block_size,
            )

            if extract_succeeded and rec_bytes is not None:
                rec_size = len(rec_bytes)
                if original_payload is not None:
                    orig_bytes = (
                        original_payload.encode("utf-8")
                        if isinstance(original_payload, str)
                        else original_payload
                    )
                    payload_ber = compute_payload_ber(orig_bytes, rec_bytes)
            else:
                if original_payload is not None:
                    payload_ber = 1.0  # Total loss

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        report = RobustnessReport(
            attack_type=attack_type,
            attack_params=attack_params,
            attack_intensity=float(intensity),
            degraded_psnr_db=round(float(deg_psnr), 2),
            degraded_ssim=round(float(deg_ssim), 4),
            degraded_mse=round(float(deg_mse), 4),
            cover_psnr_db=round(float(cov_psnr), 2) if cov_psnr is not None else None,
            cover_ssim=round(float(cov_ssim), 4) if cov_ssim is not None else None,
            lsb_ber=round(float(lsb_ber), 6),
            quality_rating=quality_rating,
            is_imperceptible=is_imperceptible,
            extraction_attempted=extract_attempted,
            extraction_succeeded=extract_succeeded,
            survival_status=survival_status,
            tamper_detected=tamper_detected,
            integrity_message=integrity_msg,
            recovered_payload_size=rec_size,
            payload_ber=round(float(payload_ber), 6) if payload_ber is not None else None,
            execution_time_ms=elapsed_ms,
        )

        return perturbed_img, report

    @classmethod
    def run_sweep(
        cls,
        stego_img: np.ndarray,
        attack_type: str,
        intensities: Optional[List[float]] = None,
        extraction_method: Optional[str] = "scatter",
        credentials: Optional[Dict[str, Any]] = None,
        block_size: int = 16,
        original_payload: Optional[Union[str, bytes]] = None,
    ) -> List[Dict[str, Any]]:
        """Executes a multi-point degradation sweep across parameter levels."""
        atk = attack_type.lower().strip()

        # Provide research-standard defaults if none specified
        if intensities is None or len(intensities) == 0:
            if atk in ("gaussian", "gaussian_noise"):
                intensities = [0.5, 1.0, 2.0, 3.0, 5.0]
            elif atk in ("salt_pepper", "impulse"):
                intensities = [0.001, 0.005, 0.01, 0.02, 0.05]
            elif atk in ("jpeg", "jpeg_compression"):
                intensities = [95.0, 90.0, 85.0, 75.0, 50.0]
            elif atk in ("blur", "gaussian_blur"):
                intensities = [0.5, 1.0, 1.5, 2.0]
            elif atk in ("speckle", "multiplicative"):
                intensities = [0.01, 0.03, 0.05, 0.10, 0.15]
            else:
                intensities = [1.0, 2.0, 3.0]

        results = []
        for val in intensities:
            params: Dict[str, Any] = {}
            if atk in ("gaussian", "gaussian_noise", "speckle"):
                params["std"] = float(val)
            elif atk in ("salt_pepper", "impulse"):
                params["density"] = float(val)
            elif atk in ("jpeg", "jpeg_compression"):
                params["quality"] = int(val)
            elif atk in ("blur", "gaussian_blur"):
                params["sigma"] = float(val)

            _, rep = cls.profile_attack(
                stego_img=stego_img,
                attack_type=atk,
                attack_params=params,
                original_payload=original_payload,
                extraction_method=extraction_method,
                credentials=credentials,
                block_size=block_size,
            )
            results.append(rep.to_dict())

        return results
