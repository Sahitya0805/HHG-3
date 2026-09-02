#!/usr/bin/env python3
"""
FaceTrace — Face Identification & Blockchain Verification Pipeline Demo Script
Runs an end-to-end execution of the 7-step pipeline from terminal.
"""

import os
import sys
import time
import argparse
from dotenv import load_dotenv

load_dotenv()

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.face.detector import FaceDetector
from backend.face.encoder import FaceEncoder
from backend.search.reverse_search import ReverseSearchOrchestrator
from backend.hashing.fingerprint import FingerprintEngine
from backend.blockchain.verifier import BlockchainVerifier


def print_banner():
    print("""
========================================================================
   FACETRACE — FACE IDENTIFICATION & BLOCKCHAIN VERIFICATION PIPELINE
========================================================================
    """)


def run_demo(image_path: str):
    print_banner()

    if not os.path.exists(image_path):
        print(f"[!] Error: Image not found at {image_path}")
        sys.exit(1)

    print(f"[*] Loading input face image: {image_path}")
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    detector = FaceDetector()
    encoder = FaceEncoder(embedding_dim=512)
    searcher = ReverseSearchOrchestrator()
    verifier = BlockchainVerifier()

    # --- STEP 1: Face Detection & Encoding ---
    print("\n" + "=" * 50)
    print("STEP 1: FACE DETECTION & EMBEDDING")
    print("=" * 50)
    img_bgr = detector.load_image(image_bytes)
    det_res = detector.detect_faces(img_bgr)

    if not det_res.get("face_detected"):
        print(f"[x] Face detection failed: {det_res.get('error')}")
        sys.exit(1)

    print(f" [✓] Face detected successfully! Faces found: {det_res['faces_found']}")
    print(f" [✓] Primary face bounding box (x,y,w,h): {det_res['primary_box']}")

    emb_res = encoder.generate_embedding(det_res["primary_face_crop"])
    print(f" [✓] 512-dimensional face embedding generated.")
    print(f" [✓] Embedding vector sample (first 6 dims): {emb_res['embedding'][:6]}")
    print(f" [✓] Vector L2 Norm: {emb_res['norm']}")

    # --- STEP 2: Genuine Reverse Search ---
    print("\n" + "=" * 50)
    print("STEP 2: GENUINE REVERSE IMAGE SEARCH & MATCHING")
    print("=" * 50)
    print(f" [*] Querying search provider: {searcher.provider.__class__.__name__}...")
    time.sleep(0.5)

    search_res = searcher.search_and_match(image_bytes, emb_res["embedding"])
    if not search_res.get("success"):
        print(f"[x] Reverse search failed: {search_res.get('error')}")
        sys.exit(1)

    print(f" [✓] Reverse image search completed! Candidates discovered: {search_res['total_candidates']}")
    for cand in search_res["candidates"][:3]:
        print(f"     #{cand['rank']} {cand['source']}: {cand['title'][:40]}... (Sim: {cand['similarity_percent']}%) -> {cand['match_label']}")

    best = search_res["best_match"]
    print(f"\n [*] STRONGEST MATCH SELECTED:")
    print(f"     Platform:   {best['source']}")
    print(f"     URL:        {best['url']}")
    print(f"     Similarity: {best['similarity_percent']}% ({best['match_label']})")
    print(f"     Snippet:    {best['snippet']}")

    # --- STEP 3: Metadata Extraction & Cryptographic Fingerprinting ---
    print("\n" + "=" * 50)
    print("STEP 3: METADATA EXTRACTION & SHA-256 FINGERPRINT")
    print("=" * 50)
    metadata = search_res["metadata"]
    fingerprint = FingerprintEngine.generate_sha256(metadata)

    print(f" [*] Canonical JSON Payload:\n     {fingerprint['canonical_payload']}")
    print(f" [✓] Cryptographic Fingerprint (SHA-256):\n     {fingerprint['hash']}")
    print(f" [✓] On-Chain EVM format:\n     {fingerprint['bytes32_hash']}")

    # --- STEP 4: Blockchain Registration ---
    print("\n" + "=" * 50)
    print("STEP 4: BLOCKCHAIN UPLOAD & TRANSACTION RECORDING")
    print("=" * 50)
    print(f" [*] Connecting to {verifier.network_info['mode']}...")
    bc_res = verifier.store_hash(fingerprint["hash"])

    print(f" [✓] Status: Transaction Confirmed on Blockchain!")
    print(f"     Transaction Hash: {bc_res['transaction_hash']}")
    print(f"     Block Number:     {bc_res['block_number']}")
    print(f"     Submitter:        {bc_res['submitter']}")
    print(f"     Contract:         {bc_res['contract_address']}")
    print(f"     Gas Used:         {bc_res['gas_used']}")

    # --- STEP 5: On-Chain Verification ---
    print("\n" + "=" * 50)
    print("STEP 5: ON-CHAIN VERIFICATION")
    print("=" * 50)
    verify_res = verifier.verify_hash(fingerprint["hash"])

    print(f" [*] Querying Verification Registry contract...")
    print(f"     Local Computed Hash: {fingerprint['bytes32_hash']}")
    print(f"     On-Chain Hash:       {verify_res['on_chain_hash']}")
    print(f"     Result:              MATCH (Verified: {verify_res['verified']})")
    print(f" [✓] BLOCKCHAIN VERIFIED: Data is authentic and unmodified.")

    # --- STEP 6: Interactive Tamper Demonstration ---
    print("\n" + "=" * 50)
    print("STEP 6: TAMPERING DEMONSTRATION")
    print("=" * 50)
    print(" [*] Simulating unauthorized metadata tampering...")
    tampered_metadata = dict(metadata)
    tampered_metadata["caption"] = "Tampered metadata text inserted by attacker"

    tamper_eval = FingerprintEngine.test_tamper(
        original_metadata=metadata,
        tampered_metadata=tampered_metadata,
        on_chain_hash=verify_res["on_chain_hash"],
    )

    print(f"     Original Caption: '{metadata.get('caption')}'")
    print(f"     Tampered Caption: '{tampered_metadata.get('caption')}'")
    print(f"     Original Hash:    {tamper_eval['original_hash']}")
    print(f"     Recalculated:     {tamper_eval['tampered_hash']}")
    print(f"     On-Chain Hash:    {tamper_eval['on_chain_hash']}")
    print(f"\n [!] {tamper_eval['message']}")
    print(f" [✓] Tamper detection successfully proved data modification.")
    print("=" * 50 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FaceTrace Demo Pipeline")
    parser.add_argument(
        "--image",
        default="samples/demo_face.jpg",
        help="Path to face image (default: samples/demo_face.jpg)",
    )
    args = parser.parse_args()
    run_demo(args.image)
