"""Comprehensive End-to-End Verification Script for Phases 0 through 9."""
import io
import numpy as np
from PIL import Image
from fastapi.testclient import TestClient

from app.main import app
from app.crypto.aes_engine import AESCipher
from app.crypto.rsa_engine import RSACipher
from app.crypto.hybrid_cipher import HybridCipher
from app.image.loader import ImageLoader
from app.image.feature_extractor import FeatureExtractor
from app.image.metrics import (
    compute_all_metrics,
    compute_mse,
    compute_psnr,
    compute_ssim,
    compute_payload_ber,
)
from app.steganography.baseline_lsb import BaselineLSB


def main():
    print("=================================================================")
    print("  AI-BASED ADAPTIVE STEGANOGRAPHY SYSTEM — COMPREHENSIVE AUDIT   ")
    print("=================================================================\n")

    # 1. Cryptography Primitives
    print("--- 1. Cryptography Engine (Phases 5 & 6) ---")
    secret_msg = "FINAL_YEAR_RESEARCH_PROJECT_2026_CONFIDENTIAL"
    pub_pem, priv_pem = RSACipher.generate_key_pair(key_size=2048)
    envelope = HybridCipher.encrypt(secret_msg.encode("utf-8"), pub_pem)
    recovered_bytes = HybridCipher.decrypt(envelope, priv_pem)
    assert recovered_bytes.decode("utf-8") == secret_msg, "Hybrid decryption failed"
    print("  [PASS] AES-256-GCM + RSA-OAEP Hybrid Envelope: 100% Lossless Roundtrip")

    # 2. Image Processing & Spatial Feature Extraction
    print("\n--- 2. Image Feature Extraction Engine (Phase 8) ---")
    cover_img = np.random.randint(50, 200, (64, 64, 3), dtype=np.uint8)
    png_bytes = ImageLoader.save_image_to_bytes(cover_img)
    loaded_pixels, (w, h) = ImageLoader.load_image(png_bytes)
    assert (w, h) == (64, 64), "Image dimension mismatch"
    analysis = FeatureExtractor.analyze_image(loaded_pixels, block_size=16)
    print(f"  [PASS] Image Loaded: {w}x{h} PNG")
    print(f"  [PASS] Mean Shannon Entropy: {analysis.global_features['entropy']:.2f} bits")
    print(f"  [PASS] Mean Sobel Gradient: {analysis.global_features['sobel_gradient_mean']:.2f}")
    print(f"  [PASS] Mean Canny Edge Density: {analysis.global_features['canny_edge_density']:.4f}")
    print(f"  [PASS] 16x16 Spatial Blocks Extracted: {len(analysis.blocks)} blocks")

    # 3. Baseline Spatial LSB Steganography Engine
    print("\n--- 3. Spatial LSB Steganography Engine (Phase 7) ---")
    envelope_bytes = envelope.to_bytes()
    stego_pixels, meta = BaselineLSB.embed(loaded_pixels, envelope_bytes)
    stego_png = ImageLoader.save_image_to_bytes(stego_pixels)
    extracted_envelope_bytes, extract_meta = BaselineLSB.extract(stego_pixels)
    assert extract_meta["crc_verified"] is True, "CRC-32 verification failed"
    decrypted_secret = HybridCipher.decrypt(extracted_envelope_bytes, priv_pem)
    assert decrypted_secret.decode("utf-8") == secret_msg, "Extracted secret mismatch"
    print(f"  [PASS] Payload Embedded: {meta['payload_bytes']} bytes")
    print(f"  [PASS] Capacity Utilization: {meta['capacity_used_percent']}%")
    print(f"  [PASS] CRC-32 Frame Integrity: Verified True")
    print(f"  [PASS] Secret Recovered: '{decrypted_secret.decode('utf-8')}'")

    # 4. Image Quality Metrics Engine
    print("\n--- 4. Full-Reference Quality Metrics (Phase 9) ---")
    metrics = compute_all_metrics(
        cover_img=loaded_pixels,
        stego_img=stego_pixels,
        original_payload=secret_msg,
        recovered_payload=decrypted_secret.decode("utf-8"),
        payload_bytes=len(secret_msg),
    )
    print(f"  [PASS] Mean Squared Error (MSE): {metrics.mse:.6f}")
    print(f"  [PASS] Peak Signal-to-Noise Ratio (PSNR): {metrics.psnr_db:.2f} dB")
    print(f"  [PASS] Structural Similarity (SSIM): {metrics.ssim:.6f}")
    print(f"  [PASS] Image LSB Alteration Rate: {(metrics.image_lsb_ber * 100):.2f}%")
    print(f"  [PASS] Secret Payload BER: {metrics.payload_ber:.6f} (0.00% errors)")
    print(f"  [PASS] Perceptual Rating: {metrics.quality_rating} (Imperceptible={metrics.is_imperceptible})")
    assert metrics.psnr_db >= 40.0, f"PSNR must be >= 40 dB, got {metrics.psnr_db}"
    assert metrics.ssim >= 0.98, f"SSIM must be >= 0.98, got {metrics.ssim}"
    assert metrics.payload_ber == 0.0, "Payload BER must be 0.0"

    # 5. FastAPI REST API Lifecycle
    print("\n--- 5. FastAPI Endpoints Integration ---")
    client = TestClient(app)

    # /health
    r_health = client.get("/health")
    assert r_health.status_code == 200 and r_health.json()["status"] == "healthy"
    print("  [PASS] GET /health -> 200 OK (All components healthy)")

    # /capacity
    r_cap = client.post("/capacity", files={"image": ("cover.png", png_bytes, "image/png")})
    assert r_cap.status_code == 200
    print(f"  [PASS] POST /capacity -> 200 OK (Max capacity: {r_cap.json()['max_payload_bytes']} bytes)")

    # /encode
    r_enc = client.post(
        "/encode",
        files={"image": ("cover.png", png_bytes, "image/png")},
        data={"message": "EndToEnd_Verification_2026"},
    )
    assert r_enc.status_code == 200
    assert "x-metric-psnr" in r_enc.headers
    assert "x-metric-ssim" in r_enc.headers
    stego_api_bytes = r_enc.content
    print(f"  [PASS] POST /encode -> 200 OK (Headers: PSNR={r_enc.headers['x-metric-psnr']} dB, SSIM={r_enc.headers['x-metric-ssim']})")

    # /decode
    r_dec = client.post("/decode", files={"image": ("stego.png", stego_api_bytes, "image/png")})
    assert r_dec.status_code == 200 and r_dec.json()["payload_text"] == "EndToEnd_Verification_2026"
    print("  [PASS] POST /decode -> 200 OK (Payload exact match)")

    # /analyze
    r_ana = client.post("/analyze", files={"image": ("cover.png", png_bytes, "image/png")}, data={"block_size": "16"})
    assert r_ana.status_code == 200
    print("  [PASS] POST /analyze -> 200 OK")

    # /metrics/compare
    r_met = client.post(
        "/metrics/compare",
        files={
            "cover_image": ("cover.png", png_bytes, "image/png"),
            "stego_image": ("stego.png", stego_api_bytes, "image/png"),
        },
        data={
            "original_payload": "EndToEnd_Verification_2026",
            "recovered_payload": "EndToEnd_Verification_2026",
            "record_experiment": "true",
            "method_name": "Full_Verification_Audit",
        },
    )
    assert r_met.status_code == 200
    print(f"  [PASS] POST /metrics/compare -> 200 OK (PSNR={r_met.json()['psnr_db']:.2f} dB, Rating={r_met.json()['quality_rating']})")

    # /metrics/history
    r_his = client.get("/metrics/history")
    assert r_his.status_code == 200 and len(r_his.json()) > 0
    print(f"  [PASS] GET /metrics/history -> 200 OK ({len(r_his.json())} audit log records retrieved)")

    print("\n=================================================================")
    print("  VERIFICATION RESULT: ALL FUNCTIONALITIES WORK AS INTENDED!     ")
    print("=================================================================\n")


if __name__ == "__main__":
    main()
