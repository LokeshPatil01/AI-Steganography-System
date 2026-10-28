"""PRNG Key-Based Random Block Scatter Steganography Engine (Phase 15).

Combines:
1. MSB-Invariant Spatial Feature Extraction (pixel & 0xFE).
2. Random Forest AI Suitability Classification (Phase 12-14).
3. HKDF-SHA256 Cryptographic Seed Derivation from secret stego keys / passphrases.
4. SHA-256 Counter-PRNG Fisher-Yates Permutation over candidate textured blocks.
5. Selective LSB Embedding: Smooth blocks preserved 100% untouched.
6. Wire Framing: Magic b'STEGPRN1', 32-bit length, 32-bit CRC-32 checksum.
7. Receiver-Side Authenticated Blind Extraction: extraction fails unless the exact
   steganographic key is provided.
"""
import math
import struct
import zlib
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from app.ai.region_classifier import CLASS_NAMES
from app.crypto.scatter_prng import CryptographicPermuter, PrngKeyDeriver
from app.image.metrics import compute_mse, compute_psnr, compute_ssim
from app.steganography.ai_stego import AiAdaptiveLSB, AiStegoBlockInfo
from app.steganography.baseline_lsb import (
    CapacityExceededError,
    NoStegoPayloadFoundError,
)
from app.steganography.payload_packer import PayloadCorruptedError

DEFAULT_BLOCK_SIZE = 16


