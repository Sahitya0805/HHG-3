"""FastAPI Backend server for FaceTrace Pipeline."""

import os
import base64
from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

load_dotenv()

from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.face.matcher import FaceMatcher
from backend.search.reverse_search import ReverseSearchOrchestrator
from backend.hashing.fingerprint import FingerprintEngine
from backend.blockchain.verifier import BlockchainVerifier
from backend.models.schemas import (
    FaceDetectionResponse,
    SearchRequest,
    SearchResponse,
    HashRequest,
    HashResponse,
    BlockchainStoreRequest,
    BlockchainStoreResponse,
    BlockchainVerifyResponse,
    TamperTestRequest,
    TamperTestResponse,
    PipelineRunResponse,
)

app = FastAPI(
    title="FaceTrace API",
    description="Face Identification & Blockchain Verification Pipeline",
    version="1.0.0",
)

# Enable CORS for React frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline singletons
detector = FaceDetector()
encoder = FaceEncoder(embedding_dim=512)
matcher = FaceMatcher()
search_orchestrator = ReverseSearchOrchestrator()
blockchain_verifier = BlockchainVerifier()


@app.get("/api/health")
def health_check():
    """Returns system status and active submodules."""
    return {
        "status": "healthy",
        "service": "FaceTrace Pipeline",
        "version": "1.0.0",
        "blockchain": blockchain_verifier.network_info,
        "search_provider": search_orchestrator.provider.__class__.__name__,
    }


@app.post("/api/face", response_model=FaceDetectionResponse)
async def process_face(image: UploadFile = File(...)):
    """
    Feature 1 & 2: Accept face image, detect face bounding box, and extract 512-dim embedding.
    """
    contents = await image.read()
    if not contents:
        return FaceDetectionResponse(
            success=False,
            face_detected=False,
            faces_found=0,
            error="Empty image file received.",
        )

    try:
        img_bgr = detector.load_image(contents)
    except Exception as e:
        return FaceDetectionResponse(
            success=False,
            face_detected=False,
            faces_found=0,
            error=f"Could not decode image: {str(e)}",
        )

    det_result = detector.detect_faces(img_bgr)
    if not det_result.get("face_detected"):
        return FaceDetectionResponse(
            success=False,
            face_detected=False,
            faces_found=0,
            error=det_result.get("error", "No human face detected in this image. Please upload a clear photo containing a human face."),
            annotated_image_b64=det_result.get("annotated_image_b64"),
        )

    # Generate 512-dim embedding from primary aligned face crop
    face_crop = det_result["primary_face_crop"]
    emb_result = encoder.generate_embedding(face_crop)

    return FaceDetectionResponse(
        success=True,
        face_detected=True,
        faces_found=det_result["faces_found"],
        boxes=det_result["boxes"],
        primary_box=det_result["primary_box"],
        confidence=det_result.get("confidence"),
        confidence_percent=det_result.get("confidence_percent"),
        detection_method=det_result.get("detection_method"),
        embedding_generated=True,
        embedding_dimensions=emb_result["embedding_dimensions"],
        embedding=emb_result["embedding"],
        sample_vector=emb_result["sample_vector"],
        primary_crop_b64=det_result["primary_crop_b64"],
        annotated_image_b64=det_result["annotated_image_b64"],
        warning=det_result.get("warning"),
    )


@app.post("/api/search", response_model=SearchResponse)
async def search_reverse_image(req: SearchRequest):
    """
    Feature 3: Perform genuine reverse-image/web search and rank candidate results.
    """
    if not req.embedding:
        raise HTTPException(status_code=400, detail="Face embedding vector is required for search and matching.")

    image_bytes = b""
    if req.image_b64:
        try:
            if "," in req.image_b64:
                b64_clean = req.image_b64.split(",")[1]
            else:
                b64_clean = req.image_b64
            image_bytes = base64.b64decode(b64_clean)
        except Exception:
            image_bytes = b"facetrace-query-bytes"
    else:
        image_bytes = b"facetrace-query-bytes"

    res = search_orchestrator.search_and_match(
        image_bytes=image_bytes,
        input_embedding=req.embedding,
        input_crop_b64=req.image_b64,
        search_query=req.search_query,
    )

    if not res.get("success"):
        return SearchResponse(
            success=False,
            provider_name=res.get("provider_name", "SearchOrchestrator"),
            total_candidates=0,
            candidates=[],
            error=res.get("error", "Search failed."),
        )

    return SearchResponse(
        success=True,
        provider_name=res["provider_name"],
        total_candidates=res["total_candidates"],
        candidates=res["candidates"],
        best_match=res["best_match"],
        metadata=res["metadata"],
    )


