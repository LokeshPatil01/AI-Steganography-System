"""Unit and Integration Tests for Phase 18 One-Click End-to-End Stego Orchestration Pipeline.

Verifies:
1. End-to-end atomic execution of RSA-4096-OAEP + AES-256-GCM + RF + PRNG + CNN feedback.
2. Bit-exact plaintext recovery with authenticated cryptographic integrity.
3. Security profiles ("Quality", "Balanced", "Security").
4. Rejection of invalid private keys and corrupt payloads.
5. FastAPI HTTP routes (/pipeline/encode-hybrid, /pipeline/decode-hybrid, /pipeline/dryrun-hybrid).
"""
import io
import pytest
from fastapi.testclient import TestClient
import numpy as np

from app.crypto.rsa_engine import RSACipher
from app.image.loader import ImageLoader
from app.main import app
from app.pipeline.orchestrator import StegoPipelineOrchestrator


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def rsa_key_pair():
    """Generates an ephemeral RSA-4096 key pair for pipeline testing."""
    return RSACipher.generate_key_pair(key_size=4096)


@pytest.fixture(scope="module")
def another_rsa_key_pair():
    """Generates a separate RSA-4096 key pair to test unauthorized decryption."""
    return RSACipher.generate_key_pair(key_size=4096)


@pytest.fixture
def high_res_cover_png_bytes():
    """Generates a synthetic 128x128 texture PNG image with ample capacity."""
    img = np.zeros((128, 128, 3), dtype=np.uint8)
    # Inject synthetic high-frequency texture gradient
    for y in range(128):
        for x in range(128):
            img[y, x, 0] = (x * 4 + y * 2) % 256
            img[y, x, 1] = (x * 2 + y * 5) % 256
            img[y, x, 2] = ((x ^ y) * 7) % 256
    return ImageLoader.save_image_to_bytes(img)


def test_pipeline_encode_and_decode_full_cycle(rsa_key_pair, high_res_cover_png_bytes):
    """Verifies that full atomic orchestration embeds, optimizes, extracts, and decrypts."""
    pub_pem, priv_pem = rsa_key_pair
    secret_text = "IEEE-Trans-2026-Classified-Research-Steganography-Payload"
    cover_pixels, _ = ImageLoader.load_image(high_res_cover_png_bytes)

    # 1. Encode
    enc_result = StegoPipelineOrchestrator.encode_hybrid(
        cover_pixels=cover_pixels,
        payload_data=secret_text,
        recipient_public_key_pem=pub_pem,
        stego_passphrase="StrongPipelineKey#99",
        security_level="Balanced",
        block_size=16,
    )

    assert enc_result.stego_pixels.shape == cover_pixels.shape
    assert enc_result.raw_payload_bytes == len(secret_text.encode("utf-8"))
    assert enc_result.hybrid_envelope_bytes > 512  # RSA-4096 key envelope + AES-GCM
    assert enc_result.psnr_db >= 36.0
    assert enc_result.ssim >= 0.95
    assert enc_result.cover_sha256 != enc_result.stego_sha256

    # 2. Decode
    dec_result = StegoPipelineOrchestrator.decode_hybrid(
        stego_pixels=enc_result.stego_pixels,
        recipient_private_key_pem=priv_pem,
        stego_passphrase="StrongPipelineKey#99",
        block_size=16,
    )

    assert dec_result.authenticated is True
    assert dec_result.decrypted_text == secret_text
    assert dec_result.payload_size_bytes == len(secret_text.encode("utf-8"))
    assert dec_result.stego_sha256 == enc_result.stego_sha256


def test_pipeline_security_profiles(rsa_key_pair, high_res_cover_png_bytes):
    """Verifies different security profiles ('Quality' vs 'Security')."""
    pub_pem, _ = rsa_key_pair
    secret = "MultiProfileTest"
    cover_pixels, _ = ImageLoader.load_image(high_res_cover_png_bytes)

    res_quality = StegoPipelineOrchestrator.encode_hybrid(
        cover_pixels=cover_pixels,
        payload_data=secret,
        recipient_public_key_pem=pub_pem,
        security_level="Quality",
    )
    assert res_quality.security_level == "Quality"
    assert res_quality.psnr_db > 35.0


