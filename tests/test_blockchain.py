"""Unit tests for smart contract registration and verification."""

import pytest
from web3 import Web3

from backend.blockchain.verifier import BlockchainVerifier
from backend.hashing.fingerprint import FingerprintEngine

ANVIL_RPC_URL = "http://127.0.0.1:8545"
ANVIL_PRIVATE_KEY = "0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"


def _require_anvil():
    w3 = Web3(Web3.HTTPProvider(ANVIL_RPC_URL, request_kwargs={"timeout": 2}))
    if not w3.is_connected():
        pytest.skip("Local Anvil is not running at http://127.0.0.1:8545")


def test_blockchain_storage_and_verification():
    _require_anvil()
    verifier = BlockchainVerifier(
        rpc_url=ANVIL_RPC_URL,
        private_key=ANVIL_PRIVATE_KEY,
        contract_address="",
        auto_deploy=True,
    )

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
    _require_anvil()
    verifier = BlockchainVerifier(
        rpc_url=ANVIL_RPC_URL,
        private_key=ANVIL_PRIVATE_KEY,
        contract_address="",
        auto_deploy=True,
    )
    random_hash = "000000000000000000000000000000000000000000000000000000000000dead"
    res = verifier.verify_hash(random_hash)
    assert res["verified"] is False
    assert res["on_chain_hash"] is None


def test_blockchain_reports_missing_contract():
    verifier = BlockchainVerifier(
        rpc_url="http://127.0.0.1:1",
        private_key=ANVIL_PRIVATE_KEY,
        contract_address="",
        auto_deploy=False,
    )
    assert verifier.network_info["connected"] is False
    assert verifier.network_info["error"]
