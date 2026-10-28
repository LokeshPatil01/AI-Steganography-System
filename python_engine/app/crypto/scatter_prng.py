"""Cryptographic PRNG Key-Based Random Block Scatter Engine (Phase 15).

Provides:
- HKDF-SHA256 (RFC 5869) Key Derivation: Derives uniform 256-bit pseudorandom seeds from
  arbitrary user passphrases, AES keys, or RSA key fingerprints.
- Cryptographic Block Permutation: Deterministic, platform-independent Fisher-Yates shuffle
  driven by a SHA-256 counter-mode pseudorandom stream.
- Avalanche Effect: A 1-bit alteration in the steganographic key or salt yields a completely
  uncorrelated permutation across candidate image blocks.
"""
import hashlib
import struct
from typing import Any, List, Optional, Tuple, TypeVar
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

T = TypeVar("T")

DEFAULT_DOMAIN_SALT = b"AI-STEGO-PRNG-SALT-V15"
DEFAULT_INFO_CONTEXT = b"STEGO-PRNG-SCATTER-V1"


class PrngKeyDeriver:
    """Derives deterministic, uniform cryptographic seeds from user credentials."""

    @classmethod
    def derive_seed(
        cls,
        key_material: bytes | str,
        salt: Optional[bytes] = None,
        info: bytes = DEFAULT_INFO_CONTEXT,
        length: int = 32,
    ) -> bytes:
        """Derives a 256-bit (32-byte) pseudo-random seed using HKDF-SHA256."""
        if isinstance(key_material, str):
            key_bytes = key_material.encode("utf-8")
        else:
            key_bytes = key_material

        if not key_bytes:
            raise ValueError("Key material for PRNG derivation cannot be empty.")

        actual_salt = salt if salt is not None else DEFAULT_DOMAIN_SALT

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=length,
            salt=actual_salt,
            info=info,
        )
        return hkdf.derive(key_bytes)

    @classmethod
    def compute_key_fingerprint(cls, key_material: bytes | str) -> str:
        """Computes a non-reversible SHA-256 hex fingerprint for display and auditing."""
        if isinstance(key_material, str):
            key_bytes = key_material.encode("utf-8")
        else:
            key_bytes = key_material
        digest = hashlib.sha256(key_bytes).hexdigest()
        return f"SHA256:{digest[:16]}"


class CryptographicPermuter:
    """Generates cryptographic permutations and shuffles via SHA-256 counter stream."""

    @classmethod
    def generate_uint32_stream(cls, seed: bytes, count: int) -> List[int]:
        """Generates `count` uniform 32-bit unsigned integers from a 32-byte seed
        using SHA-256 in counter mode.
        """
        numbers: List[int] = []
        counter = 0
        while len(numbers) < count:
            block = hashlib.sha256(seed + struct.pack(">I", counter)).digest()
            counter += 1
            for offset in range(0, 32, 4):
                val = struct.unpack(">I", block[offset : offset + 4])[0]
                numbers.append(val)
                if len(numbers) == count:
                    break
        return numbers

    @classmethod
    def get_permutation_indices(cls, n: int, seed: bytes) -> List[int]:
        """Computes a deterministic Fisher-Yates permutation of range(n) using SHA-256 counter PRNG."""
        if n <= 1:
            return list(range(n))

        indices = list(range(n))
        random_stream = cls.generate_uint32_stream(seed, n)

        # Fisher-Yates shuffle (from n-1 down to 1)
        for i in range(n - 1, 0, -1):
            r = random_stream[n - 1 - i]
            j = r % (i + 1)
            indices[i], indices[j] = indices[j], indices[i]

        return indices

    @classmethod
    def permute(
        cls,
        items: List[T],
        key_or_seed: bytes | str,
        salt: Optional[bytes] = None,
    ) -> List[T]:
        """Permutes a list of items using a key-derived cryptographic seed."""
        n = len(items)
        if n <= 1:
            return list(items)

        if isinstance(key_or_seed, str) or len(key_or_seed) != 32:
            seed = PrngKeyDeriver.derive_seed(key_or_seed, salt=salt)
        else:
            seed = key_or_seed

        perm_indices = cls.get_permutation_indices(n, seed)
        return [items[idx] for idx in perm_indices]

    @classmethod
    def unpermute(
        cls,
        permuted_items: List[T],
        key_or_seed: bytes | str,
        salt: Optional[bytes] = None,
    ) -> List[T]:
        """Restores original item order from permuted list using the same key."""
        n = len(permuted_items)
        if n <= 1:
            return list(permuted_items)

        if isinstance(key_or_seed, str) or len(key_or_seed) != 32:
            seed = PrngKeyDeriver.derive_seed(key_or_seed, salt=salt)
        else:
            seed = key_or_seed

        perm_indices = cls.get_permutation_indices(n, seed)

        original_items: List[Optional[T]] = [None] * n
        for new_pos, orig_pos in enumerate(perm_indices):
            original_items[orig_pos] = permuted_items[new_pos]

        return original_items  # type: ignore[return-value]
