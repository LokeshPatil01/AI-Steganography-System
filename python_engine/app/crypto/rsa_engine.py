"""RSA-4096-OAEP Asymmetric Cryptographic Engine.

Provides secure asymmetric key encapsulation and decapsulation:
- RSA-4096 key pair operations
- OAEP padding with SHA-256 and MGF1-SHA256 (IND-CCA2 secure)
- Fingerprint calculation and PEM formatting
"""
import hashlib
from typing import Optional, Tuple

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
    load_pem_private_key,
    load_pem_public_key,
)

from app.crypto.aes_engine import CryptoError

class RSAError(CryptoError):
    """Raised when an RSA cryptographic operation fails."""
    pass

class RSACipher:
    """RSA-4096-OAEP cipher for symmetric key encapsulation."""

    DEFAULT_KEY_SIZE_BITS = 4096
    PUBLIC_EXPONENT = 65537

    @classmethod
    def generate_key_pair(cls, key_size: int = DEFAULT_KEY_SIZE_BITS) -> Tuple[str, str]:
        """Generates an RSA key pair and returns (public_key_pem, private_key_pem)."""
        private_key = rsa.generate_private_key(
            public_exponent=cls.PUBLIC_EXPONENT,
            key_size=key_size,
        )

        private_pem = private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption(),
        ).decode("utf-8")

        public_pem = private_key.public_key().public_bytes(
            encoding=Encoding.PEM,
            format=PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return public_pem, private_pem

    @classmethod
    def get_public_key_fingerprint(cls, public_key_pem: str) -> str:
        """Computes the SHA-256 fingerprint of an RSA public key."""
        public_key = cls.load_public_key(public_key_pem)
        der_bytes = public_key.public_bytes(
            encoding=Encoding.DER,
            format=PublicFormat.SubjectPublicKeyInfo,
        )
        digest = hashlib.sha256(der_bytes).hexdigest().upper()
        return f"SHA256:{digest}"

    @classmethod
    def load_public_key(cls, public_key_pem: str) -> rsa.RSAPublicKey:
        """Loads an RSAPublicKey from a PEM-encoded string."""
        try:
            key = load_pem_public_key(public_key_pem.encode("utf-8"))
            if not isinstance(key, rsa.RSAPublicKey):
                raise RSAError("Loaded public key is not an RSA public key.")
            return key
        except Exception as e:
            raise RSAError(f"Failed to load RSA public key PEM: {e}") from e

    @classmethod
    def load_private_key(
        cls, private_key_pem: str, password: Optional[bytes] = None
    ) -> rsa.RSAPrivateKey:
        """Loads an RSAPrivateKey from a PEM-encoded string."""
        try:
            key = load_pem_private_key(private_key_pem.encode("utf-8"), password=password)
            if not isinstance(key, rsa.RSAPrivateKey):
                raise RSAError("Loaded private key is not an RSA private key.")
            return key
        except Exception as e:
            raise RSAError(f"Failed to load RSA private key PEM: {e}") from e

    @classmethod
    def encrypt_key(cls, symmetric_key: bytes, public_key_pem: str) -> bytes:
        """Encrypts a symmetric AES key (32 bytes) using recipient's RSA-4096 public key.

        Uses OAEP padding with SHA-256 and MGF1-SHA256.
        Produces exactly 512 bytes for RSA-4096.
        """
        public_key = cls.load_public_key(public_key_pem)
        try:
            encrypted_key = public_key.encrypt(
                symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return encrypted_key
        except Exception as e:
            raise RSAError(f"RSA encryption failed: {e}") from e

    @classmethod
    def decrypt_key(cls, encrypted_symmetric_key: bytes, private_key_pem: str) -> bytes:
        """Decrypts a 512-byte encrypted symmetric key using recipient's RSA-4096 private key."""
        private_key = cls.load_private_key(private_key_pem)
        try:
            decrypted_key = private_key.decrypt(
                encrypted_symmetric_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return decrypted_key
        except Exception as e:
            raise RSAError(f"RSA decryption failed (unauthorized or corrupted key material): {e}") from e
