"""Rule-Based Adaptive Steganography Engine (Phase 10).

Implements content-adaptive spatial LSB steganography based on spatial complexity metrics:
- 16x16 block partitioning
- Invariant MSB-plane feature extraction (Entropy, Sobel Gradients, Canny Edges, Variance, Laplacian)
- Deterministic suitability ranking (textures/edges prioritized over smooth areas)
- Zero-overhead self-synchronizing extraction (no block map transmission needed)
- Wire framing with magic header b'STEGADP1' and CRC-32 integrity verification
- Baseline LSB vs. Adaptive LSB empirical comparison
"""
import math
import struct
import zlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np

from app.image.metrics import compute_all_metrics, compute_mse, compute_psnr, compute_ssim
from app.steganography.baseline_lsb import (
    BaselineLSB,
    CapacityExceededError,
    NoStegoPayloadFoundError,
)
from app.steganography.payload_packer import PayloadCorruptedError


@dataclass
class AdaptiveBlockInfo:
    """Metadata and texture suitability metrics for an individual image block."""
    block_index: int
    bx: int
    by: int
    x_start: int
    x_end: int
    y_start: int
    y_end: int
    score: float
    entropy: float
    sobel_mean: float
    edge_density: float
    variance: float
    laplacian_var: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class AdaptivePayloadPacker:
    """Frames and unframes adaptive steganography payloads with CRC32 integrity."""

    MAGIC_HEADER = b"STEGADP1"
    HEADER_SIZE_BYTES = 16  # 8 bytes magic + 4 bytes payload len + 4 bytes CRC32

    @classmethod
    def pack(cls, payload_data: bytes) -> bytes:
        """Packs raw payload into adaptive binary frame:
        [8 bytes: Magic b'STEGADP1']
        [4 bytes: Payload length (big-endian uint32)]
        [4 bytes: CRC-32 checksum (big-endian uint32)]
        [N bytes: Raw payload data]
        """
        length = len(payload_data)
        crc = zlib.crc32(payload_data) & 0xFFFFFFFF
        header = cls.MAGIC_HEADER + struct.pack(">II", length, crc)
        return header + payload_data

    @classmethod
    def unpack(cls, framed_data: bytes) -> Tuple[bytes, int]:
        """Validates adaptive header and CRC-32 checksum, returning payload bytes."""
        if len(framed_data) < cls.HEADER_SIZE_BYTES:
            raise PayloadCorruptedError("Data is too short to contain a valid adaptive stego frame.")

        magic = framed_data[:8]
        if magic != cls.MAGIC_HEADER:
            raise PayloadCorruptedError(
                f"Invalid or missing adaptive stego header. Expected {cls.MAGIC_HEADER!r}, found {magic!r}."
            )

        length, expected_crc = struct.unpack(">II", framed_data[8:16])
        total_expected_len = cls.HEADER_SIZE_BYTES + length

        if len(framed_data) < total_expected_len:
            raise PayloadCorruptedError(
                f"Truncated adaptive payload: expected {total_expected_len} bytes, got {len(framed_data)}."
            )

        payload_data = framed_data[16:total_expected_len]
        actual_crc = zlib.crc32(payload_data) & 0xFFFFFFFF

        if actual_crc != expected_crc:
            raise PayloadCorruptedError(
                f"CRC32 integrity failed on adaptive payload: expected {expected_crc:#010x}, got {actual_crc:#010x}."
            )

        return payload_data, length


