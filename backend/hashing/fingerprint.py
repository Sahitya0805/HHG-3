"""Cryptographic hashing and canonical fingerprint generation module."""

import json
import hashlib
from typing import Dict, Any, Tuple


class FingerprintEngine:
    """Generates and verifies deterministic SHA-256 cryptographic fingerprints."""

    @staticmethod
    def canonicalize(data: Dict[str, Any]) -> str:
        """
        Produce deterministic, normalized JSON representation:
        - Sorted keys
        - Compact separators (no extra whitespace)
        - UTF-8 representation
        """
        # Ensure only string/primitive values and sorted keys
        clean_dict = {}
        for k, v in data.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                clean_dict[str(k)] = v
            else:
                clean_dict[str(k)] = str(v)

        return json.dumps(clean_dict, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def generate_sha256(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate standard 256-bit SHA-256 hex digest from canonical metadata.
        """
        canonical_str = cls.canonicalize(data)
        encoded_bytes = canonical_str.encode("utf-8")
        hash_digest = hashlib.sha256(encoded_bytes).hexdigest()
        bytes32_hex = "0x" + hash_digest

        return {
            "algorithm": "SHA-256",
            "canonical_payload": canonical_str,
            "hash": hash_digest,
            "bytes32_hash": bytes32_hex,
            "byte_length": 32,
        }

    @classmethod
    def test_tamper(
        cls,
        original_metadata: Dict[str, Any],
        tampered_metadata: Dict[str, Any],
        on_chain_hash: str,
    ) -> Dict[str, Any]:
        """
        Demonstrates tamper detection:
        Recalculates SHA-256 on modified metadata and compares against the on-chain stored hash.
        """
        orig_res = cls.generate_sha256(original_metadata)
        tamp_res = cls.generate_sha256(tampered_metadata)

        normalized_on_chain = on_chain_hash.lower()
        if not normalized_on_chain.startswith("0x"):
            normalized_on_chain = "0x" + normalized_on_chain

        matches_original = (orig_res["bytes32_hash"].lower() == normalized_on_chain)
        matches_tampered = (tamp_res["bytes32_hash"].lower() == normalized_on_chain)

        is_tampered = (orig_res["hash"] != tamp_res["hash"])

        # Identify which fields were altered
        altered_fields = []
        for k in set(original_metadata.keys()).union(set(tampered_metadata.keys())):
            if original_metadata.get(k) != tampered_metadata.get(k):
                altered_fields.append({
                    "field": k,
                    "original_value": original_metadata.get(k),
                    "tampered_value": tampered_metadata.get(k),
                })

        return {
            "original_hash": orig_res["bytes32_hash"],
            "tampered_hash": tamp_res["bytes32_hash"],
            "on_chain_hash": normalized_on_chain,
            "is_tampered": is_tampered,
            "tamper_detected": not matches_tampered,
            "status": "TAMPER_DETECTED" if not matches_tampered else "HASH_MATCH",
            "message": "❌ HASH MISMATCH — DATA TAMPERED" if not matches_tampered else "✓ Data has not changed",
            "altered_fields": altered_fields,
        }
