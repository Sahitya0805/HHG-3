"""Integration tests for all FastAPI REST endpoints."""

import os
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


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


def test_api_search_and_hash():
    # 1. Search with dummy embedding
    emb = [0.05] * 512
    search_resp = client.post("/api/search", json={"embedding": emb})
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


def test_api_end_to_end_pipeline():
    sample_path = "samples/demo_face.jpg"
    with open(sample_path, "rb") as f:
        response = client.post("/api/pipeline", files={"image": ("demo.jpg", f, "image/jpeg")})

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