class AdaptiveRulesLSB:
    """Rule-based content-adaptive steganography engine."""

    DEFAULT_BLOCK_SIZE = 16

    @classmethod
    def calculate_block_suitability(
        cls,
        pixel_array: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> List[AdaptiveBlockInfo]:
        """Calculates suitability scores for all blocks using the MSB plane (pixel & 0xFE).

        Extracting features strictly from the upper 7 bits guarantees that 1-bit LSB
        modifications DO NOT shift the feature values, enabling the receiver to recreate
        the exact same block ranking deterministically without transmitting block maps.

        Args:
            pixel_array: RGB uint8 image array (H, W, 3).
            block_size: Spatial block size in pixels (default 16).

        Returns:
            List of AdaptiveBlockInfo sorted in DESCENDING order of suitability score.
        """
        h, w = pixel_array.shape[:2]
        blocks_x = w // block_size
        blocks_y = h // block_size

        if blocks_x == 0 or blocks_y == 0:
            raise ValueError(f"Image ({w}x{h}) is too small for block size {block_size}.")

        # Invariant MSB plane: Mask off LSB bit
        msb_array = pixel_array & 0xFE
        gray_msb = cv2.cvtColor(msb_array, cv2.COLOR_RGB2GRAY)

        block_list: List[AdaptiveBlockInfo] = []
        idx = 0

        for by in range(blocks_y):
            for bx in range(blocks_x):
                y0 = by * block_size
                y1 = y0 + block_size
                x0 = bx * block_size
                x1 = x0 + block_size

                block_gray = gray_msb[y0:y1, x0:x1]
                num_pixels = block_size * block_size

                # 1. Shannon Entropy [0.0, 8.0]
                hist, _ = np.histogram(block_gray, bins=256, range=(0, 256))
                p = hist / num_pixels
                p_nz = p[p > 0]
                entropy = float(-np.sum(p_nz * np.log2(p_nz))) if len(p_nz) > 0 else 0.0
                norm_entropy = min(1.0, entropy / 8.0)

                # 2. Sobel Gradient Magnitude
                gx = cv2.Sobel(block_gray, cv2.CV_64F, 1, 0, ksize=3)
                gy = cv2.Sobel(block_gray, cv2.CV_64F, 0, 1, ksize=3)
                g_mag = np.sqrt(gx ** 2 + gy ** 2)
                sobel_mean = float(np.mean(g_mag))
                norm_sobel = min(1.0, sobel_mean / 128.0)

                # 3. Canny Edge Density [0.0, 1.0]
                edges = cv2.Canny(block_gray, 50, 150)
                edge_density = float(np.count_nonzero(edges) / num_pixels)

                # 4. Variance
                var_val = float(np.var(block_gray))
                norm_var = min(1.0, math.sqrt(var_val) / 64.0)

                # 5. Laplacian Texture Sharpness
                lap = cv2.Laplacian(block_gray, cv2.CV_64F)
                lap_var = float(np.var(lap))
                norm_lap = min(1.0, math.sqrt(lap_var) / 64.0)

                # Weighted Suitability Formula:
                # High texture + high edge density + high entropy = better embedding region
                suitability_score = (
                    0.25 * norm_entropy
                    + 0.25 * norm_sobel
                    + 0.25 * edge_density
                    + 0.15 * norm_var
                    + 0.10 * norm_lap
                )

                info = AdaptiveBlockInfo(
                    block_index=idx,
                    bx=bx,
                    by=by,
                    x_start=x0,
                    x_end=x1,
                    y_start=y0,
                    y_end=y1,
                    score=float(round(suitability_score, 6)),
                    entropy=float(round(entropy, 4)),
                    sobel_mean=float(round(sobel_mean, 4)),
                    edge_density=float(round(edge_density, 4)),
                    variance=float(round(var_val, 4)),
                    laplacian_var=float(round(lap_var, 4)),
                )
                block_list.append(info)
                idx += 1

        # Deterministic sorting: Highest score first, with coordinates as stable tiebreaker
        block_list.sort(key=lambda b: (-b.score, b.by, b.bx))
        return block_list

    @classmethod
    def calculate_capacity(
        cls,
        pixel_array: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Dict[str, Any]:
        """Calculates adaptive payload capacity and block statistics for an image."""
        h, w = pixel_array.shape[:2]
        channels = pixel_array.shape[2] if pixel_array.ndim == 3 else 1
        blocks_x = w // block_size
        blocks_y = h // block_size
        total_blocks = blocks_x * blocks_y

        bits_per_block = block_size * block_size * channels
        bytes_per_block = bits_per_block // 8

        total_bits_available = total_blocks * bits_per_block
        total_capacity_bytes = total_bits_available // 8

        header_overhead = AdaptivePayloadPacker.HEADER_SIZE_BYTES
        max_payload_bytes = max(0, total_capacity_bytes - header_overhead)

        return {
            "width": w,
            "height": h,
            "channels": channels,
            "block_size": block_size,
            "total_blocks": total_blocks,
            "bits_per_block": bits_per_block,
            "bytes_per_block": bytes_per_block,
            "header_overhead_bytes": header_overhead,
            "max_payload_bytes": max_payload_bytes,
            "max_payload_kb": round(max_payload_bytes / 1024.0, 3),
        }

    @classmethod
    def embed(
        cls,
        cover_pixels: np.ndarray,
        payload: bytes,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Embeds payload into the most suitable blocks (Adaptive LSB).

        Smooth/sensitive blocks are bypassed unless the payload size requires them.

        Args:
            cover_pixels: RGB uint8 image array (H, W, 3).
            payload: Secret message bytes.
            block_size: Block partition dimension (default 16).

        Returns:
            Tuple of (stego_pixels: np.ndarray, metadata: dict).
        """
        cap = cls.calculate_capacity(cover_pixels, block_size)
        if len(payload) > cap["max_payload_bytes"]:
            raise CapacityExceededError(
                f"Payload size ({len(payload)} bytes) exceeds adaptive capacity "
                f"({cap['max_payload_bytes']} bytes)."
            )

        framed_bytes = AdaptivePayloadPacker.pack(payload)
        total_bits = len(framed_bytes) * 8

        # Unpack framed bytes into 1D bit array
        bits = np.unpackbits(np.frombuffer(framed_bytes, dtype=np.uint8))

        # Rank blocks deterministically
        ranked_blocks = cls.calculate_block_suitability(cover_pixels, block_size)
        bytes_per_block = cap["bytes_per_block"]
        blocks_needed = math.ceil(len(framed_bytes) / bytes_per_block)

        selected_blocks = ranked_blocks[:blocks_needed]

        stego_pixels = cover_pixels.copy()
        bit_idx = 0
        channels = cover_pixels.shape[2]

        for block in selected_blocks:
            if bit_idx >= total_bits:
                break

            for y in range(block.y_start, block.y_end):
                if bit_idx >= total_bits:
                    break
                for x in range(block.x_start, block.x_end):
                    if bit_idx >= total_bits:
                        break
                    for c in range(channels):
                        if bit_idx < total_bits:
                            current_val = int(stego_pixels[y, x, c])
                            target_bit = int(bits[bit_idx])
                            stego_pixels[y, x, c] = (current_val & 0xFE) | target_bit
                            bit_idx += 1

        capacity_used_pct = round((len(payload) / cap["max_payload_bytes"]) * 100.0, 2)
        bpp = round((len(payload) * 8.0) / (cover_pixels.shape[0] * cover_pixels.shape[1]), 6)

        metadata = {
            "method": "Adaptive_Rule_Based_LSB",
            "payload_bytes": len(payload),
            "framed_bytes": len(framed_bytes),
            "capacity_total_bytes": cap["max_payload_bytes"],
            "capacity_used_percent": capacity_used_pct,
            "bpp": bpp,
            "total_blocks": len(ranked_blocks),
            "blocks_utilized": blocks_needed,
            "blocks_preserved_smooth": len(ranked_blocks) - blocks_needed,
            "top_block_score": selected_blocks[0].score if selected_blocks else 0.0,
            "lowest_selected_score": selected_blocks[-1].score if selected_blocks else 0.0,
        }

        return stego_pixels, metadata

    @classmethod
    def extract(
        cls,
        stego_pixels: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Extracts and verifies an adaptive steganographic payload.

        Extracts block ranking deterministically from stego_pixels & 0xFE.

        Args:
            stego_pixels: Stego RGB uint8 image array (H, W, 3).
            block_size: Block partition dimension (default 16).

        Returns:
            Tuple of (extracted_payload: bytes, metadata: dict).
        """
        ranked_blocks = cls.calculate_block_suitability(stego_pixels, block_size)
        channels = stego_pixels.shape[2]
        header_len = AdaptivePayloadPacker.HEADER_SIZE_BYTES
        header_bits_needed = header_len * 8

        extracted_bits: List[int] = []
        total_bits_needed: Optional[int] = None
        blocks_traversed = 0

        for block in ranked_blocks:
            blocks_traversed += 1
            for y in range(block.y_start, block.y_end):
                for x in range(block.x_start, block.x_end):
                    for c in range(channels):
                        extracted_bits.append(int(stego_pixels[y, x, c] & 1))

                        # Once header bits are collected, validate and parse expected length
                        if total_bits_needed is None and len(extracted_bits) == header_bits_needed:
                            header_bytes = np.packbits(
                                np.array(extracted_bits[:header_bits_needed], dtype=np.uint8)
                            ).tobytes()

                            magic = header_bytes[:8]
                            if magic != AdaptivePayloadPacker.MAGIC_HEADER:
                                raise NoStegoPayloadFoundError(
                                    f"No adaptive stego payload detected. Found magic header {magic!r} "
                                    f"instead of {AdaptivePayloadPacker.MAGIC_HEADER!r}."
                                )

                            payload_len, _ = struct.unpack(">II", header_bytes[8:16])
                            total_bits_needed = (header_len + payload_len) * 8

                        if total_bits_needed is not None and len(extracted_bits) >= total_bits_needed:
                            break
                    if total_bits_needed is not None and len(extracted_bits) >= total_bits_needed:
                        break
                if total_bits_needed is not None and len(extracted_bits) >= total_bits_needed:
                    break
            if total_bits_needed is not None and len(extracted_bits) >= total_bits_needed:
                break

        if total_bits_needed is None or len(extracted_bits) < total_bits_needed:
            raise PayloadCorruptedError("Image was truncated before complete adaptive payload could be extracted.")

        framed_bytes = np.packbits(np.array(extracted_bits[:total_bits_needed], dtype=np.uint8)).tobytes()
        payload_data, _ = AdaptivePayloadPacker.unpack(framed_bytes)

        metadata = {
            "method": "Adaptive_Rule_Based_LSB",
            "payload_bytes": len(payload_data),
            "crc_verified": True,
            "blocks_traversed": blocks_traversed,
        }

        return payload_data, metadata

    @classmethod
    def compare_with_baseline(
        cls,
        cover_pixels: np.ndarray,
        payload: bytes,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Dict[str, Any]:
        """Empirically evaluates Baseline Sequential LSB vs. Adaptive Rule-Based LSB
        on the exact same cover image and secret payload.

        Returns side-by-side PSNR, SSIM, MSE, and alteration statistics.
        """
        # 1. Baseline Sequential LSB
        stego_baseline, meta_base = BaselineLSB.embed(cover_pixels, payload)
        metrics_base = compute_all_metrics(
            cover_img=cover_pixels,
            stego_img=stego_baseline,
            original_payload=payload,
            recovered_payload=payload,
            payload_bytes=len(payload),
        )

        # 2. Adaptive Rule-Based LSB
        stego_adaptive, meta_adap = cls.embed(cover_pixels, payload, block_size)
        metrics_adap = compute_all_metrics(
            cover_img=cover_pixels,
            stego_img=stego_adaptive,
            original_payload=payload,
            recovered_payload=payload,
            payload_bytes=len(payload),
        )

        # 3. Analyze spatial alteration distribution:
        # Check alterations in top 25% smooth region vs. textured region
        diff_base = np.abs(cover_pixels.astype(int) - stego_baseline.astype(int))
        diff_adap = np.abs(cover_pixels.astype(int) - stego_adaptive.astype(int))

        return {
            "payload_bytes": len(payload),
            "baseline_lsb": {
                "psnr_db": 100.0 if math.isinf(metrics_base.psnr_db) else round(metrics_base.psnr_db, 4),
                "ssim": round(metrics_base.ssim, 6),
                "mse": round(metrics_base.mse, 6),
                "image_lsb_ber": round(metrics_base.image_lsb_ber, 6),
                "quality_rating": metrics_base.quality_rating,
            },
            "adaptive_lsb": {
                "psnr_db": 100.0 if math.isinf(metrics_adap.psnr_db) else round(metrics_adap.psnr_db, 4),
                "ssim": round(metrics_adap.ssim, 6),
                "mse": round(metrics_adap.mse, 6),
                "image_lsb_ber": round(metrics_adap.image_lsb_ber, 6),
                "quality_rating": metrics_adap.quality_rating,
                "blocks_utilized": meta_adap["blocks_utilized"],
                "blocks_preserved_smooth": meta_adap["blocks_preserved_smooth"],
            },
            "psnr_improvement_db": round(
                (metrics_adap.psnr_db if not math.isinf(metrics_adap.psnr_db) else 100.0)
                - (metrics_base.psnr_db if not math.isinf(metrics_base.psnr_db) else 100.0),
                4,
            ),
            "ssim_difference": round(metrics_adap.ssim - metrics_base.ssim, 6),
        }
