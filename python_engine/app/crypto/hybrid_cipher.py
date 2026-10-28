"""RSA + AES Hybrid Envelope Encryption Engine.

Combines asymmetric and symmetric cryptographic primitives:
1. Symmetric Confidentiality & Authentication: AES-256-GCM message encryption.
2. Asymmetric Key Encapsulation: RSA-4096-OAEP (SHA-256) encryption of the AES key.
3. Cryptographic Wire Framing: Magic headers, key fingerprints, nonces, and authentication tags.
"""
import struct
from dataclasses import dataclass
from typing import Optional, Union

from app.crypto.aes_engine import (
    AESCipher,
    AESEncryptedPayload,
    CryptoError,
    IntegrityError,
    InvalidKeyError,
)
from app.crypto.rsa_engine import RSACipher, RSAError

class HybridEncryptionError(CryptoError):
    """Raised when hybrid envelope encryption or decryption fails."""
    pass

@dataclass
class HybridEnvelope:
    """Represents a packaged hybrid-encrypted cryptographic envelope."""
    encrypted_aes_key: bytes  # 512 bytes for RSA-4096
    nonce: bytes              # 12 bytes for AES-GCM
    tag: bytes                # 16 bytes for AES-GCM authentication tag
    ciphertext: bytes         # Variable length ciphertext
    recipient_fingerprint: Optional[str] = None  # Helpful for recipient key selection

    MAGIC_HEADER = b"STEGHYB1"

    def to_bytes(self) -> bytes:
        """Serializes the hybrid envelope into a compact binary byte array.

        Format:
        [8 bytes: Magic Header b'STEGHYB1']
        [1 byte: Fingerprint length F]
        [F bytes: Recipient SHA-256 Fingerprint ASCII]
        [2 bytes: Encrypted AES key length K (512)]
        [K bytes: Encrypted AES Key]
        [12 bytes: AES-GCM Nonce]
        [16 bytes: AES-GCM Authentication Tag]
        [4 bytes: Ciphertext length C]
        [C bytes: Ciphertext]
        """
        fp_bytes = (self.recipient_fingerprint or "").encode("ascii")
        if len(fp_bytes) > 255:
            fp_bytes = fp_bytes[:255]

        header = self.MAGIC_HEADER + struct.pack(
            ">BH", len(fp_bytes), len(self.encrypted_aes_key)
        )
        body = (
            fp_bytes
            + self.encrypted_aes_key
            + self.nonce
            + self.tag
            + struct.pack(">I", len(self.ciphertext))
            + self.ciphertext
        )
        return header + body

    @classmethod
    def from_bytes(cls, data: bytes) -> "HybridEnvelope":
        """Deserializes raw binary bytes back into a validated HybridEnvelope."""
        min_header_len = 8 + 1 + 2 + 12 + 16 + 4
        if len(data) < min_header_len:
            raise HybridEncryptionError("Data is too short to be a valid HybridEnvelope.")

        magic = data[:8]
        if magic != cls.MAGIC_HEADER:
            raise HybridEncryptionError(
                f"Invalid envelope magic header: expected {cls.MAGIC_HEADER!r}, got {magic!r}"
            )

        offset = 8
        fp_len, enc_key_len = struct.unpack(">BH", data[offset : offset + 3])
        offset += 3

        if len(data) < offset + fp_len + enc_key_len + 12 + 16 + 4:
            raise HybridEncryptionError("Truncated hybrid envelope data.")

        fp_bytes = data[offset : offset + fp_len]
        recipient_fp = fp_bytes.decode("ascii") if fp_bytes else None
        offset += fp_len

        enc_key = data[offset : offset + enc_key_len]
        offset += enc_key_len

        nonce = data[offset : offset + 12]
        offset += 12

        tag = data[offset : offset + 16]
        offset += 16

        (ciphertext_len,) = struct.unpack(">I", data[offset : offset + 4])
        offset += 4

        ciphertext = data[offset : offset + ciphertext_len]
        if len(ciphertext) != ciphertext_len:
            raise HybridEncryptionError("Truncated ciphertext in hybrid envelope.")

        return cls(
            encrypted_aes_key=enc_key,
            nonce=nonce,
            tag=tag,
            ciphertext=ciphertext,
            recipient_fingerprint=recipient_fp,
        )

class HybridCipher:
    """End-to-end RSA + AES Hybrid Cipher implementation."""

    @classmethod
    def encrypt(
        cls,
        secret_message: Union[str, bytes],
        recipient_public_key_pem: str,
    ) -> HybridEnvelope:
        """Executes the hybrid encryption flow:
        1. Generates a fresh 256-bit AES key.
        2. Encrypts the secret message using AES-256-GCM.
        3. Encapsulates the AES key using recipient's RSA-4096-OAEP public key.
        4. Packages into a HybridEnvelope.
        """
        # 1. Generate fresh AES key
        aes_key = AESCipher.generate_key()

        try:
            # 2. Encrypt message with AES-256-GCM
            aes_payload = AESCipher.encrypt(secret_message, aes_key)

            # 3. Encrypt AES key with recipient's RSA public key (OAEP-SHA256)
            encrypted_aes_key = RSACipher.encrypt_key(aes_key, recipient_public_key_pem)

            # 4. Extract public key fingerprint for envelope metadata
            recipient_fp = RSACipher.get_public_key_fingerprint(recipient_public_key_pem)

            return HybridEnvelope(
                encrypted_aes_key=encrypted_aes_key,
                nonce=aes_payload.nonce,
                tag=aes_payload.tag,
                ciphertext=aes_payload.ciphertext,
                recipient_fingerprint=recipient_fp,
            )
        finally:
            # Zero out symmetric key from memory
            del aes_key

    @classmethod
    def decrypt(
        cls,
        envelope: Union[HybridEnvelope, bytes],
        recipient_private_key_pem: str,
    ) -> bytes:
        """Executes the reverse hybrid decapsulation and decryption flow:
        1. Unpacks the HybridEnvelope.
        2. Decrypts the 512-byte encapsulated AES key using recipient's RSA private key.
        3. Decrypts the ciphertext using AES-256-GCM and verifies the authentication tag.
        4. Returns verified plaintext bytes.
        """
        if isinstance(envelope, bytes):
            envelope = HybridEnvelope.from_bytes(envelope)

        # 1. Decapsulate AES key using recipient's RSA private key
        try:
            aes_key = RSACipher.decrypt_key(
                envelope.encrypted_aes_key, recipient_private_key_pem
            )
        except RSAError as e:
            raise HybridEncryptionError(f"Failed to recover AES key using RSA private key: {e}") from e

        try:
            # 2. Decrypt ciphertext and verify authentication tag
            aes_payload = AESEncryptedPayload(
                ciphertext=envelope.ciphertext,
                nonce=envelope.nonce,
                tag=envelope.tag,
            )
            plaintext = AESCipher.decrypt(aes_payload, aes_key)
            return plaintext
        finally:
            del aes_key

    @classmethod
    def decrypt_to_str(
        cls,
        envelope: Union[HybridEnvelope, bytes],
        recipient_private_key_pem: str,
    ) -> str:
        """Decrypts a hybrid envelope and decodes the result as a UTF-8 string."""
        plaintext_bytes = cls.decrypt(envelope, recipient_private_key_pem)
        return plaintext_bytes.decode("utf-8")
