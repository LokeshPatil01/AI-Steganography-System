"""AI-Selected Adaptive Steganography Engine (Phase 14).

Embeds confidential payloads strictly into image regions classified as high-suitability
by the pre-trained Scikit-Learn Random Forest Classifier (Phase 12 & 13):
- 16x16 non-overlapping block partitioning.
- 8-dimensional MSB-invariant spatial feature extraction (pixel & 0xFE).
- AI suitability score ranking: S = 2.0*P(HighTexture) + 1.0*P(Medium).
- Selective embedding: modifies only the highest-scoring textured/edge blocks,
  preserving smooth/flat regions 100% untouched to maximize Human Visual System (HVS) masking.
- Wire framing: Magic b'STEGAI01', 32-bit length, 32-bit CRC-32 integrity.
- Receiver-side blind self-synchronizing extraction (zero coordinate transmission overhead).
- 3-way comparative evaluation (Baseline Sequential vs. Rule-Based vs. AI-Selected).
"""
import math
import struct
import zlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np

from app.ai.region_classifier import CLASS_NAMES, RegionClassifier
from app.image.metrics import compute_all_metrics, compute_mse, compute_psnr, compute_ssim
from app.steganography.adaptive_rules import AdaptiveRulesLSB
from app.steganography.baseline_lsb import (
    BaselineLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
)
from app.steganography.payload_packer import PayloadCorruptedError

DEFAULT_BLOCK_SIZE = 16


@dataclass
class AiStegoBlockInfo:
    """Metadata and AI suitability prediction for an individual image block."""
    block_index: int
    bx: int
    by: int
    x_start: int
    x_end: int
    y_start: int
    y_end: int
    predicted_class: int
    class_name: str
    suitability_score: float
    prob_high_texture: float
    prob_medium: float
    prob_smooth: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AiPayloadPacker:
    """Frames and unframes AI-selected adaptive steganography payloads with CRC-32 integrity."""

    MAGIC_HEADER = b"STEGAI01"
    HEADER_SIZE_BYTES = 16  # 8 bytes magic + 4 bytes length + 4 bytes CRC-32

    @classmethod
    def pack(cls, payload_data: bytes) -> bytes:
        """Packs raw payload into binary frame:
        [8 bytes: Magic b'STEGAI01']
        [4 bytes: Payload length (big-endian uint32)]
        [4 bytes: CRC-32 checksum (big-endian uint32)]
        [N bytes: Raw payload data]
        """
        length = len(payload_data)
        crc = zlib.crc32(payload_data) & 0xFFFFFFFF
        header = cls.MAGIC_HEADER + struct.pack(">II", length, crc)
        return header + payload_data

    @classmethod
    def unpack_header(cls, frame_bytes: bytes) -> Tuple[int, int]:
        """Extracts expected payload length and CRC-32 checksum from header."""
        if len(frame_bytes) < cls.HEADER_SIZE_BYTES:
            raise NoStegoPayloadFoundError(
                f"Insufficient data to unpack header: got {len(frame_bytes)} bytes, expected {cls.HEADER_SIZE_BYTES}."
            )

        magic = frame_bytes[:8]
        if magic != cls.MAGIC_HEADER:
            raise NoStegoPayloadFoundError(
                f"AI Stego magic header mismatch: expected {cls.MAGIC_HEADER}, got {magic}."
            )

        payload_length, expected_crc = struct.unpack(">II", frame_bytes[8:16])
        return payload_length, expected_crc