class ScatterPayloadPacker:
    """Frames and unframes PRNG key-scattered payloads with CRC-32 integrity."""

    MAGIC_HEADER = b"STEGPRN1"
    HEADER_SIZE_BYTES = 16  # 8 bytes magic + 4 bytes length + 4 bytes CRC-32

    @classmethod
    def pack(cls, payload_data: bytes) -> bytes:
        """Packs raw payload into binary wire frame:
        [8 bytes: Magic b'STEGPRN1']
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
                f"PRNG Scatter magic header mismatch: expected {cls.MAGIC_HEADER}, got {magic}. "
                "Incorrect steganographic key or not a key-scattered stego image."
            )

        payload_length, expected_crc = struct.unpack(">II", frame_bytes[8:16])
        return payload_length, expected_crc


class KeyScatteredAiLSB:
    """Steganography engine combining Random Forest AI region selection with PRNG block scattering."""

    DEFAULT_BLOCK_SIZE = DEFAULT_BLOCK_SIZE

    @classmethod
    def calculate_capacity(
        cls,
        pixel_array: np.ndarray,
        block_size: int = DEFAULT_BLOCK_SIZE,
    ) -> Dict[str, Any]:
        """Calculates total capacity and AI-preserved capacity for key-scattered embedding."""
        cap = AiAdaptiveLSB.calculate_capacity(pixel_array, block_size)
        cap["method"] = "Key_Scattered_AI_Adaptive_LSB"
        cap["header_overhead_bytes"] = ScatterPayloadPacker.HEADER_SIZE_BYTES
        return cap

    @classmethod
    def embed(
        cls,
        cover_pixels: np.ndarray,
        payload: bytes,
        stego_key: str | bytes,
        block_size: int = DEFAULT_BLOCK_SIZE,
        salt: Optional[bytes] = None,
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Embeds confidential payload into AI-ranked blocks in a cryptographically permuted sequence.

        1. Partitions image into N x N blocks and scores them via Random Forest (MSB-invariant).
        2. Filters candidate textured blocks (Class 2: HighTexture, Class 1: Medium).
        3. Permutes candidate blocks using HKDF-derived PRNG seed from `stego_key`.
        4. Embeds payload into the permuted sequence of blocks.
        5. Smooth blocks remain 100% untouched whenever capacity permits.
        """
        if not stego_key:
            raise ValueError("Steganographic key/passphrase cannot be empty.")

        stego = cover_pixels.copy()
        h, w, c = stego.shape

        if c < 3:
            raise ValueError(f"Color image required with 3 channels, got {c}.")

        # 1. AI Region Ranking (MSB-invariant)
        ranked_blocks = AiAdaptiveLSB.rank_blocks_with_ai(cover_pixels, block_size)
        total_blocks = len(ranked_blocks)

        packed_frame = ScatterPayloadPacker.pack(payload)
        frame_bit_len = len(packed_frame) * 8

        bits_per_block = block_size * block_size * c
        required_blocks = math.ceil(frame_bit_len / bits_per_block)

        if required_blocks > total_blocks:
            raise CapacityExceededError(
                f"Payload requires {required_blocks} blocks ({frame_bit_len} bits), "
                f"but cover image only contains {total_blocks} blocks ({total_blocks * bits_per_block} bits capacity)."
            )

        # 2. Candidate Pool Separation: Textured vs Smooth
        textured_blocks = [b for b in ranked_blocks if b.predicted_class != 0]
        smooth_blocks = [b for b in ranked_blocks if b.predicted_class == 0]

        # If payload fits within textured blocks, candidate pool is textured only.
        # Otherwise, candidate pool extends to include smooth blocks at the end.
        if required_blocks <= len(textured_blocks):
            candidates_to_scatter = textured_blocks
            remaining_untouched_smooth = len(smooth_blocks)
        else:
            candidates_to_scatter = ranked_blocks
            remaining_untouched_smooth = max(0, total_blocks - required_blocks)

        # 3. Cryptographic Permutation of Candidate Blocks
        key_seed = PrngKeyDeriver.derive_seed(stego_key, salt=salt)
        scattered_blocks = CryptographicPermuter.permute(candidates_to_scatter, key_seed)

        # 4. Sequential Embedding into Scattered Blocks
        bit_stream = np.unpackbits(np.frombuffer(packed_frame, dtype=np.uint8))
        bit_idx = 0
        total_bits = len(bit_stream)

        blocks_used = 0

        for block_info in scattered_blocks:
            if bit_idx >= total_bits:
                break

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
        key_fingerprint = PrngKeyDeriver.compute_key_fingerprint(stego_key)

        metadata = {
            "method": "Key_Scattered_AI_Adaptive_LSB",
            "key_fingerprint": key_fingerprint,
            "payload_bytes": len(payload),
            "frame_bytes": len(packed_frame),
            "blocks_utilized": blocks_used,
            "blocks_total": total_blocks,
            "blocks_preserved_smooth": remaining_untouched_smooth,
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
        stego_key: str | bytes,
        block_size: int = DEFAULT_BLOCK_SIZE,
        salt: Optional[bytes] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Extracts hidden payload from key-scattered stego image using receiver's stego key."""
        if not stego_key:
            raise ValueError("Steganographic key/passphrase cannot be empty for extraction.")

        h, w, c = stego_pixels.shape

        # 1. Receiver re-ranks blocks using MSB-invariant features
        ranked_blocks = AiAdaptiveLSB.rank_blocks_with_ai(stego_pixels, block_size)
        total_blocks = len(ranked_blocks)

        textured_blocks = [b for b in ranked_blocks if b.predicted_class != 0]

        # 2. Derive PRNG seed from receiver key
        key_seed = PrngKeyDeriver.derive_seed(stego_key, salt=salt)

        header_bytes_needed = ScatterPayloadPacker.HEADER_SIZE_BYTES
        header_bits_needed = header_bytes_needed * 8

        # Strategy: first attempt extraction using textured candidates (standard case).
        # If header magic not found and textured_blocks < total_blocks, attempt across all blocks.
        candidate_pools = [textured_blocks]
        if len(textured_blocks) < total_blocks:
            candidate_pools.append(ranked_blocks)

        last_error: Optional[Exception] = None

        for pool in candidate_pools:
            if not pool:
                continue

            scattered_blocks = CryptographicPermuter.permute(pool, key_seed)

            collected_bits: List[int] = []
            blocks_traversed = 0
            payload_bit_len: Optional[int] = None
            total_bits_to_extract = header_bits_needed

            for block_info in scattered_blocks:
                blocks_traversed += 1
                y0, y1 = block_info.y_start, block_info.y_end
                x0, x1 = block_info.x_start, block_info.x_end

                block = stego_pixels[y0:y1, x0:x1, :]

                for y in range(block_size):
                    for x in range(block_size):
                        for ch in range(c):
                            bit = int(block[y, x, ch] & 1)
                            collected_bits.append(bit)

                            # Check header once enough bits collected
                            if len(collected_bits) == header_bits_needed and payload_bit_len is None:
                                header_bytes = np.packbits(
                                    np.array(collected_bits[:header_bits_needed], dtype=np.uint8)
                                ).tobytes()
                                try:
                                    payload_len, expected_crc = ScatterPayloadPacker.unpack_header(header_bytes)
                                    payload_bit_len = payload_len * 8
                                    total_bits_to_extract = header_bits_needed + payload_bit_len
                                except NoStegoPayloadFoundError as e:
                                    last_error = e
                                    break

                            if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                                break
                        if (payload_bit_len is None and last_error is not None) or (
                            payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract
                        ):
                            break
                    if (payload_bit_len is None and last_error is not None) or (
                        payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract
                    ):
                        break

                if payload_bit_len is None and last_error is not None:
                    # Magic mismatch in this candidate pool, try next
                    break

                if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                    break

            if payload_bit_len is not None and len(collected_bits) >= total_bits_to_extract:
                # Successfully extracted frame
                full_bytes = np.packbits(np.array(collected_bits[:total_bits_to_extract], dtype=np.uint8)).tobytes()
                header_bytes = full_bytes[:header_bytes_needed]
                payload_len, expected_crc = ScatterPayloadPacker.unpack_header(header_bytes)
                payload_bytes = full_bytes[header_bytes_needed : header_bytes_needed + payload_len]

                actual_crc = zlib.crc32(payload_bytes) & 0xFFFFFFFF
                if actual_crc != expected_crc:
                    raise PayloadCorruptedError(
                        f"CRC-32 checksum mismatch: expected 0x{expected_crc:08X}, got 0x{actual_crc:08X}. "
                        "Payload is corrupted or incorrect steganographic key was supplied."
                    )

                key_fingerprint = PrngKeyDeriver.compute_key_fingerprint(stego_key)
                meta = {
                    "method": "Key_Scattered_AI_Adaptive_LSB",
                    "key_fingerprint": key_fingerprint,
                    "payload_bytes": payload_len,
                    "blocks_traversed": blocks_traversed,
                    "crc_verified": True,
                    "crc32": f"0x{actual_crc:08X}",
                }
                return payload_bytes, meta

        raise NoStegoPayloadFoundError(
            "Unable to extract valid PRNG key-scattered payload. "
            "Verification failed: incorrect steganographic key or clean cover image."
        )
