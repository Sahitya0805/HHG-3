"""Unit tests for canonical serialization, SHA-256 fingerprinting, and tamper detection."""

import pytest
from backend.hashing.fingerprint import FingerprintEngine


def test_canonical_hash_determinism():
    # Dict with keys in different order
    meta_a = {
        "url": "https://instagram.com/p/test123",
        "title": "Conference Speaker",
        "source": "Instagram",
        "caption": "Great keynote today!",
    }

    meta_b = {
        "source": "Instagram",
        "caption": "Great keynote today!",
        "url": "https://instagram.com/p/test123",
        "title": "Conference Speaker",
    }

    res_a = FingerprintEngine.generate_sha256(meta_a)
    res_b = FingerprintEngine.generate_sha256(meta_b)

    assert res_a["hash"] == res_b["hash"]
    assert res_a["bytes32_hash"] == res_b["bytes32_hash"]
    assert len(res_a["hash"]) == 64
    assert res_a["bytes32_hash"].startswith("0x")


def test_tamper_detection():
    orig_meta = {
        "source": "Instagram",
        "url": "https://instagram.com/p/keynote2026",
        "title": "FaceTrace Keynote",
        "caption": "Great match today",
    }

    tampered_meta = {
        "source": "Instagram",
        "url": "https://instagram.com/p/keynote2026",
        "title": "FaceTrace Keynote",
        "caption": "Great match yesterday",  # Altered text
    }

    orig_hash = FingerprintEngine.generate_sha256(orig_meta)["bytes32_hash"]

    tamper_result = FingerprintEngine.test_tamper(
        original_metadata=orig_meta,
        tampered_metadata=tampered_meta,
        on_chain_hash=orig_hash,
    )

    assert tamper_result["is_tampered"] is True
    assert tamper_result["tamper_detected"] is True
    assert tamper_result["status"] == "TAMPER_DETECTED"
    assert len(tamper_result["altered_fields"]) == 1
    assert tamper_result["altered_fields"][0]["field"] == "caption"
    assert tamper_result["original_hash"] != tamper_result["tampered_hash"]
