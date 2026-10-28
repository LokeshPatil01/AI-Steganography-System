"""AES-256-GCM Authenticated Encryption Engine.

Provides secure symmetric encryption with Galois/Counter Mode (GCM):
- Confidentiality: 256-bit AES encryption
- Integrity & Authenticity: 128-bit authentication tag (detects bit-flipping and tampering)
- Unique Random IV: 96-bit nonce generated per message
"""
import os
import struct
from dataclasses import dataclass
from typing import Optional, Union

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class CryptoError(Exception):
    """Base exception for cryptographic operations."""
    pass

class IntegrityError(CryptoError):
    """Raised when ciphertext or authentication tag has been tampered with."""
    pass

class InvalidKeyError(CryptoError):
    """Raised when an invalid key length or format is provided."""
    pass

@dataclass
class AESEncryptedPayload:
    """Represents an AES-256-GCM encrypted message payload."""
    ciphertext: bytes
    nonce: bytes  # 12-byte IV (96-bit)
    tag: bytes    # 16-byte authentication tag (128-bit)
    associated_data: Optional[bytes] = None

    def to_bytes(self) -> bytes:
        """Serializes the payload into a compact binary wire format.

        Format:
        [1 byte: Version = 0x01]
        [2 bytes: AAD length (big-endian)]
        [N bytes: Associated Authenticated Data]
        [12 bytes: Nonce]
        [16 bytes: Authentication Tag]
        [Remaining bytes: Ciphertext]
        """
        aad = self.associated_data or b""
        header = struct.pack(">BH", 1, len(aad))
        return header + aad + self.nonce + self.tag + self.ciphertext

    @classmethod
    def from_bytes(cls, data: bytes) -> "AESEncryptedPayload":
        """Deserializes a binary payload back into an AESEncryptedPayload instance."""
        if len(data) < 3 + 12 + 16:
            raise CryptoError("Payload is too short to be a valid AES-GCM binary payload.")

        version, aad_len = struct.unpack(">BH", data[:3])
        if version != 1:
            raise CryptoError(f"Unsupported payload version: {version}")

        offset = 3
        aad = data[offset : offset + aad_len] if aad_len > 0 else None
        offset += aad_len

        nonce = data[offset : offset + 12]
        offset += 12

        tag = data[offset : offset + 16]
        offset += 16

        ciphertext = data[offset:]
        return cls(ciphertext=ciphertext, nonce=nonce, tag=tag, associated_data=aad)

class AESCipher:
    """High-level authenticated encryption cipher using AES-256-GCM."""

    KEY_SIZE_BYTES = 32     # 256 bits
    NONCE_SIZE_BYTES = 12   # 96 bits (standard for GCM)
    TAG_SIZE_BYTES = 16     # 128 bits

    @classmethod
    def generate_key(cls) -> bytes:
        """Generates a fresh, cryptographically secure 256-bit AES key."""
        return os.urandom(cls.KEY_SIZE_BYTES)

    @classmethod
    def encrypt(
        cls,
        plaintext: Union[str, bytes],
        key: bytes,
        associated_data: Optional[bytes] = None,
    ) -> AESEncryptedPayload:
        """Encrypts plaintext using AES-256-GCM.

        Args:
            plaintext: Secret message as string or raw bytes.
            key: 256-bit (32-byte) AES key.
            associated_data: Optional unencrypted data to authenticate.

        Returns:
            AESEncryptedPayload containing ciphertext, nonce, and tag.
        """
        if len(key) != cls.KEY_SIZE_BYTES:
            raise InvalidKeyError(
                f"AES-256 key must be exactly {cls.KEY_SIZE_BYTES} bytes, got {len(key)}."
            )

        if isinstance(plaintext, str):
            data_bytes = plaintext.encode("utf-8")
        else:
            data_bytes = plaintext

        # Generate a fresh, unique 96-bit nonce
        nonce = os.urandom(cls.NONCE_SIZE_BYTES)

        aesgcm = AESGCM(key)
        # AESGCM.encrypt appends the 16-byte tag to the ciphertext
        encrypted_data = aesgcm.encrypt(nonce, data_bytes, associated_data)

        # Separate ciphertext and authentication tag
        ciphertext = encrypted_data[: -cls.TAG_SIZE_BYTES]
        tag = encrypted_data[-cls.TAG_SIZE_BYTES :]

        return AESEncryptedPayload(
            ciphertext=ciphertext,
            nonce=nonce,
            tag=tag,
            associated_data=associated_data,
        )

    @classmethod
    def decrypt(
        cls,
        payload: Union[AESEncryptedPayload, bytes],
        key: bytes,
        associated_data: Optional[bytes] = None,
    ) -> bytes:
        """Decrypts an AES-256-GCM payload and verifies its cryptographic tag.

        Args:
            payload: AESEncryptedPayload instance or serialized bytes.
            key: 256-bit (32-byte) AES key.
            associated_data: Associated data that was authenticated during encryption.

        Returns:
            Decrypted plaintext as raw bytes.

        Raises:
            IntegrityError: If ciphertext, tag, or nonce has been modified.
            InvalidKeyError: If the key length is incorrect.
        """
        if len(key) != cls.KEY_SIZE_BYTES:
            raise InvalidKeyError(
                f"AES-256 key must be exactly {cls.KEY_SIZE_BYTES} bytes, got {len(key)}."
            )

        if isinstance(payload, bytes):
            payload = AESEncryptedPayload.from_bytes(payload)

        # Re-attach the 16-byte tag to the ciphertext for AESGCM.decrypt
        full_ciphertext = payload.ciphertext + payload.tag
        effective_aad = associated_data if associated_data is not None else payload.associated_data

        aesgcm = AESGCM(key)
        try:
            return aesgcm.decrypt(payload.nonce, full_ciphertext, effective_aad)
        except InvalidTag:
            raise IntegrityError(
                "INTEGRITY VIOLATION: Authentication tag verification failed! "
                "The ciphertext, nonce, or key has been tampered with or corrupted."
            )

    @classmethod
    def decrypt_to_str(
        cls,
        payload: Union[AESEncryptedPayload, bytes],
        key: bytes,
        associated_data: Optional[bytes] = None,
    ) -> str:
        """Decrypts and decodes the result as a UTF-8 string."""
        raw_bytes = cls.decrypt(payload, key, associated_data)
        return raw_bytes.decode("utf-8")
