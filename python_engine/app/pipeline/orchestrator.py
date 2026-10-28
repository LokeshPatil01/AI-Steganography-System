"""One-Click End-to-End Steganography Orchestration Pipeline (Phase 18).

Integrates the full multi-tier architecture into a single unified pipeline:
1. RSA-4096-OAEP key encapsulation + AES-256-GCM authenticated payload encryption.
2. AI Random Forest spatial block classification & suitability ranking.
3. Cryptographic PRNG coordinate scattering with HKDF-SHA256.
4. Deep learning SRM-CNN steganalyzer closed-loop feedback optimization.
5. Full-reference quality metrics (PSNR, SSIM, MSE) and SHA-256 forensic hashes.
"""
from dataclasses import asdict, dataclass
import hashlib
import math
import time
from typing import Any, Dict, Optional, Tuple, Union

import cv2
import numpy as np

from app.ai.feedback_optimizer import (
    FeedbackOptimizationReport,
    FeedbackOptimizer,
)
from app.ai.steganalyzer_net import SteganalyzerDetector
from app.crypto.hybrid_cipher import HybridCipher, HybridEnvelope, HybridEncryptionError
from app.image.loader import ImageLoader
from app.image.metrics import compute_mse, compute_psnr, compute_ssim, evaluate_quality_rating
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError


@dataclass
class PipelineEncodeResult:
    """Detailed summary of the end-to-end encoding procedure."""
    stego_pixels: np.ndarray
    cover_sha256: str
    stego_sha256: str
    raw_payload_bytes: int
    hybrid_envelope_bytes: int
    security_level: str
    recipient_fingerprint: str
    stego_key_used: str
    converged: bool
    iterations_run: int
    initial_p_stego: float
    final_p_stego: float
    p_stego_reduction: float
    psnr_db: float
    ssim: float
    mse: float
    quality_rating: str
    is_imperceptible: bool
    execution_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        """Converts report fields (excluding pixel arrays) to serializable dict."""
        res = asdict(self)
        res.pop("stego_pixels", None)
        return res


@dataclass
class PipelineDecodeResult:
    """Detailed summary of the end-to-end extraction and decryption procedure."""
    decrypted_bytes: bytes
    decrypted_text: Optional[str]
    stego_sha256: str
    payload_size_bytes: int
    recipient_fingerprint: str
    authenticated: bool
    opt_iteration: int
    realloc_level: int
    execution_time_ms: int

    def to_dict(self) -> Dict[str, Any]:
        """Converts report fields to serializable dict."""
        res = asdict(self)
        res.pop("decrypted_bytes", None)
        return res


