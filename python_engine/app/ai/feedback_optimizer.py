"""Feedback-Driven Adaptive Steganography Optimization Engine (Phase 17).

Implements the multi-objective adversarial optimization loop (PROJECT_ARCHITECTURE.md Section 8.3):
1. Evaluates candidate stego images against the PyTorch Steganalyzer CNN (Phase 16).
2. If P(stego) >= tau (default 0.35) or PSNR < 40 dB:
   - Identifies candidate blocks exhibiting elevated Spatial Rich Model (SRM) residual energy.
   - Dynamically reallocates payload bits away from marginal/culprit blocks into higher-texture
     regions with superior visual & statistical masking (Class 2 blocks).
   - Mutates PRNG scattering distribution to break up detectable spatial noise clusters.
3. Repeats up to k_max = 5 iterations until equilibrium (P(stego) < tau and PSNR >= 40 dB).
4. Employs a multi-objective loss function J to select the optimal Pareto candidate across iterations:
   J = P(stego) + 0.05 * max(0, 40 - PSNR) + 1.0 * max(0, 0.98 - SSIM) + 0.1 * ResidualEnergy
5. Supports self-synchronizing blind extraction with wire frame b'STEGFDB1' and CRC-32 integrity.
"""
from dataclasses import asdict, dataclass
import math
import struct
import time
from typing import Any, Dict, List, Optional, Tuple, Union
import zlib

import cv2
import numpy as np

from app.ai.region_classifier import CLASS_NAMES, RegionClassifier
from app.ai.steganalyzer_net import SteganalyzerDetector, StegoDetectionResult
from app.crypto.scatter_prng import CryptographicPermuter, PrngKeyDeriver
from app.image.metrics import compute_mse, compute_psnr, compute_ssim, evaluate_quality_rating
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError

DEFAULT_BLOCK_SIZE = 16
DEFAULT_DECISION_THRESHOLD = 0.35
DEFAULT_MAX_ITERATIONS = 5
DEFAULT_TARGET_PSNR = 40.0
DEFAULT_TARGET_SSIM = 0.98


class FeedbackPayloadPacker:
    """Binary wire framing with iteration metadata for feedback-optimized steganography."""

    MAGIC_HEADER = b"STEGFDB1"
    HEADER_SIZE_BYTES = 20  # 8 magic + 1 iter + 1 realloc + 2 reserved + 4 len + 4 crc32

    @classmethod
    def pack(cls, payload_data: bytes, opt_iteration: int = 1, realloc_level: int = 0) -> bytes:
        """Packs payload into feedback wire frame:
        [8 bytes: Magic b'STEGFDB1']
        [1 byte:  Optimization iteration k in 1..5]
        [1 byte:  Reallocation level in 0..5]
        [2 bytes: Reserved padding b'\\x00\\x00']
        [4 bytes: Payload length (big-endian uint32)]
        [4 bytes: CRC-32 checksum (big-endian uint32)]
        [N bytes: Raw payload data]
        """
        length = len(payload_data)
        crc = zlib.crc32(payload_data) & 0xFFFFFFFF
        header = (
            cls.MAGIC_HEADER
            + struct.pack(">BBHII", opt_iteration, realloc_level, 0, length, crc)
        )
        return header + payload_data

    @classmethod
    def unpack_header(cls, frame_bytes: bytes) -> Tuple[int, int, int, int]:
        """Extracts (payload_length, expected_crc, opt_iteration, realloc_level)."""
        if len(frame_bytes) < cls.HEADER_SIZE_BYTES:
            raise NoStegoPayloadFoundError(
                f"Insufficient data to unpack feedback header: got {len(frame_bytes)} bytes, expected {cls.HEADER_SIZE_BYTES}."
            )

        magic = frame_bytes[:8]
        if magic != cls.MAGIC_HEADER:
            raise NoStegoPayloadFoundError(
                f"Feedback magic header mismatch: expected {cls.MAGIC_HEADER}, got {magic}. "
                "Not a feedback-optimized stego image or incorrect key."
            )

        opt_iter, realloc_lvl, _, payload_len, expected_crc = struct.unpack(
            ">BBHII", frame_bytes[8:20]
        )
        return payload_len, expected_crc, opt_iter, realloc_lvl