class AiAdaptiveLSB:
    """Core steganography engine utilizing Random Forest AI region selection."""

    DEFAULT_BLOCK_SIZE = DEFAULT_BLOCK_SIZE

    @classmethod
    def rank_blocks_with_ai(
        cls,
        pixel_array: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> List[AiStegoBlockInfo]:
        """Partitions image into N x N blocks and ranks them by AI Random Forest suitability score.

        Uses the upper 7 bits (pixel & 0xFE) to guarantee MSB-plane invariance between cover and stego.
        """
        model = RegionClassifier.get_model()
        h, w, c = pixel_array.shape

        grid_y = h // block_size
        grid_x = w // block_size

        feature_rows: List[List[float]] = []
        block_coords: List[Tuple[int, int, int, int, int, int, int]] = []

        idx = 0
        for by in range(grid_y):
            y0 = by * block_size
            y1 = y0 + block_size
            for bx in range(grid_x):
                x0 = bx * block_size
                x1 = x0 + block_size

                block = pixel_array[y0:y1, x0:x1, :]
                feats = RegionClassifier.extract_features_msb(block)
                feature_rows.append(feats)
                block_coords.append((idx, bx, by, x0, x1, y0, y1))
                idx += 1

        if not feature_rows:
            return []

        X_matrix = np.array(feature_rows, dtype=np.float32)
        predictions = model.predict(X_matrix)
        probabilities = model.predict_proba(X_matrix)

        block_list: List[AiStegoBlockInfo] = []
        for i, (b_idx, bx, by, x0, x1, y0, y1) in enumerate(block_coords):
            p_class = int(predictions[i])
            probs = probabilities[i]

            p_smooth = float(round(float(probs[0]), 4))
            p_med = float(round(float(probs[1]), 4))
            p_high = float(round(float(probs[2]), 4))

            # Composite AI suitability: High texture prioritized highest
            suitability = float(round(float(p_high * 2.0 + p_med * 1.0), 4))

            info = AiStegoBlockInfo(
                block_index=b_idx,
                bx=bx,
                by=by,
                x_start=x0,
                x_end=x1,
                y_start=y0,
                y_end=y1,
                predicted_class=p_class,
                class_name=CLASS_NAMES[p_class],
                suitability_score=suitability,
                prob_high_texture=p_high,
                prob_medium=p_med,
                prob_smooth=p_smooth,
            )
            block_list.append(info)

        # Deterministic sorting: Highest AI score first; tiebreaker is (by, bx) coordinate
        block_list.sort(key=lambda b: (-b.suitability_score, b.by, b.bx))
        return block_list

    @classmethod
    def calculate_capacity(
        cls,
        pixel_array: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Dict[str, Any]:
        """Calculates total capacity and AI-selected capacity (preserving smooth regions)."""
        h, w = pixel_array.shape[:2]
        channels = pixel_array.shape[2] if pixel_array.ndim == 3 else 1
        blocks_x = w // block_size
        blocks_y = h // block_size
        total_blocks = blocks_x * blocks_y

        bits_per_block = block_size * block_size * channels
        bytes_per_block = bits_per_block // 8

        total_bits_available = total_blocks * bits_per_block
        total_capacity_bytes = total_bits_available // 8

        header_overhead = AiPayloadPacker.HEADER_SIZE_BYTES
        max_payload_bytes = max(0, total_capacity_bytes - header_overhead)

        ranked = cls.rank_blocks_with_ai(pixel_array, block_size)
        high_blocks = sum(1 for b in ranked if b.predicted_class == 2)
        med_blocks = sum(1 for b in ranked if b.predicted_class == 1)
        smooth_blocks = sum(1 for b in ranked if b.predicted_class == 0)

        # AI-preserved capacity: high + medium blocks only
        ai_usable_blocks = high_blocks + med_blocks
        ai_capacity_bytes = max(0, (ai_usable_blocks * bytes_per_block) - header_overhead)

        return {
            "width": w,
            "height": h,
            "channels": channels,
            "block_size": block_size,
            "total_blocks": total_blocks,
            "bits_per_block": bits_per_block,
            "bytes_per_block": bytes_per_block,
            "header_overhead_bytes": header_overhead,
            "total_capacity_bytes": total_capacity_bytes,
            "max_payload_bytes": max_payload_bytes,
            "ai_usable_blocks": ai_usable_blocks,
            "ai_preserved_capacity_bytes": ai_capacity_bytes,
            "high_texture_blocks": high_blocks,
            "medium_texture_blocks": med_blocks,
            "smooth_blocks": smooth_blocks,
        }

    @classmethod
    def embed(
        cls,
        cover_pixels: np.ndarray,
        payload: bytes,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Embeds payload strictly into the highest-ranked AI-selected blocks.

        Smooth regions (Class 0) are preserved 100% untouched whenever capacity permits.
        """
        stego = cover_pixels.copy()
        h, w, c = stego.shape

        if c < 3:
            raise ValueError(f"Color image required with 3 channels, got {c}.")

        ranked_blocks = cls.rank_blocks_with_ai(cover_pixels, block_size)
        total_blocks = len(ranked_blocks)

        packed_frame = AiPayloadPacker.pack(payload)
        frame_bit_len = len(packed_frame) * 8

        bits_per_block = block_size * block_size * c
        required_blocks = math.ceil(frame_bit_len / bits_per_block)

        if required_blocks > total_blocks:
            raise CapacityExceededError(
                f"Payload requires {required_blocks} blocks ({frame_bit_len} bits), "
                f"but cover image only contains {total_blocks} blocks ({total_blocks * bits_per_block} bits capacity)."
            )

        # Unpack binary frame into bitstream
        bit_stream = np.unpackbits(np.frombuffer(packed_frame, dtype=np.uint8))
        bit_idx = 0
        total_bits = len(bit_stream)

        blocks_used = 0
        blocks_preserved_smooth = 0

        # Embed bit by bit across AI-ranked blocks in strict priority sequence
        for block_info in ranked_blocks:
            if bit_idx >= total_bits:
                if block_info.predicted_class == 0:
                    blocks_preserved_smooth += 1
                continue

            blocks_used += 1
            y0, y1 = block_info.y_start, block_info.y_end
            x0, x1 = block_info.x_start, block_info.x_end

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

        altered_pixels = int(np.count_nonzero(np.any(cover_pixels != stego, axis=2)))
        cap_info = cls.calculate_capacity(cover_pixels, block_size)

        metadata = {
            "method": "AI_Random_Forest_Adaptive_LSB",
            "payload_bytes": len(payload),
            "frame_bytes": len(packed_frame),
            "blocks_utilized": blocks_used,
            "blocks_total": total_blocks,
            "blocks_preserved_smooth": blocks_preserved_smooth,
            "capacity_total_bytes": cap_info["max_payload_bytes"],
            "capacity_used_percent": round((len(payload) / cap_info["max_payload_bytes"]) * 100, 2)
            if cap_info["max_payload_bytes"] > 0 else 100.0,
            "altered_pixels": altered_pixels,
            "bpp": round(total_bits / (w * h), 6),
        }
        return stego, metadata

    @classmethod
    def extract(
        cls,
        stego_pixels: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Extracts embedded payload from stego image with zero block map transmission overhead."""
        h, w, c = stego_pixels.shape
        ranked_blocks = cls.rank_blocks_with_ai(stego_pixels, block_size)

        header_bytes_needed = AiPayloadPacker.HEADER_SIZE_BYTES
        header_bits_needed = header_bytes_needed * 8

        # First pass: Extract header to determine payload length and CRC
        collected_bits: List[int] = []
        blocks_traversed = 0
        payload_bit_len = None
        total_bits_to_extract = header_bits_needed

        for block_info in ranked_blocks:
            blocks_traversed += 1
            y0, y1 = block_info.y_start, block_info.y_end
            x0, x1 = block_info.x_start, block_info.x_end

            block = stego_pixels[y0:y1, x0:x1, :]

            for y in range(block_size):
                for x in range(block_size):
                    for ch in range(c):
                        bit = int(block[y, x, ch] & 1)
                        collected_bits.append(bit)

                        # Once we reach header size, unpack header
                        if len(collected_bits) == header_bits_needed and payload_bit_len is None:
                            header_bytes = np.packbits(np.array(collected_bits[:header_bits_needed], dtype=np.uint8)).tobytes()
                            payload_len, expected_crc = AiPayloadPacker.unpack_header(header_bytes)
                            payload_bit_len = payload_len * 8
                            total_bits_to_extract = header_bits_needed + payload_bit_len

                        if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                            break
                    if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                        break
                if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                    break

            if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                break

        if payload_bit_len is None or len(collected_bits) < total_bits_to_extract:
            raise NoStegoPayloadFoundError("Unable to extract valid AI Stego payload from image.")

        full_bytes = np.packbits(np.array(collected_bits[:total_bits_to_extract], dtype=np.uint8)).tobytes()
        header_bytes = full_bytes[:header_bytes_needed]
        payload_len, expected_crc = AiPayloadPacker.unpack_header(header_bytes)

        payload_bytes = full_bytes[header_bytes_needed : header_bytes_needed + payload_len]

        actual_crc = zlib.crc32(payload_bytes) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise PayloadCorruptedError(
                f"CRC-32 checksum mismatch in AI Stego: expected 0x{expected_crc:08X}, got 0x{actual_crc:08X}."
            )

        meta = {
            "method": "AI_Random_Forest_Adaptive_LSB",
            "payload_bytes": payload_len,
            "blocks_traversed": blocks_traversed,
            "crc_verified": True,
            "crc32": f"0x{actual_crc:08X}",
        }
        return payload_bytes, meta

    @classmethod
    def compare_all_methods(
        cls,
        cover_pixels: np.ndarray,
        payload_bytes: bytes,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Dict[str, Any]:
        """Executes a direct 3-way empirical comparison on the exact same cover image and payload:
        1. Baseline Sequential LSB (Phase 7)
        2. Rule-Based Adaptive LSB (Phase 10)
        3. AI Random Forest Adaptive LSB (Phase 14)
        """
        # 1. Baseline Sequential LSB
        stego_base, meta_base = BaselineLSB.embed(cover_pixels, payload_bytes)
        mse_base = compute_mse(cover_pixels, stego_base)
        psnr_base = compute_psnr(cover_pixels, stego_base)
        ssim_base = compute_ssim(cover_pixels, stego_base)["ssim_mean"]

        # 2. Rule-Based Adaptive LSB
        stego_rule, meta_rule = AdaptiveRulesLSB.embed(cover_pixels, payload_bytes, block_size)
        mse_rule = compute_mse(cover_pixels, stego_rule)
        psnr_rule = compute_psnr(cover_pixels, stego_rule)
        ssim_rule = compute_ssim(cover_pixels, stego_rule)["ssim_mean"]

        # 3. AI Random Forest Adaptive LSB
        stego_ai, meta_ai = cls.embed(cover_pixels, payload_bytes, block_size)
        mse_ai = compute_mse(cover_pixels, stego_ai)
        psnr_ai = compute_psnr(cover_pixels, stego_ai)
        ssim_ai = compute_ssim(cover_pixels, stego_ai)["ssim_mean"]

        psnr_gain_over_baseline = psnr_ai - psnr_base
        psnr_gain_over_rule = psnr_ai - psnr_rule

        return {
            "payload_bytes": len(payload_bytes),
            "baseline_lsb": {
                "method": "Baseline_Sequential_LSB",
                "mse": float(round(mse_base, 6)),
                "psnr_db": float(round(psnr_base, 4)) if not math.isinf(psnr_base) else 999.0,
                "ssim": float(round(ssim_base, 6)),
                "altered_pixels": meta_base.get("altered_pixels", 0),
            },
            "rule_adaptive_lsb": {
                "method": "Rule_Based_Adaptive_LSB",
                "mse": float(round(mse_rule, 6)),
                "psnr_db": float(round(psnr_rule, 4)) if not math.isinf(psnr_rule) else 999.0,
                "ssim": float(round(ssim_rule, 6)),
                "blocks_utilized": meta_rule.get("blocks_utilized", 0),
                "blocks_preserved_smooth": meta_rule.get("blocks_preserved_smooth", 0),
            },
            "ai_adaptive_lsb": {
                "method": "AI_Random_Forest_Adaptive_LSB",
                "mse": float(round(mse_ai, 6)),
                "psnr_db": float(round(psnr_ai, 4)) if not math.isinf(psnr_ai) else 999.0,
                "ssim": float(round(ssim_ai, 6)),
                "blocks_utilized": meta_ai.get("blocks_utilized", 0),
                "blocks_preserved_smooth": meta_ai.get("blocks_preserved_smooth", 0),
            },
            "psnr_gain_vs_baseline_db": float(round(psnr_gain_over_baseline, 4)),
            "psnr_gain_vs_rule_db": float(round(psnr_gain_over_rule, 4)),
            "ssim_gain_vs_baseline": float(round(ssim_ai - ssim_base, 6)),
        }