class StegoPipelineOrchestrator:
    """Unified coordinator for the multi-tier steganographic pipeline."""

    SECURITY_PROFILES = {
        "Quality": {
            "threshold": 0.45,
            "max_iterations": 3,
            "block_size": 16,
            "target_psnr": 42.0,
            "target_ssim": 0.99,
        },
        "Balanced": {
            "threshold": 0.35,
            "max_iterations": 5,
            "block_size": 16,
            "target_psnr": 40.0,
            "target_ssim": 0.98,
        },
        "Security": {
            "threshold": 0.25,
            "max_iterations": 7,
            "block_size": 16,
            "target_psnr": 38.0,
            "target_ssim": 0.97,
        },
    }

    @classmethod
    def encode_hybrid(
        cls,
        cover_pixels: np.ndarray,
        payload_data: Union[str, bytes],
        recipient_public_key_pem: str,
        stego_passphrase: Optional[str] = None,
        security_level: str = "Balanced",
        block_size: Optional[int] = None,
    ) -> PipelineEncodeResult:
        """Executes the complete one-click encoding pipeline."""
        start_time = time.time()

        if security_level not in cls.SECURITY_PROFILES:
            security_level = "Balanced"

        profile = cls.SECURITY_PROFILES[security_level]
        eff_block_size = block_size if block_size is not None else profile["block_size"]
        eff_threshold = profile["threshold"]
        eff_max_iterations = profile["max_iterations"]
        eff_target_psnr = profile["target_psnr"]
        eff_target_ssim = profile["target_ssim"]

        # 1. Normalize payload data
        if isinstance(payload_data, str):
            raw_payload_bytes = payload_data.encode("utf-8")
        else:
            raw_payload_bytes = payload_data

        if not raw_payload_bytes:
            raise ValueError("Payload cannot be empty.")

        # 2. Hybrid Asymmetric + Symmetric Encryption (RSA-4096-OAEP + AES-256-GCM)
        envelope = HybridCipher.encrypt(
            secret_message=raw_payload_bytes,
            recipient_public_key_pem=recipient_public_key_pem,
        )
        envelope_bytes = envelope.to_bytes()

        # 3. Derive or validate Stego Key
        if not stego_passphrase or not stego_passphrase.strip():
            # Derive deterministic stego key from recipient fingerprint if not explicitly supplied
            stego_key = f"STEGO-PIPELINE-{envelope.recipient_fingerprint}"
        else:
            stego_key = stego_passphrase.strip()

        # 4. Closed-Loop Adversarial Feedback Optimization Embedding
        stego_pixels, opt_report = FeedbackOptimizer.optimize(
            cover_pixels=cover_pixels,
            payload_bytes=envelope_bytes,
            stego_key=stego_key,
            block_size=eff_block_size,
            threshold=eff_threshold,
            max_iterations=eff_max_iterations,
            target_psnr=eff_target_psnr,
            target_ssim=eff_target_ssim,
        )

        # 5. Compute Forensic Hashes
        cover_hash = hashlib.sha256(cover_pixels.tobytes()).hexdigest()
        stego_hash = hashlib.sha256(stego_pixels.tobytes()).hexdigest()

        elapsed_ms = int((time.time() - start_time) * 1000)

        return PipelineEncodeResult(
            stego_pixels=stego_pixels,
            cover_sha256=cover_hash,
            stego_sha256=stego_hash,
            raw_payload_bytes=len(raw_payload_bytes),
            hybrid_envelope_bytes=len(envelope_bytes),
            security_level=security_level,
            recipient_fingerprint=envelope.recipient_fingerprint or "Unknown",
            stego_key_used=stego_key,
            converged=opt_report.converged,
            iterations_run=opt_report.iterations_run,
            initial_p_stego=opt_report.initial_p_stego,
            final_p_stego=opt_report.final_p_stego,
            p_stego_reduction=opt_report.p_stego_reduction,
            psnr_db=opt_report.final_psnr,
            ssim=opt_report.final_ssim,
            mse=opt_report.final_mse,
            quality_rating=opt_report.quality_rating,
            is_imperceptible=opt_report.is_imperceptible,
            execution_time_ms=elapsed_ms,
        )

    @classmethod
    def decode_hybrid(
        cls,
        stego_pixels: np.ndarray,
        recipient_private_key_pem: str,
        stego_passphrase: Optional[str] = None,
        private_key_passphrase: Optional[str] = None,
        block_size: int = 16,
    ) -> PipelineDecodeResult:
        """Executes the complete one-click extraction and decryption pipeline."""
        start_time = time.time()
        stego_hash = hashlib.sha256(stego_pixels.tobytes()).hexdigest()

        # If user did not supply stego_passphrase, compute fingerprint from public key derived from private key
        if not stego_passphrase or not stego_passphrase.strip():
            from app.crypto.rsa_engine import RSACipher
            pub_pem = RSACipher.get_public_key_pem(recipient_private_key_pem, passphrase=private_key_passphrase)
            pub_fp = RSACipher.get_key_fingerprint(pub_pem)
            stego_key = f"STEGO-PIPELINE-{pub_fp}"
        else:
            stego_key = stego_passphrase.strip()

        # 1. Extract raw envelope bytes using FeedbackOptimizer iteration recovery
        envelope_bytes, extract_meta = FeedbackOptimizer.extract(
            stego_pixels=stego_pixels,
            stego_key=stego_key,
            block_size=block_size,
        )

        # 2. Deserialize hybrid envelope
        envelope = HybridEnvelope.from_bytes(envelope_bytes)

        # 3. Decrypt AES key with RSA-4096-OAEP & Authenticate payload with AES-256-GCM
        decrypted_bytes = HybridCipher.decrypt(
            envelope=envelope,
            recipient_private_key_pem=recipient_private_key_pem,
        )

        # 4. Attempt UTF-8 text decoding
        try:
            decrypted_text = decrypted_bytes.decode("utf-8")
        except UnicodeDecodeError:
            decrypted_text = None

        elapsed_ms = int((time.time() - start_time) * 1000)

        return PipelineDecodeResult(
            decrypted_bytes=decrypted_bytes,
            decrypted_text=decrypted_text,
            stego_sha256=stego_hash,
            payload_size_bytes=len(decrypted_bytes),
            recipient_fingerprint=envelope.recipient_fingerprint or "Unknown",
            authenticated=True,
            opt_iteration=extract_meta.get("opt_iteration", 1),
            realloc_level=extract_meta.get("realloc_level", 0),
            execution_time_ms=elapsed_ms,
        )