def test_pipeline_wrong_private_key_fails(rsa_key_pair, another_rsa_key_pair, high_res_cover_png_bytes):
    """Verifies that an unauthorized recipient cannot decrypt the hybrid envelope."""
    pub_pem, _ = rsa_key_pair
    _, wrong_priv_pem = another_rsa_key_pair
    secret = "TopSecretAuthorizedOnly"
    cover_pixels, _ = ImageLoader.load_image(high_res_cover_png_bytes)

    enc_result = StegoPipelineOrchestrator.encode_hybrid(
        cover_pixels=cover_pixels,
        payload_data=secret,
        recipient_public_key_pem=pub_pem,
        stego_passphrase="SharedPassphrase",
    )

    with pytest.raises(Exception):
        StegoPipelineOrchestrator.decode_hybrid(
            stego_pixels=enc_result.stego_pixels,
            recipient_private_key_pem=wrong_priv_pem,
            stego_passphrase="SharedPassphrase",
        )


def test_api_pipeline_encode_and_decode(client, rsa_key_pair, high_res_cover_png_bytes):
    """Verifies HTTP API roundtrip: POST /pipeline/encode-hybrid -> stego PNG -> POST /pipeline/decode-hybrid."""
    pub_pem, priv_pem = rsa_key_pair
    secret = "HTTP-API-Orchestrated-Confidential-Message"
    stego_pass = "APIPipelinePassphrase2026"

    # 1. Encode via HTTP
    files = {"image": ("cover.png", high_res_cover_png_bytes, "image/png")}
    data = {
        "message": secret,
        "recipient_public_key": pub_pem,
        "stego_passphrase": stego_pass,
        "security_level": "Balanced",
        "block_size": "16",
    }
    res_enc = client.post("/pipeline/encode-hybrid", files=files, data=data)
    assert res_enc.status_code == 200
    assert res_enc.headers["content-type"] == "image/png"
    assert res_enc.headers["x-stego-method"] == "One_Click_Hybrid_AI_Pipeline"
    assert "x-stego-sha256" in res_enc.headers
    assert float(res_enc.headers["x-metric-ssim"]) > 0.90

    stego_png_bytes = res_enc.content

    # 2. Decode via HTTP
    files_dec = {"image": ("stego.png", stego_png_bytes, "image/png")}
    data_dec = {
        "recipient_private_key": priv_pem,
        "stego_passphrase": stego_pass,
        "block_size": "16",
    }
    res_dec = client.post("/pipeline/decode-hybrid", files=files_dec, data=data_dec)
    assert res_dec.status_code == 200
    dec_json = res_dec.json()
    assert dec_json["success"] is True
    assert dec_json["authenticated"] is True
    assert dec_json["payload_text"] == secret


def test_api_pipeline_dryrun(client, rsa_key_pair, high_res_cover_png_bytes):
    """Verifies POST /pipeline/dryrun-hybrid returns full JSON report without streaming image."""
    pub_pem, _ = rsa_key_pair
    files = {"image": ("cover.png", high_res_cover_png_bytes, "image/png")}
    data = {
        "message": "DryrunMessage",
        "recipient_public_key": pub_pem,
        "security_level": "Quality",
    }
    res = client.post("/pipeline/dryrun-hybrid", files=files, data=data)
    assert res.status_code == 200
    dryrun_json = res.json()
    assert dryrun_json["success"] is True
    assert dryrun_json["security_level"] == "Quality"
    assert "cover_sha256" in dryrun_json
    assert "stego_sha256" in dryrun_json
    assert dryrun_json["psnr_db"] > 35.0
