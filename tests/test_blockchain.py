"""Unit tests for smart contract registration and verification."""

import pytest
from backend.blockchain.verifier import BlockchainVerifier
from backend.hashing.fingerprint import FingerprintEngine


def test_blockchain_storage_and_verification():
    verifier = BlockchainVerifier()

    test_data = {
        "source": "Instagram",
        "url": "https://instagram.com/p/public-event-99",
        "title": "Hackathon Demo Post",
        "caption": "Testing blockchain immutability",
    }
    fingerprint = FingerprintEngine.generate_sha256(test_data)["hash"]

    # 1. Store hash on blockchain
    store_res = verifier.store_hash(fingerprint)
    assert store_res["success"] is True
    assert "transaction_hash" in store_res
    assert store_res["transaction_hash"].startswith("0x")
    assert store_res["block_number"] > 0

    # 2. Verify hash on blockchain
    verify_res = verifier.verify_hash(fingerprint)
    assert verify_res["verified"] is True
    assert verify_res["on_chain_hash"].lower().endswith(fingerprint.lower())
    assert verify_res["timestamp"] > 0
    assert verify_res["submitter"].startswith("0x")


def test_blockchain_nonexistent_hash():
    verifier = BlockchainVerifier()
    random_hash = "000000000000000000000000000000000000000000000000000000000000dead"
    res = verifier.verify_hash(random_hash)
    assert res["verified"] is False
    assert res["on_chain_hash"] is None