@app.post("/api/hash", response_model=HashResponse)
def generate_hash(req: HashRequest):
    """
    Feature 5: Generate canonical SHA-256 cryptographic fingerprint from discovered metadata.
    """
    if not req.metadata:
        raise HTTPException(status_code=400, detail="Metadata dictionary required.")

    res = FingerprintEngine.generate_sha256(req.metadata)
    return HashResponse(
        algorithm="SHA-256",
        canonical_payload=res["canonical_payload"],
        hash=res["hash"],
        bytes32_hash=res["bytes32_hash"],
        byte_length=32,
    )


@app.post("/api/blockchain/store", response_model=BlockchainStoreResponse)
def store_on_blockchain(req: BlockchainStoreRequest):
    """
    Feature 6: Upload SHA-256 fingerprint hash to the EVM smart contract.
    """
    if not req.hash:
        raise HTTPException(status_code=400, detail="Hash string required.")

    try:
        res = blockchain_verifier.store_hash(req.hash)
        return BlockchainStoreResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Blockchain storage failed: {str(e)}")


@app.get("/api/blockchain/verify", response_model=BlockchainVerifyResponse)
def verify_on_blockchain(hash: str = Query(..., description="SHA-256 hash in hex format")):
    """
    Feature 7: Query the smart contract and verify on-chain existence.
    """
    if not hash:
        raise HTTPException(status_code=400, detail="Query parameter 'hash' is required.")

    try:
        res = blockchain_verifier.verify_hash(hash)
        return BlockchainVerifyResponse(**res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@app.post("/api/tamper-test", response_model=TamperTestResponse)
def test_tampering(req: TamperTestRequest):
    """
    Feature 8 / Demo: Interactive Tampering Demonstration.
    """
    res = FingerprintEngine.test_tamper(
        original_metadata=req.original_metadata,
        tampered_metadata=req.tampered_metadata,
        on_chain_hash=req.on_chain_hash,
    )
    return TamperTestResponse(**res)


@app.post("/api/pipeline", response_model=PipelineRunResponse)
async def run_full_pipeline(image: UploadFile = File(...)):
    """
    End-to-end Automated Pipeline execution.
    """
    contents = await image.read()
    try:
        img_bgr = detector.load_image(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to decode image: {str(e)}")

    # 1. Face Detection
    det_res = detector.detect_faces(img_bgr)
    if not det_res.get("face_detected"):
        raise HTTPException(status_code=400, detail="❌ No face detected. Please upload an image containing a clear human face.")

    # 2. Embedding Generation
    emb_res = encoder.generate_embedding(det_res["primary_face_crop"])

    # 3. Reverse Web Search & Candidate Match
    search_res = search_orchestrator.search_and_match(
        image_bytes=contents,
        input_embedding=emb_res["embedding"],
        input_crop_b64=det_res["primary_crop_b64"],
    )
    if not search_res.get("success"):
        raise HTTPException(status_code=500, detail="Search failed to find candidates.")

    # 4. Canonical Metadata & Cryptographic Fingerprint
    metadata = search_res["metadata"]
    fingerprint = FingerprintEngine.generate_sha256(metadata)

    # 5. Blockchain Store
    bc_store = blockchain_verifier.store_hash(fingerprint["hash"])

    # 6. On-chain Verification
    bc_verify = blockchain_verifier.verify_hash(fingerprint["hash"])

    return PipelineRunResponse(
        success=True,
        face={
            "faces_found": det_res["faces_found"],
            "primary_box": det_res["primary_box"],
            "confidence_percent": det_res.get("confidence_percent"),
            "detection_method": det_res.get("detection_method"),
            "embedding_dimensions": emb_res["embedding_dimensions"],
            "primary_crop_b64": det_res["primary_crop_b64"],
            "annotated_image_b64": det_res["annotated_image_b64"],
            "sample_vector": emb_res["sample_vector"],
        },
        search={
            "provider": search_res["provider_name"],
            "candidates": search_res["candidates"],
            "best_match": search_res["best_match"],
        },
        metadata=metadata,
        fingerprint=fingerprint,
        blockchain=bc_store,
        verification=bc_verify,
    )


# --- Serve Built React Frontend SPA ---
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
frontend_assets = os.path.join(frontend_dist, "assets")

if os.path.exists(frontend_assets):
    app.mount("/assets", StaticFiles(directory=frontend_assets), name="assets")


@app.get("/")
async def serve_root():
    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"status": "ok", "service": "FaceTrace API", "docs": "/docs"}


@app.get("/{full_path:path}")
async def serve_spa_catchall(full_path: str):
    if full_path.startswith("api/") or full_path.startswith("docs") or full_path == "openapi.json":
        raise HTTPException(status_code=404, detail="Not Found")

    index_file = os.path.join(frontend_dist, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"detail": "Not Found"}
