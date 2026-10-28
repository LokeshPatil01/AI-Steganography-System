"""Baseline Sequential Spatial LSB Steganography Engine.

Provides standard 1-bit-per-channel spatial domain LSB embedding and extraction:
- Capacity calculation with header overhead compensation
- Overflow prevention rejecting oversized payloads
- Bit-level masking: channel = (channel & 0xFE) | bit
- Lossless PNG reconstruction
"""
from dataclasses import dataclass
from typing import Tuple, Union
import numpy as np

from app.steganography.payload_packer import (
    PayloadCorruptedError,
    PayloadPacker,
)

class CapacityExceededError(Exception):
    """Raised when the payload size exceeds the maximum available image capacity."""
    pass

class NoStegoPayloadFoundError(Exception):
    """Raised when an image does not contain valid steganographic markers."""
    pass

@dataclass
class CapacityInfo:
    """Image capacity statistics."""
    width: int
    height: int
    channels: int
    total_pixels: int
    total_bits_available: int
    header_overhead_bytes: int
    max_payload_bytes: int
    max_payload_kb: float

class BaselineLSB:
    """Baseline spatial domain 1-bit LSB steganography implementation."""

    HEADER_OVERHEAD_BYTES = PayloadPacker.HEADER_SIZE_BYTES  # 16 bytes

    @classmethod
    def calculate_capacity(cls, pixel_array: np.ndarray) -> CapacityInfo:
        """Calculates maximum steganographic payload capacity for a given image.

        Each color channel (R, G, B) stores 1 bit in its least significant bit.
        Capacity = (H * W * C) / 8 - Header Overhead Bytes.
        """
        h, w, c = pixel_array.shape
        total_pixels = h * w
        total_bits = total_pixels * c
        raw_bytes = total_bits // 8

        max_payload = max(0, raw_bytes - cls.HEADER_OVERHEAD_BYTES)
        max_kb = round(max_payload / 1024.0, 2)

        return CapacityInfo(
            width=w,
            height=h,
            channels=c,
            total_pixels=total_pixels,
            total_bits_available=total_bits,
            header_overhead_bytes=cls.HEADER_OVERHEAD_BYTES,
            max_payload_bytes=max_payload,
            max_payload_kb=max_kb,
        )

    @classmethod
    def embed(
        cls,
        cover_pixels: np.ndarray,
        payload: Union[str, bytes],
    ) -> Tuple[np.ndarray, dict]:
        """Embeds a payload into cover image pixels using sequential 1-bit LSB.

        Args:
            cover_pixels: uint8 NumPy array of shape (H, W, 3).
            payload: Secret message as string or binary bytes.

        Returns:
            Tuple of (stego_pixels: np.ndarray, metadata: dict)

        Raises:
            CapacityExceededError: If payload exceeds capacity.
        """
        if isinstance(payload, str):
            raw_payload = payload.encode("utf-8")
        else:
            raw_payload = payload

        # 1. Capacity check
        cap_info = cls.calculate_capacity(cover_pixels)
        if len(raw_payload) > cap_info.max_payload_bytes:
            raise CapacityExceededError(
                f"Payload size ({len(raw_payload):,} bytes) exceeds maximum image "
                f"capacity ({cap_info.max_payload_bytes:,} bytes). "
                f"Requires an image with at least "
                f"{(len(raw_payload) + cls.HEADER_OVERHEAD_BYTES) * 8 // cap_info.channels:,} pixels."
            )

        # 2. Frame payload with magic header, length prefix, and CRC32
        framed_data = PayloadPacker.pack(raw_payload)
        total_bits_to_embed = len(framed_data) * 8

        # 3. Convert framed bytes to bit array
        bits = np.unpackbits(np.frombuffer(framed_data, dtype=np.uint8))

        # 4. Sequential LSB embedding
        # Flatten pixels view for fast linear indexing
        stego_pixels = cover_pixels.copy()
        flat_channels = stego_pixels.reshape(-1)

        # Clear LSB and insert payload bits
        flat_channels[:total_bits_to_embed] = (
            flat_channels[:total_bits_to_embed] & 0xFE
        ) | bits

        metadata = {
            "payload_bytes": len(raw_payload),
            "framed_bytes": len(framed_data),
            "total_bits_embedded": int(total_bits_to_embed),
            "capacity_total_bytes": cap_info.max_payload_bytes,
            "capacity_used_percent": round((len(raw_payload) / cap_info.max_payload_bytes) * 100, 2),
            "bpp": round(total_bits_to_embed / cap_info.total_pixels, 4),
        }

        return stego_pixels, metadata

    @classmethod
    def extract(cls, stego_pixels: np.ndarray) -> Tuple[bytes, dict]:
        """Extracts the embedded payload from stego image pixels.

        Args:
            stego_pixels: uint8 NumPy array of shape (H, W, 3).

        Returns:
            Tuple of (payload_bytes: bytes, metadata: dict)

        Raises:
            NoStegoPayloadFoundError: If no valid steganographic header is detected.
            PayloadCorruptedError: If CRC32 verification fails.
        """
        flat_channels = stego_pixels.reshape(-1)

        # 1. Read the header bits (16 bytes = 128 bits)
        header_bits_count = cls.HEADER_OVERHEAD_BYTES * 8
        if len(flat_channels) < header_bits_count:
            raise NoStegoPayloadFoundError("Image too small to contain a steganographic header.")

        header_bits = flat_channels[:header_bits_count] & 0x01
        header_bytes = np.packbits(header_bits).tobytes()

        # Check magic marker
        if header_bytes[:8] != PayloadPacker.MAGIC_HEADER:
            raise NoStegoPayloadFoundError(
                "No valid steganographic payload detected in image (missing magic marker)."
            )

        # Read payload length from header
        import struct
        payload_len, _ = struct.unpack(">II", header_bytes[8:16])

        # Validate that length is physically plausible
        cap_info = cls.calculate_capacity(stego_pixels)
        if payload_len > cap_info.max_payload_bytes:
            raise NoStegoPayloadFoundError(
                f"Corrupted stego header: reported length ({payload_len} bytes) "
                f"exceeds maximum physical capacity ({cap_info.max_payload_bytes} bytes)."
            )

        # 2. Read full framed bits
        total_framed_bytes = cls.HEADER_OVERHEAD_BYTES + payload_len
        total_framed_bits = total_framed_bytes * 8

        all_bits = flat_channels[:total_framed_bits] & 0x01
        framed_data = np.packbits(all_bits).tobytes()

        # 3. Unpack and verify CRC32
        payload_data, _ = PayloadPacker.unpack(framed_data)

        metadata = {
            "payload_bytes": len(payload_data),
            "framed_bytes": total_framed_bytes,
            "crc_verified": True,
        }

        return payload_data, metadata

    @classmethod
    def extract_to_str(cls, stego_pixels: np.ndarray) -> str:
        """Extracts payload and decodes as a UTF-8 string."""
        raw_bytes, _ = cls.extract(stego_pixels)
        return raw_bytes.decode("utf-8")
