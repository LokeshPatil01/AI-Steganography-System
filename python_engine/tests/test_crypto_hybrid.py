"""Unit tests for RSA-4096 and Hybrid RSA+AES envelope encryption engine."""
import os
import pytest

from app.crypto.aes_engine import IntegrityError
from app.crypto.hybrid_cipher import (
    HybridCipher,
    HybridEncryptionError,
    HybridEnvelope,
)
from app.crypto.rsa_engine import RSACipher, RSAError

@pytest.fixture(scope="module")
def recipient_keypair():
    """Generates an RSA-4096 key pair for the test module."""
    public_pem, private_pem = RSACipher.generate_key_pair(2048)  # 2048-bit for fast unit tests
    return public_pem, private_pem

@pytest.fixture(scope="module")
def second_recipient_keypair():
    """Generates a second key pair to test unauthorized decryption attempts."""
    public_pem, private_pem = RSACipher.generate_key_pair(2048)
    return public_pem, private_pem

def test_rsa_key_generation_and_fingerprint(recipient_keypair):
    public_pem, private_pem = recipient_keypair

    assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")
    assert private_pem.startswith("-----BEGIN PRIVATE KEY-----")

    fp = RSACipher.get_public_key_fingerprint(public_pem)
    assert fp.startswith("SHA256:")
    assert len(fp) == 7 + 64

def test_rsa_encrypt_and_decrypt_key_roundtrip(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    raw_aes_key = os.urandom(32)

    encrypted_key = RSACipher.encrypt_key(raw_aes_key, public_pem)
    assert len(encrypted_key) == 256  # 2048 bits / 8 = 256 bytes

    decrypted_key = RSACipher.decrypt_key(encrypted_key, private_pem)
    assert decrypted_key == raw_aes_key

def test_rsa_decrypt_with_wrong_private_key_fails(recipient_keypair, second_recipient_keypair):
    public_pem, _ = recipient_keypair
    _, wrong_private_pem = second_recipient_keypair

    raw_aes_key = os.urandom(32)
    encrypted_key = RSACipher.encrypt_key(raw_aes_key, public_pem)

    with pytest.raises(RSAError):
        RSACipher.decrypt_key(encrypted_key, wrong_private_pem)

def test_hybrid_encrypt_and_decrypt_string_roundtrip(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    secret_text = "Top-Secret Military Coordinates: 37°14'06\"N 115°48'40\"W. Research 2026."

    envelope = HybridCipher.encrypt(secret_text, public_pem)

    assert isinstance(envelope, HybridEnvelope)
    assert len(envelope.nonce) == 12
    assert len(envelope.tag) == 16
    assert envelope.ciphertext != secret_text.encode("utf-8")
    assert envelope.recipient_fingerprint is not None

    decrypted_text = HybridCipher.decrypt_to_str(envelope, private_pem)
    assert decrypted_text == secret_text

def test_hybrid_encrypt_and_decrypt_binary_roundtrip(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    binary_data = os.urandom(1024 * 32)  # 32 KB payload

    envelope = HybridCipher.encrypt(binary_data, public_pem)
    recovered_data = HybridCipher.decrypt(envelope, private_pem)

    assert recovered_data == binary_data

def test_hybrid_envelope_binary_serialization_roundtrip(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    message = "Envelope binary serialization test for image steganography packaging"

    envelope = HybridCipher.encrypt(message, public_pem)
    raw_bytes = envelope.to_bytes()

    assert raw_bytes.startswith(b"STEGHYB1")

    # Deserialize back from wire bytes
    unpacked = HybridEnvelope.from_bytes(raw_bytes)
    assert unpacked.encrypted_aes_key == envelope.encrypted_aes_key
    assert unpacked.nonce == envelope.nonce
    assert unpacked.tag == envelope.tag
    assert unpacked.ciphertext == envelope.ciphertext
    assert unpacked.recipient_fingerprint == envelope.recipient_fingerprint

    # Decrypt directly from serialized bytes
    decrypted = HybridCipher.decrypt_to_str(raw_bytes, private_pem)
    assert decrypted == message

def test_tampered_ciphertext_fails_with_integrity_error(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    envelope = HybridCipher.encrypt("Sensitive message to tamper", public_pem)

    # Flip 1 bit in ciphertext
    corrupted_ciphertext = bytearray(envelope.ciphertext)
    corrupted_ciphertext[0] ^= 0x01

    tampered_envelope = HybridEnvelope(
        encrypted_aes_key=envelope.encrypted_aes_key,
        nonce=envelope.nonce,
        tag=envelope.tag,
        ciphertext=bytes(corrupted_ciphertext),
        recipient_fingerprint=envelope.recipient_fingerprint,
    )

    with pytest.raises(IntegrityError):
        HybridCipher.decrypt(tampered_envelope, private_pem)

def test_tampered_tag_fails_with_integrity_error(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    envelope = HybridCipher.encrypt("Sensitive message to tamper tag", public_pem)

    corrupted_tag = bytearray(envelope.tag)
    corrupted_tag[0] ^= 0x01

    tampered_envelope = HybridEnvelope(
        encrypted_aes_key=envelope.encrypted_aes_key,
        nonce=envelope.nonce,
        tag=bytes(corrupted_tag),
        ciphertext=envelope.ciphertext,
        recipient_fingerprint=envelope.recipient_fingerprint,
    )

    with pytest.raises(IntegrityError):
        HybridCipher.decrypt(tampered_envelope, private_pem)

def test_tampered_encrypted_aes_key_fails(recipient_keypair):
    public_pem, private_pem = recipient_keypair
    envelope = HybridCipher.encrypt("Sensitive message to tamper key", public_pem)

    # Corrupt encrypted AES key
    corrupted_key = bytearray(envelope.encrypted_aes_key)
    corrupted_key[0] ^= 0x01

    tampered_envelope = HybridEnvelope(
        encrypted_aes_key=bytes(corrupted_key),
        nonce=envelope.nonce,
        tag=envelope.tag,
        ciphertext=envelope.ciphertext,
        recipient_fingerprint=envelope.recipient_fingerprint,
    )

    with pytest.raises(HybridEncryptionError):
        HybridCipher.decrypt(tampered_envelope, private_pem)

def test_unauthorized_recipient_cannot_decrypt(recipient_keypair, second_recipient_keypair):
    public_pem_a, _ = recipient_keypair
    _, private_pem_b = second_recipient_keypair

    envelope = HybridCipher.encrypt("Confidential to User A", public_pem_a)

    with pytest.raises(HybridEncryptionError):
        HybridCipher.decrypt(envelope, private_pem_b)

def test_invalid_magic_header_fails_deserialization():
    corrupted_bytes = b"BADMAGIC" + os.urandom(100)
    with pytest.raises(HybridEncryptionError) as exc_info:
        HybridEnvelope.from_bytes(corrupted_bytes)
    assert "Invalid envelope magic header" in str(exc_info.value)
