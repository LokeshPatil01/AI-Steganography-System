"""Unit tests for AES-256-GCM authenticated encryption engine."""
import os
import pytest

from app.crypto.aes_engine import (
    AESCipher,
    AESEncryptedPayload,
    CryptoError,
    IntegrityError,
    InvalidKeyError,
)

def test_generate_key_returns_32_random_bytes():
    key1 = AESCipher.generate_key()
    key2 = AESCipher.generate_key()

    assert len(key1) == 32
    assert len(key2) == 32
    assert key1 != key2, "Keys must be cryptographically random and unique"

def test_encrypt_decrypt_string_roundtrip():
    key = AESCipher.generate_key()
    secret_message = "Confidential Steganography Payload: B.Tech Final Year 2026!"

    payload = AESCipher.encrypt(secret_message, key)

    assert isinstance(payload, AESEncryptedPayload)
    assert len(payload.nonce) == 12
    assert len(payload.tag) == 16
    assert payload.ciphertext != secret_message.encode("utf-8")

    decrypted = AESCipher.decrypt_to_str(payload, key)
    assert decrypted == secret_message

def test_encrypt_decrypt_binary_roundtrip():
    key = AESCipher.generate_key()
    binary_data = os.urandom(1024 * 64)  # 64 KB of random bytes

    payload = AESCipher.encrypt(binary_data, key)
    recovered = AESCipher.decrypt(payload, key)

    assert recovered == binary_data

def test_fresh_nonce_per_message():
    key = AESCipher.generate_key()
    message = "Static plaintext message"

    payload1 = AESCipher.encrypt(message, key)
    payload2 = AESCipher.encrypt(message, key)

    assert payload1.nonce != payload2.nonce, "Nonce must NEVER be reused with the same key"
    assert payload1.ciphertext != payload2.ciphertext, "Different nonces must yield different ciphertexts"

def test_tampered_ciphertext_raises_integrity_error():
    key = AESCipher.generate_key()
    payload = AESCipher.encrypt("Secret message", key)

    # Flip 1 bit in ciphertext
    corrupted_ciphertext = bytearray(payload.ciphertext)
    corrupted_ciphertext[0] ^= 0x01
    tampered_payload = AESEncryptedPayload(
        ciphertext=bytes(corrupted_ciphertext),
        nonce=payload.nonce,
        tag=payload.tag,
    )

    with pytest.raises(IntegrityError) as exc_info:
        AESCipher.decrypt(tampered_payload, key)
    assert "INTEGRITY VIOLATION" in str(exc_info.value)

def test_tampered_tag_raises_integrity_error():
    key = AESCipher.generate_key()
    payload = AESCipher.encrypt("Secret message", key)

    # Flip 1 bit in authentication tag
    corrupted_tag = bytearray(payload.tag)
    corrupted_tag[0] ^= 0x01
    tampered_payload = AESEncryptedPayload(
        ciphertext=payload.ciphertext,
        nonce=payload.nonce,
        tag=bytes(corrupted_tag),
    )

    with pytest.raises(IntegrityError):
        AESCipher.decrypt(tampered_payload, key)

def test_tampered_nonce_raises_integrity_error():
    key = AESCipher.generate_key()
    payload = AESCipher.encrypt("Secret message", key)

    corrupted_nonce = bytearray(payload.nonce)
    corrupted_nonce[0] ^= 0x01
    tampered_payload = AESEncryptedPayload(
        ciphertext=payload.ciphertext,
        nonce=bytes(corrupted_nonce),
        tag=payload.tag,
    )

    with pytest.raises(IntegrityError):
        AESCipher.decrypt(tampered_payload, key)

def test_wrong_key_fails_decryption():
    key1 = AESCipher.generate_key()
    key2 = AESCipher.generate_key()

    payload = AESCipher.encrypt("Top secret content", key1)

    with pytest.raises(IntegrityError):
        AESCipher.decrypt(payload, key2)

def test_invalid_key_length_raises_invalid_key_error():
    short_key = b"short_16_byte_pw"
    with pytest.raises(InvalidKeyError):
        AESCipher.encrypt("Test", short_key)

    with pytest.raises(InvalidKeyError):
        payload = AESEncryptedPayload(ciphertext=b"x", nonce=b"y" * 12, tag=b"z" * 16)
        AESCipher.decrypt(payload, short_key)

def test_serialization_to_bytes_and_from_bytes():
    key = AESCipher.generate_key()
    message = "Serialization wire test"
    aad = b"protocol_v1_header"

    payload = AESCipher.encrypt(message, key, associated_data=aad)
    serialized = payload.to_bytes()

    assert isinstance(serialized, bytes)

    deserialized = AESEncryptedPayload.from_bytes(serialized)
    assert deserialized.ciphertext == payload.ciphertext
    assert deserialized.nonce == payload.nonce
    assert deserialized.tag == payload.tag
    assert deserialized.associated_data == aad

    decrypted = AESCipher.decrypt_to_str(deserialized, key)
    assert decrypted == message

def test_authenticated_associated_data_validation():
    key = AESCipher.generate_key()
    message = "Sensitive banking record"
    correct_aad = b"Sender:Alice|Receiver:Bob"
    wrong_aad = b"Sender:Eve|Receiver:Bob"

    payload = AESCipher.encrypt(message, key, associated_data=correct_aad)

    # Decrypt with correct AAD -> Success
    decrypted = AESCipher.decrypt_to_str(payload, key, associated_data=correct_aad)
    assert decrypted == message

    # Decrypt with altered AAD -> Failure
    with pytest.raises(IntegrityError):
        AESCipher.decrypt(payload, key, associated_data=wrong_aad)

def test_empty_message_handling():
    key = AESCipher.generate_key()
    empty_msg = ""

    payload = AESCipher.encrypt(empty_msg, key)
    assert len(payload.ciphertext) == 0
    assert len(payload.tag) == 16

    recovered = AESCipher.decrypt_to_str(payload, key)
    assert recovered == empty_msg

def test_large_payload_handling():
    key = AESCipher.generate_key()
    large_payload = os.urandom(1024 * 1024 * 2)  # 2 Megabytes

    encrypted = AESCipher.encrypt(large_payload, key)
    decrypted = AESCipher.decrypt(encrypted, key)

    assert decrypted == large_payload
