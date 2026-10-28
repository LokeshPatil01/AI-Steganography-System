"""Payload packaging, framing, and CRC32 integrity verification."""
import struct
import zlib
from typing import Tuple

class PayloadCorruptedError(Exception):
    """Raised when extracted payload fails magic header check or CRC32 verification."""
    pass

class PayloadPacker:
    """Frames and unframes steganographic payload data with length headers and CRC32."""

    MAGIC_HEADER = b"STEGLSB1"
    HEADER_SIZE_BYTES = 16  # 8 bytes magic + 4 bytes length + 4 bytes CRC32

    @classmethod
    def pack(cls, payload_data: bytes) -> bytes:
        """Packs raw payload data into a framed binary structure.

        Format:
        [8 bytes: Magic Header b'STEGLSB1']
        [4 bytes: Payload Length (big-endian unsigned int)]
        [4 bytes: CRC-32 Checksum of Payload (big-endian unsigned int)]
        [N bytes: Raw Payload Data]
        """
        length = len(payload_data)
        crc = zlib.crc32(payload_data) & 0xFFFFFFFF
        header = cls.MAGIC_HEADER + struct.pack(">II", length, crc)
        return header + payload_data

    @classmethod
    def unpack(cls, framed_data: bytes) -> Tuple[bytes, int]:
        """Unpacks framed binary structure, validates magic header and verifies CRC32.

        Returns:
            Tuple of (payload_data: bytes, payload_length: int)
        """
        if len(framed_data) < cls.HEADER_SIZE_BYTES:
            raise PayloadCorruptedError("Data is too short to contain a valid steganographic frame.")

        magic = framed_data[:8]
        if magic != cls.MAGIC_HEADER:
            raise PayloadCorruptedError(
                f"Invalid or missing steganographic header. Expected {cls.MAGIC_HEADER!r}, found {magic!r}."
            )

        length, expected_crc = struct.unpack(">II", framed_data[8:16])

        total_expected_len = cls.HEADER_SIZE_BYTES + length
        if len(framed_data) < total_expected_len:
            raise PayloadCorruptedError(
                f"Truncated stego payload: expected {total_expected_len} bytes, got {len(framed_data)}."
            )

        payload_data = framed_data[16:total_expected_len]

        actual_crc = zlib.crc32(payload_data) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            raise PayloadCorruptedError(
                f"CRC32 integrity verification failed: expected {expected_crc:#010x}, calculated {actual_crc:#010x}."
            )

        return payload_data, length
