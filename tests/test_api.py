"""Integration tests for all FastAPI REST endpoints."""

import os
from pathlib import Path
from fastapi.testclient import TestClient
from backend import main
from backend.main import app

client = TestClient(app)


class FixtureSearcher:
    def search(self, image_bytes: bytes, filename: str = "query.jpg", search_query=None):
        return [
            {
                "url": "https://instagram.com/p/public-event-99",
                "title": "Hackathon Demo Post",
                "source": "Instagram",
                "image_url": "https://example.com/demo_face.jpg",
                "snippet": "Testing blockchain immutability",
            }
        ]


class FakeBlockchainVerifier:
    network_info = {
        "mode": "local_anvil_evm",
        "chain_id": 31337,
        "contract_address": "0x0000000000000000000000000000000000000001",
        "wallet_address": "0x0000000000000000000000000000000000000002",
        "connected": True,
        "error": None,
    }

    def __init__(self):
        self.records = {}

    def store_hash(self, hash_str):
        normalized = "0x" + hash_str.lower().removeprefix("0x")
        self.records[normalized] = True
        return {
            "success": True,
            "transaction_hash": "0x" + "1" * 64,
            "block_number": 1,
            "gas_used": 47218,
            "submitter": self.network_info["wallet_address"],
            "stored_hash": normalized,
            "timestamp": 1,
            "mode": "local_anvil_evm",
            "contract_address": self.network_info["contract_address"],
        }

    def verify_hash(self, hash_str):
        normalized = "0x" + hash_str.lower().removeprefix("0x")
        return {
            "verified": normalized in self.records,
            "on_chain_hash": normalized if normalized in self.records else None,
            "timestamp": 1 if normalized in self.records else None,
            "submitter": self.network_info["wallet_address"] if normalized in self.records else None,
            "transaction_hash": "0x" + "1" * 64 if normalized in self.records else None,
            "block_number": 1 if normalized in self.records else None,
            "mode": "local_anvil_evm",
            "contract_address": self.network_info["contract_address"],
        }


def _sample_bytes():
    return Path("samples/demo_face.jpg").read_bytes()


def _patch_search(monkeypatch):
    main.search_orchestrator.provider = FixtureSearcher()
    monkeypatch.setattr(
        main.search_orchestrator.parser,
        "_download_image_bytes",
        lambda image_url: _sample_bytes(),
    )


def test_api_health():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "blockchain" in data
    assert "search_provider" in data


def test_api_face_detection():
    sample_path = "samples/demo_face.jpg"
    assert os.path.exists(sample_path)

    with open(sample_path, "rb") as f:
        response = client.post("/api/face", files={"image": ("demo.jpg", f, "image/jpeg")})

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["face_detected"] is True
    assert data["embedding_generated"] is True
    assert data["embedding_dimensions"] == 512
    assert len(data["embedding"]) == 512


def test_api_search_and_hash(monkeypatch):
    _patch_search(monkeypatch)
    main.blockchain_verifier = FakeBlockchainVerifier()

    # 1. Search with dummy embedding
    detector = main.detector
    encoder = main.encoder
    img = detector.load_image(_sample_bytes())
    face = detector.detect_faces(img)
    emb_res = encoder.generate_embedding_from_landmarks(
        img,
        face.get("primary_landmarks"),
    )
    search_resp = client.post(
        "/api/search",
        json={
            "embedding": emb_res["embedding"],
            "embedding_model": emb_res["model"],
            "image_b64": "data:image/jpeg;base64,full-image",
            "face_crop_b64": face["primary_crop_b64"],
            "strict_face_match": False,
        },
    )
    assert search_resp.status_code == 200
    sdata = search_resp.json()
    assert sdata["success"] is True
    assert len(sdata["candidates"]) > 0
    assert sdata["best_match"] is not None
    assert sdata["metadata"] is not None

    metadata = sdata["metadata"]

    # 2. Hash generation
    hash_resp = client.post("/api/hash", json={"metadata": metadata})
    assert hash_resp.status_code == 200
    hdata = hash_resp.json()
    assert hdata["algorithm"] == "SHA-256"
    assert len(hdata["hash"]) == 64
    assert hdata["bytes32_hash"].startswith("0x")

    # 3. Store on blockchain
    store_resp = client.post("/api/blockchain/store", json={"hash": hdata["hash"]})
    assert store_resp.status_code == 200
    bdata = store_resp.json()
    assert bdata["success"] is True
    assert bdata["transaction_hash"].startswith("0x")

    # 4. Verify on blockchain
    verify_resp = client.get(f"/api/blockchain/verify?hash={hdata['hash']}")
    assert verify_resp.status_code == 200
    vdata = verify_resp.json()
    assert vdata["verified"] is True
    assert vdata["on_chain_hash"].lower().endswith(hdata["hash"].lower())

    # 5. Tamper demonstration
    tampered_meta = dict(metadata)
    tampered_meta["caption"] = "Tampered unauthorized text modification"

    tamper_resp = client.post(
        "/api/tamper-test",
        json={
            "original_metadata": metadata,
            "tampered_metadata": tampered_meta,
            "on_chain_hash": vdata["on_chain_hash"],
        },
    )
    assert tamper_resp.status_code == 200
    tdata = tamper_resp.json()
    assert tdata["is_tampered"] is True
    assert tdata["tamper_detected"] is True
    assert tdata["status"] == "TAMPER_DETECTED"


def test_api_end_to_end_pipeline(monkeypatch):
    _patch_search(monkeypatch)
    main.blockchain_verifier = FakeBlockchainVerifier()

    sample_path = "samples/demo_face.jpg"
    with open(sample_path, "rb") as f:
        response = client.post(
            "/api/pipeline",
            files={"image": ("demo.jpg", f, "image/jpeg")},
            data={"strict_face_match": "false"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "face" in data
    assert "search" in data
    assert "metadata" in data
    assert "fingerprint" in data
    assert "blockchain" in data
    assert "verification" in data
    assert data["verification"]["verified"] is True
    assert "provider_results" in data["search"]
    assert "verified_candidates" in data["search"]
