"""Unit and Integration Tests for PRNG Key-Based Random Block Scatter Steganography (Phase 15).

Validates:
- HKDF-SHA256 seed derivation determinism, uniform entropy, and avalanche effect.
- CryptographicPermuter Fisher-Yates permutation determinism, reversibility (unpermute), and key sensitivity.
- ScatterPayloadPacker wire framing and CRC-32 integrity.
- KeyScatteredAiLSB embed and blind extract roundtrip with authenticated secret key.
- Key authentication failure: extraction with incorrect key fails with NoStegoPayloadFoundError / PayloadCorruptedError.
- Clean cover image rejection.
- Smooth regions 100% untouched.
- FastAPI endpoints: /scatter/capacity, /scatter/encode, /scatter/decode, /scatter/verify-key.
"""
import io
import numpy as np
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

from app.crypto.scatter_prng import CryptographicPermuter, PrngKeyDeriver
from app.main import app
from app.steganography.baseline_lsb import CapacityExceededError, NoStegoPayloadFoundError
from app.steganography.payload_packer import PayloadCorruptedError
from app.steganography.scatter_stego import KeyScatteredAiLSB, ScatterPayloadPacker


def _create_synthetic_test_image(width: int = 64, height: int = 64) -> np.ndarray:
    """Creates a deterministic synthetic test image containing both smooth and highly textured blocks."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    # Top half: solid uniform color (Class 0: Smooth)
    img[: height // 2, :, :] = 128

    # Bottom half: high texture pseudo-random noise (Class 2: HighTexture)
    rng = np.random.RandomState(42)
    noise = rng.randint(0, 256, size=(height // 2, width, 3)).astype(np.uint8)
    img[height // 2 :, :, :] = noise
    return img


def _png_bytes_from_array(arr: np.ndarray) -> bytes:
    """Converts numpy array to in-memory PNG bytes."""
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="PNG")
    return buf.getvalue()


# -------------------------------------------------------------------------
# Unit Tests: PRNG Key Deriver & Permuter
# -------------------------------------------------------------------------

def test_prng_key_deriver_seed_determinism_and_length():
    seed1 = PrngKeyDeriver.derive_seed("SecureStegoPassphrase2026")
    seed2 = PrngKeyDeriver.derive_seed("SecureStegoPassphrase2026")
    assert len(seed1) == 32
    assert seed1 == seed2


def test_prng_key_deriver_rejects_empty_key():
    with pytest.raises(ValueError, match="cannot be empty"):
        PrngKeyDeriver.derive_seed("")


def test_prng_key_deriver_avalanche_effect():
    """A 1-bit / 1-character difference in key yields completely uncorrelated 256-bit seeds."""
    seed_a = PrngKeyDeriver.derive_seed("SecretKeyA")
    seed_b = PrngKeyDeriver.derive_seed("SecretKeyB")
    assert seed_a != seed_b

    # Calculate bitwise Hamming distance
    diff_bits = bin(int.from_bytes(seed_a, "big") ^ int.from_bytes(seed_b, "big")).count("1")
    # For a 256-bit hash, expected bit difference is ~128 bits
    assert diff_bits > 90


def test_key_fingerprint_format_and_determinism():
    fp1 = PrngKeyDeriver.compute_key_fingerprint("UserKeyMaterial")
    fp2 = PrngKeyDeriver.compute_key_fingerprint("UserKeyMaterial")
    assert fp1.startswith("SHA256:")
    assert len(fp1) == 7 + 16
    assert fp1 == fp2


def test_cryptographic_permuter_determinism_and_reversibility():
    items = [f"block_{i}" for i in range(25)]
    seed = PrngKeyDeriver.derive_seed("PermuteTestKey")

    permuted_1 = CryptographicPermuter.permute(items, seed)
    permuted_2 = CryptographicPermuter.permute(items, seed)

    # Determinism
    assert permuted_1 == permuted_2
    assert set(permuted_1) == set(items)
    # Permutation should not be equal to original sequence
    assert permuted_1 != items

    # Reversibility
    unpermuted = CryptographicPermuter.unpermute(permuted_1, seed)
    assert unpermuted == items


def test_cryptographic_permuter_key_sensitivity():
    items = [f"node_{i}" for i in range(30)]
    perm_a = CryptographicPermuter.permute(items, "KeyAlpha")
    perm_b = CryptographicPermuter.permute(items, "KeyBeta")
    assert perm_a != perm_b


# -------------------------------------------------------------------------
# Unit Tests: Scatter Payload Packer
# -------------------------------------------------------------------------

def test_scatter_payload_packer_pack_and_unpack():
    payload = b"PRNG Key Scattered Confidential Secret 2026"
    packed = ScatterPayloadPacker.pack(payload)

    assert packed.startswith(b"STEGPRN1")
    assert len(packed) == 16 + len(payload)

    extracted_len, crc = ScatterPayloadPacker.unpack_header(packed)
    assert extracted_len == len(payload)
    assert crc > 0


def test_scatter_payload_packer_invalid_magic_raises_error():
    invalid_frame = b"WRONGMAG" + b"\x00" * 8
    with pytest.raises(NoStegoPayloadFoundError, match="magic header mismatch"):
        ScatterPayloadPacker.unpack_header(invalid_frame)


# -------------------------------------------------------------------------
# Unit Tests: Key-Scattered Stego Engine
# -------------------------------------------------------------------------

def test_key_scattered_ai_lsb_capacity():
    cover = _create_synthetic_test_image(64, 64)
    cap = KeyScatteredAiLSB.calculate_capacity(cover, block_size=16)

    assert cap["total_blocks"] == 16
    assert cap["max_payload_bytes"] > 0
    assert cap["header_overhead_bytes"] == 16
    assert cap["method"] == "Key_Scattered_AI_Adaptive_LSB"


def test_key_scattered_ai_lsb_embed_and_extract_correct_key():
    cover = _create_synthetic_test_image(64, 64)
    secret_text = "Top-Secret Cryptographic Key-Scattered Payload 🔒"
    payload = secret_text.encode("utf-8")
    stego_key = "SuperSecretStegoPassword!2026"

    # Embed
    stego, meta = KeyScatteredAiLSB.embed(cover, payload, stego_key, block_size=16)
    assert meta["method"] == "Key_Scattered_AI_Adaptive_LSB"
    assert meta["payload_bytes"] == len(payload)
    assert meta["altered_pixels"] > 0
    assert "key_fingerprint" in meta

    # Extract with correct key
    extracted_bytes, ext_meta = KeyScatteredAiLSB.extract(stego, stego_key, block_size=16)
    assert ext_meta["crc_verified"] is True
    assert extracted_bytes == payload
    assert extracted_bytes.decode("utf-8") == secret_text


def test_key_scattered_ai_lsb_extract_wrong_key_fails():
    cover = _create_synthetic_test_image(64, 64)
    payload = b"Confidential financial telemetry"
    correct_key = "AliceSecretPasscode#1"
    wrong_key = "EveUnauthorizedGuess#2"

    stego, _ = KeyScatteredAiLSB.embed(cover, payload, correct_key, block_size=16)

    # Extraction with wrong key MUST fail
    with pytest.raises((NoStegoPayloadFoundError, PayloadCorruptedError)):
        KeyScatteredAiLSB.extract(stego, wrong_key, block_size=16)


def test_key_scattered_ai_lsb_smooth_blocks_preserved():
    cover = _create_synthetic_test_image(64, 64)
    payload = b"Small message fitting into high texture"
    key = "PreservationKeyTest"

    stego, meta = KeyScatteredAiLSB.embed(cover, payload, key, block_size=16)
    assert meta["blocks_preserved_smooth"] >= 1

    # Check that top half (smooth region) is 100% identical between cover and stego
    top_half_cover = cover[:32, :, :]
    top_half_stego = stego[:32, :, :]
    np.testing.assert_array_equal(top_half_cover, top_half_stego)


def test_key_scattered_ai_lsb_clean_image_raises_error():
    cover = _create_synthetic_test_image(64, 64)
    with pytest.raises(NoStegoPayloadFoundError):
        KeyScatteredAiLSB.extract(cover, "AnyKey", block_size=16)


def test_key_scattered_ai_lsb_oversized_payload_raises_capacity_error():
    cover = _create_synthetic_test_image(32, 32)
    oversized = b"A" * 2000
    with pytest.raises(CapacityExceededError):
        KeyScatteredAiLSB.embed(cover, oversized, "SecretKey", block_size=16)


# -------------------------------------------------------------------------
# Integration Tests: FastAPI Endpoints
# -------------------------------------------------------------------------

@pytest.mark.anyio
async def test_api_scatter_capacity_endpoint():
    cover = _create_synthetic_test_image(64, 64)
    png_bytes = _png_bytes_from_array(cover)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        files = {"image": ("test.png", png_bytes, "image/png")}
        resp = await client.post("/scatter/capacity", files=files, data={"block_size": "16"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["total_blocks"] == 16
    assert data["method"] == "Key_Scattered_AI_Adaptive_LSB"


@pytest.mark.anyio
async def test_api_scatter_encode_and_decode_endpoint():
    cover = _create_synthetic_test_image(64, 64)
    png_bytes = _png_bytes_from_array(cover)
    secret_text = "FastAPI Key-Scattered Stego Lifecycle Verification 🔐"
    stego_key = "FastApiTestKey999"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Encode
        encode_files = {"image": ("cover.png", png_bytes, "image/png")}
        encode_resp = await client.post(
            "/scatter/encode",
            files=encode_files,
            data={"message": secret_text, "stego_key": stego_key, "block_size": "16"},
        )
        assert encode_resp.status_code == 200
        assert encode_resp.headers["X-Stego-Method"] == "Key_Scattered_AI_Adaptive_LSB"
        stego_png_bytes = encode_resp.content

        # 2. Decode with correct key
        decode_files = {"image": ("stego.png", stego_png_bytes, "image/png")}
        decode_resp = await client.post(
            "/scatter/decode",
            files=decode_files,
            data={"stego_key": stego_key, "block_size": "16"},
        )
        assert decode_resp.status_code == 200
        decode_data = decode_resp.json()
        assert decode_data["crc_verified"] is True
        assert decode_data["payload_text"] == secret_text

        # 3. Decode with incorrect key should fail with 404 or 422
        decode_fail_resp = await client.post(
            "/scatter/decode",
            files={"image": ("stego.png", stego_png_bytes, "image/png")},
            data={"stego_key": "WrongAttackerKey", "block_size": "16"},
        )
        assert decode_fail_resp.status_code in [404, 422]


@pytest.mark.anyio
async def test_api_scatter_verify_key_endpoint():
    cover = _create_synthetic_test_image(64, 64)
    png_bytes = _png_bytes_from_array(cover)
    stego_key = "AuthKeyVerificationTest"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Encode
        encode_resp = await client.post(
            "/scatter/encode",
            files={"image": ("cover.png", png_bytes, "image/png")},
            data={"message": "Verification message payload", "stego_key": stego_key, "block_size": "16"},
        )
        stego_png_bytes = encode_resp.content

        # Verify correct key
        v_resp_ok = await client.post(
            "/scatter/verify-key",
            files={"image": ("stego.png", stego_png_bytes, "image/png")},
            data={"stego_key": stego_key, "block_size": "16"},
        )
        assert v_resp_ok.status_code == 200
        assert v_resp_ok.json()["valid_key"] is True

        # Verify wrong key
        v_resp_bad = await client.post(
            "/scatter/verify-key",
            files={"image": ("stego.png", stego_png_bytes, "image/png")},
            data={"stego_key": "BogusKeyAttempt", "block_size": "16"},
        )
        assert v_resp_bad.status_code == 200
        assert v_resp_bad.json()["valid_key"] is False