@dataclass
class IterationHistory:
    """Log record of a single optimization iteration."""
    iteration: int
    p_stego: float
    is_detected: bool
    psnr: float
    ssim: float
    mse: float
    residual_energy: float
    objective_loss: float
    action_taken: str
    textured_blocks_used: int
    candidate_pool_size: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackOptimizationReport:
    """Comprehensive summary of the feedback optimization run."""
    converged: bool
    iterations_run: int
    initial_p_stego: float
    final_p_stego: float
    p_stego_reduction: float
    initial_psnr: float
    final_psnr: float
    psnr_improvement: float
    final_ssim: float
    final_mse: float
    decision_threshold: float
    quality_rating: str
    is_imperceptible: bool
    best_iteration_selected: int
    key_fingerprint: str
    payload_bytes: int
    duration_seconds: float
    history: List[IterationHistory]

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["history"] = [h.to_dict() if isinstance(h, IterationHistory) else h for h in self.history]
        return d


class FeedbackOptimizer:
    """Multi-objective iterative feedback controller for adversarial steganography."""

    DEFAULT_THRESHOLD = DEFAULT_DECISION_THRESHOLD
    DEFAULT_MAX_ITERATIONS = DEFAULT_MAX_ITERATIONS

    @staticmethod
    def calculate_objective_loss(
        p_stego: float,
        psnr_val: float,
        ssim_val: float,
        residual_energy: float,
        target_psnr: float = DEFAULT_TARGET_PSNR,
        target_ssim: float = DEFAULT_TARGET_SSIM,
    ) -> float:
        """Computes the scalar multi-objective loss J(k).

        Lower is strictly superior.
        J = P(stego) + 0.05 * max(0, target_psnr - PSNR) + 1.0 * max(0, target_ssim - SSIM) + 0.1 * ResidualEnergy
        """
        psnr_penalty = 0.05 * max(0.0, target_psnr - psnr_val) if not math.isinf(psnr_val) else 0.0
        ssim_penalty = 1.0 * max(0.0, target_ssim - ssim_val)
        res_penalty = 0.10 * residual_energy
        loss = p_stego + psnr_penalty + ssim_penalty + res_penalty
        return round(float(loss), 5)

    @classmethod
    def _embed_candidate(
        cls,
        cover_pixels: np.ndarray,
        payload_bytes: bytes,
        stego_key: str,
        ranked_blocks: List[Any],
        block_size: int,
        iteration_k: int,
        realloc_level: int,
    ) -> Tuple[np.ndarray, int, int]:
        """Embeds payload into selected candidate blocks for iteration k."""
        stego = cover_pixels.copy()
        h, w, c = stego.shape

        packed_frame = FeedbackPayloadPacker.pack(
            payload_bytes, opt_iteration=iteration_k, realloc_level=realloc_level
        )
        frame_bit_len = len(packed_frame) * 8
        bits_per_block = block_size * block_size * c
        required_blocks = math.ceil(frame_bit_len / bits_per_block)

        # Candidate pool filtering based on realloc_level
        # Level 0: All textured blocks (Class 1 & 2)
        # Level 1+: Progressively raise suitability threshold to exclude borderline textured blocks
        if realloc_level == 0:
            candidates = [b for b in ranked_blocks if b.predicted_class != 0]
        else:
            # Raise cutoff by realloc_level * 0.10, but ensure at least required_blocks remain
            high_texture = [b for b in ranked_blocks if b.predicted_class == 2]
            medium_texture = [b for b in ranked_blocks if b.predicted_class == 1]
            # Discard lowest-scoring fraction of medium texture blocks
            keep_count = max(0, len(medium_texture) - (realloc_level * max(1, len(medium_texture) // 4)))
            filtered_medium = medium_texture[:keep_count]
            candidates = high_texture + filtered_medium

        if required_blocks > len(candidates):
            # Fall back to entire ranked pool if capacity is tight
            candidates = ranked_blocks

        # Distinct domain salt per iteration
        domain_salt = f"STEGO-FEEDBACK-V17-K{iteration_k}-R{realloc_level}".encode("utf-8")
        key_seed = PrngKeyDeriver.derive_seed(stego_key, salt=domain_salt)
        scattered_blocks = CryptographicPermuter.permute(candidates, key_seed)

        bit_stream = np.unpackbits(np.frombuffer(packed_frame, dtype=np.uint8))
        bit_idx = 0
        total_bits = len(bit_stream)
        blocks_used = 0

        for b_info in scattered_blocks:
            if bit_idx >= total_bits:
                break

            blocks_used += 1
            y0, y1 = b_info.y_start, b_info.y_end
            x0, x1 = b_info.x_start, b_info.x_end

            block = stego[y0:y1, x0:x1, :]

            for y in range(block_size):
                for x in range(block_size):
                    for ch in range(c):
                        if bit_idx < total_bits:
                            bit = bit_stream[bit_idx]
                            block[y, x, ch] = (block[y, x, ch] & 0xFE) | bit
                            bit_idx += 1
                        else:
                            break
                    if bit_idx >= total_bits:
                        break
                if bit_idx >= total_bits:
                    break

            stego[y0:y1, x0:x1, :] = block

        return stego, blocks_used, len(candidates)

    @classmethod
    def _rank_blocks(cls, pixels: np.ndarray, block_size: int) -> List[Any]:
        from app.steganography.ai_stego import AiAdaptiveLSB
        return AiAdaptiveLSB.rank_blocks_with_ai(pixels, block_size)

    @classmethod
    def optimize(
        cls,
        cover_pixels: np.ndarray,
        payload_bytes: bytes,
        stego_key: str,
        block_size: int = DEFAULT_BLOCK_SIZE,
        threshold: float = DEFAULT_THRESHOLD,
        max_iterations: int = DEFAULT_MAX_ITERATIONS,
        target_psnr: float = DEFAULT_TARGET_PSNR,
        target_ssim: float = DEFAULT_TARGET_SSIM,
    ) -> Tuple[np.ndarray, FeedbackOptimizationReport]:
        """Executes the closed-loop feedback optimization procedure."""
        start_time = time.time()
        detector = SteganalyzerDetector.get_instance()
        key_fp = PrngKeyDeriver.compute_key_fingerprint(stego_key)

        # 1. AI Region Ranking on Cover (MSB-invariant)
        ranked_blocks = cls._rank_blocks(cover_pixels, block_size)
        total_blocks = len(ranked_blocks)

        packed_probe = FeedbackPayloadPacker.pack(payload_bytes, opt_iteration=1, realloc_level=0)
        total_frame_bits = len(packed_probe) * 8
        total_capacity_bits = total_blocks * block_size * block_size * cover_pixels.shape[2]

        if total_frame_bits > total_capacity_bits:
            raise CapacityExceededError(
                f"Payload requires {total_frame_bits} bits, exceeding maximum image capacity of {total_capacity_bits} bits."
            )

        candidates_evaluated: List[Dict[str, Any]] = []
        history: List[IterationHistory] = []
        converged = False

        for k in range(1, max_iterations + 1):
            realloc_level = k - 1
            action = (
                "Initial AI-Scattered LSB Embedding"
                if k == 1
                else f"Iteration {k}: Throttled marginal blocks (Level {realloc_level}) & permuted orthogonal coordinates"
            )

            # Generate candidate k
            cand_pixels, blocks_used, pool_size = cls._embed_candidate(
                cover_pixels=cover_pixels,
                payload_bytes=payload_bytes,
                stego_key=stego_key,
                ranked_blocks=ranked_blocks,
                block_size=block_size,
                iteration_k=k,
                realloc_level=realloc_level,
            )

            # Query Adversarial Steganalyzer CNN
            detection_res: StegoDetectionResult = detector.predict(cand_pixels, threshold=threshold)
            p_stego = detection_res.stego_probability
            res_energy = detection_res.residual_energy

            # Compute Objective Quality Metrics
            mse_val = compute_mse(cover_pixels, cand_pixels)
            psnr_val = compute_psnr(cover_pixels, cand_pixels)
            ssim_res = compute_ssim(cover_pixels, cand_pixels)
            ssim_val = ssim_res["ssim_mean"]

            # Compute Multi-Objective Loss J
            loss = cls.calculate_objective_loss(
                p_stego=p_stego,
                psnr_val=psnr_val,
                ssim_val=ssim_val,
                residual_energy=res_energy,
                target_psnr=target_psnr,
                target_ssim=target_ssim,
            )

            stat = IterationHistory(
                iteration=k,
                p_stego=round(p_stego, 4),
                is_detected=bool(p_stego >= threshold),
                psnr=round(psnr_val, 2) if not math.isinf(psnr_val) else 999.0,
                ssim=round(ssim_val, 4),
                mse=round(mse_val, 6),
                residual_energy=round(res_energy, 4),
                objective_loss=round(loss, 5),
                action_taken=action,
                textured_blocks_used=blocks_used,
                candidate_pool_size=pool_size,
            )
            history.append(stat)

            cand_entry = {
                "iteration": k,
                "pixels": cand_pixels,
                "stat": stat,
                "loss": loss,
                "p_stego": p_stego,
                "psnr": psnr_val,
                "ssim": ssim_val,
                "mse": mse_val,
            }
            candidates_evaluated.append(cand_entry)

            # Check convergence condition: P(stego) < tau AND PSNR >= target_psnr
            if p_stego < threshold and (math.isinf(psnr_val) or psnr_val >= target_psnr):
                converged = True
                break

        # Select best candidate:
        # If converged, pick the converging candidate.
        # Otherwise, pick candidate with minimum objective loss J.
        if converged:
            best_cand = candidates_evaluated[-1]
        else:
            best_cand = min(candidates_evaluated, key=lambda c: c["loss"])

        best_pixels = best_cand["pixels"]
        initial_stat = history[0]
        final_stat = best_cand["stat"]

        p_reduction = round(initial_stat.p_stego - final_stat.p_stego, 4)
        psnr_improvement = round(final_stat.psnr - initial_stat.psnr, 2)

        quality_rating, is_imperceptible = evaluate_quality_rating(
            final_stat.psnr, final_stat.ssim
        )
        elapsed = round(time.time() - start_time, 3)

        report = FeedbackOptimizationReport(
            converged=converged,
            iterations_run=len(history),
            initial_p_stego=initial_stat.p_stego,
            final_p_stego=final_stat.p_stego,
            p_stego_reduction=p_reduction,
            initial_psnr=initial_stat.psnr,
            final_psnr=final_stat.psnr,
            psnr_improvement=psnr_improvement,
            final_ssim=final_stat.ssim,
            final_mse=final_stat.mse,
            decision_threshold=threshold,
            quality_rating=quality_rating,
            is_imperceptible=is_imperceptible,
            best_iteration_selected=best_cand["iteration"],
            key_fingerprint=key_fp,
            payload_bytes=len(payload_bytes),
            duration_seconds=elapsed,
            history=history,
        )

        return best_pixels, report

    @classmethod
    def extract(
        cls,
        stego_pixels: np.ndarray,
        stego_key: str,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Extracts and verifies secret payload embedded via FeedbackOptimizer."""
        if not stego_key:
            raise ValueError("Steganographic key cannot be empty.")

        h, w, c = stego_pixels.shape
        ranked_blocks = cls._rank_blocks(stego_pixels, block_size)
        total_blocks = len(ranked_blocks)

        header_bits_needed = FeedbackPayloadPacker.HEADER_SIZE_BYTES * 8

        # Scan candidate iterations k in 1..k_max to match header
        found_header: Optional[bytes] = None
        matched_candidates = None
        matched_seed = None

        for test_k in range(1, cls.DEFAULT_MAX_ITERATIONS + 1):
            test_lvl = test_k - 1
            if test_lvl == 0:
                cands = [b for b in ranked_blocks if b.predicted_class != 0]
            else:
                high_texture = [b for b in ranked_blocks if b.predicted_class == 2]
                medium_texture = [b for b in ranked_blocks if b.predicted_class == 1]
                keep_count = max(0, len(medium_texture) - (test_lvl * max(1, len(medium_texture) // 4)))
                cands = high_texture + medium_texture[:keep_count]

            if not cands:
                cands = ranked_blocks

            test_salt = f"STEGO-FEEDBACK-V17-K{test_k}-R{test_lvl}".encode("utf-8")
            test_seed = PrngKeyDeriver.derive_seed(stego_key, salt=test_salt)
            scattered_test = CryptographicPermuter.permute(cands, test_seed)

            test_bits: List[int] = []
            for b_info in scattered_test:
                if len(test_bits) >= header_bits_needed:
                    break
                y0, y1 = b_info.y_start, b_info.y_end
                x0, x1 = b_info.x_start, b_info.x_end
                block = stego_pixels[y0:y1, x0:x1, :]

                for y in range(block_size):
                    for x in range(block_size):
                        for ch in range(c):
                            if len(test_bits) < header_bits_needed:
                                test_bits.append(int(block[y, x, ch] & 0x01))
                            else:
                                break
                        if len(test_bits) >= header_bits_needed:
                            break
                    if len(test_bits) >= header_bits_needed:
                        break

            if len(test_bits) >= header_bits_needed:
                test_header_bytes = np.packbits(np.array(test_bits, dtype=np.uint8)).tobytes()
                if test_header_bytes[:8] == FeedbackPayloadPacker.MAGIC_HEADER:
                    found_header = test_header_bytes
                    matched_candidates = cands
                    matched_seed = test_seed
                    break

        if found_header is None:
            raise NoStegoPayloadFoundError(
                "No feedback stego payload found: magic header mismatch. "
                "Incorrect steganographic key or not a feedback-optimized stego image."
            )

        payload_len, expected_crc, opt_iter, realloc_lvl = FeedbackPayloadPacker.unpack_header(
            found_header
        )

        total_frame_bytes = FeedbackPayloadPacker.HEADER_SIZE_BYTES + payload_len
        total_bits_needed = total_frame_bytes * 8

        # Extract all bits from matched scattered blocks
        scattered_payload = CryptographicPermuter.permute(matched_candidates, matched_seed)
        extracted_bits: List[int] = []
        blocks_traversed = 0

        for b_info in scattered_payload:
            if len(extracted_bits) >= total_bits_needed:
                break
            blocks_traversed += 1
            y0, y1 = b_info.y_start, b_info.y_end
            x0, x1 = b_info.x_start, b_info.x_end
            block = stego_pixels[y0:y1, x0:x1, :]

            for y in range(block_size):
                for x in range(block_size):
                    for ch in range(c):
                        if len(extracted_bits) < total_bits_needed:
                            extracted_bits.append(int(block[y, x, ch] & 0x01))
                        else:
                            break
                    if len(extracted_bits) >= total_bits_needed:
                        break
                if len(extracted_bits) >= total_bits_needed:
                    break

        full_frame = np.packbits(np.array(extracted_bits, dtype=np.uint8)).tobytes()
        raw_payload = full_frame[FeedbackPayloadPacker.HEADER_SIZE_BYTES : total_frame_bytes]

        actual_crc = zlib.crc32(raw_payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise PayloadCorruptedError(
                f"CRC-32 verification failed on feedback payload: expected {expected_crc:#010x}, got {actual_crc:#010x}."
            )

        meta = {
            "crc_verified": True,
            "crc32": f"{actual_crc:#010x}",
            "payload_bytes": len(raw_payload),
            "opt_iteration": opt_iter,
            "realloc_level": realloc_lvl,
            "blocks_traversed": blocks_traversed,
            "key_fingerprint": PrngKeyDeriver.compute_key_fingerprint(stego_key),
        }
        return raw_payload, meta
