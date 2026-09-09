# FaceTrace — Face Identification & Blockchain Verification Pipeline

A privacy-conscious pipeline that detects a face from an input image, performs a genuine reverse-image/web search to locate matching public content, and records a cryptographic fingerprint of the discovered content on an EVM blockchain for tamper-evident verification.

---

## 1. What It Does

Finding where an image appears online usually requires manually performing reverse-image searches and then checking whether the discovered content has been modified.

**FaceTrace** automates this end-to-end:
1. **Face Detection & Encoding**: Detects human faces in an uploaded image, isolates the primary face crop, and extracts a normalized 512-dimensional facial embedding vector.
2. **Face-First Public Discovery**: Uploads both the full input image and isolated face crop to SerpApi Google Lens, then optionally searches indexed public profile/post/video pages when a name, handle, or context hint is supplied.
3. **Candidate Face Matching & Verification**: Extracts candidate images from result thumbnails, OpenGraph/Twitter cards, JSON-LD metadata, visible page images, profile avatars, and video thumbnails/frames where public assets are downloadable. Final matches require local face comparison evidence.
4. **Canonical Cryptographic Fingerprinting**: Serializes discovered metadata (URL, domain/source, title, snippet caption, timestamp) into deterministic canonical JSON and computes a SHA-256 fingerprint.
5. **Blockchain Registration**: Submits the 32-byte cryptographic hash to a locally deployed Anvil EVM smart contract (`VerificationRegistry.sol`) with block timestamp and submitter address.
6. **On-Chain Verification & Tamper Detection**: Queries the blockchain to prove data integrity and features an interactive **Tampering Lab** demonstrating that even a single altered character triggers an immediate `❌ HASH MISMATCH — DATA TAMPERED` alert.

---

## 2. Architecture

```
                      ┌────────────────────────────┐
                      │   React + Tailwind UI      │
                      └─────────────┬──────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │      FastAPI Backend       │
                      └─────────────┬──────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
 ┌──────────────┐            ┌──────────────┐            ┌──────────────┐
 │ Face Engine  │            │ Search Engine│            │ Web3 EVM     │
 │ (ArcFace /   │            │ (SerpApi     │            │ Blockchain   │
 │  OpenCV)     │            │  Lens)       │            │ Verifier     │
 └──────┬───────┘            └──────┬───────┘            └──────┬───────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │ Cryptographic Fingerprint  │
                      │ (Canonical JSON + SHA-256) │
                      └─────────────┬──────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │ Smart Contract (Registry)  │
                      │ Local Anvil EVM            │
                      └────────────────────────────┘
```

---

## 3. Features

- **Consented Demonstration Mode**: Privacy-conscious by design; raw biometric embeddings and full private content are never posted on-chain.
- **Multi-tiered Face Detector**: Multi-scale face detection with bounding box annotations, primary face isolation, and normalized 512-dimensional embedding generation.
- **ArcFace-First Encoding**: Uses InsightFace/ArcFace (`buffalo_l` by default) for final matching. The OpenCV structural encoder remains available for face detection/debug and local tests, but strict final matches reject fallback embeddings.
- **Public Web/Profile/Video Discovery**: Runs SerpApi Google Lens on the full image, SerpApi Google Lens on the cropped face, and SerpApi Google Search across GitHub, LinkedIn, Instagram, X/Twitter, Facebook, YouTube, TikTok, and personal sites when a search hint is provided.
- **Reason-Coded Candidate Rejections**: Keeps rejected evidence with reasons such as blocked download, missing public image, no detectable face, low similarity, and ArcFace unavailable.
- **Cosine Similarity Scoring**: Computes $\cos(\theta) = \frac{u \cdot v}{\|u\| \|v\|}$ against candidate images with classification thresholds:
  - ArcFace: `>= 0.45` strong match, `0.32 - 0.44` possible match
  - OpenCV fallback debug mode: `>= 0.90` strong match, `0.80 - 0.89` possible match
- **Canonical Hashing**: Deterministic JSON serialization and SHA-256 hashing to guarantee reproducible fingerprints across platforms.
- **EVM Smart Contract Integration**: Web3.py client connected to `VerificationRegistry.sol` on a local Anvil chain.
- **Interactive Tampering Demonstration Lab**: Live metadata editing with real-time SHA-256 recalculation, visual hash diffing, and tamper status badge.

---

## 4. Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Computer Vision & Math**: OpenCV (`opencv-python-headless`), NumPy, Pillow, optional InsightFace/ONNX Runtime
- **Web & Visual Search**: Requests, BeautifulSoup4, SerpApi Google Lens, SerpApi Google Search
- **Blockchain**: Web3.py, Anvil, Solidity (`VerificationRegistry.sol`)
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons
- **Testing**: Pytest, HTTPX

---

## 5. How Face Detection & Matching Works

1. **Detection**: The input image is converted to grayscale, histogram-equalized, and processed to identify facial regions.
2. **Isolation & Alignment**: Bounding boxes are determined with margin padding, extracting the primary face crop.
3. **Embedding Generation**: InsightFace/ArcFace generates a normalized 512-dimensional recognition embedding when it can detect the face. If it cannot, the endpoint reports the OpenCV fallback model and strict final matching will not accept it.
4. **Candidate Verification**: For each public candidate URL, downloadable images/thumbnails/frames are evaluated and ranked by local embedding similarity, not search result position.

---

## 6. How Face-First Public Search Works

FaceTrace abstracts search providers behind the `ReverseImageSearcher` base class:
- **`GoogleLensSearcher:full-image`**: Uses SerpApi Image API upload plus Google Lens visual matches for the original upload.
- **`GoogleLensSearcher:face-crop`**: Repeats Lens discovery with the isolated face crop to reduce dependence on exact full-image matches.
- **`PublicWebSearcher`**: Uses SerpApi Google Search with the optional hint to find indexed public profile/post/video pages across likely surfaces.
- **`ResultParser`**: Extracts candidate media from thumbnails, `og:image`, `twitter:image`, JSON-LD images, visible `<img>` tags, avatar images, and public video posters/frames; then detects faces, embeds them, and computes local similarity.
- Candidates without a downloadable public image, detectable face, or acceptable similarity are rejected before blockchain registration.

---

## 7. How Blockchain Verification Works

1. Minimal discovered metadata is canonicalized:
   ```json
   {"caption":"...","discovered_at":"2026-08-31T...","image_url":"https://...","source":"Instagram","title":"...","url":"https://..."}
   ```
2. The canonical payload is UTF-8 encoded and hashed with SHA-256, generating a 32-byte hash (`0x...`).
3. The hash is recorded in the locally deployed Anvil `VerificationRegistry` contract via `storeRecord(bytes32 _hash)`.
4. Verification queries `verifyRecord(bytes32 _hash)`:
   - If `records[hash].dataHash == hash`, the blockchain confirms the content is authentic and untouched.
   - If any character of the metadata is changed, the recalculated SHA-256 will mismatch the on-chain hash, immediately revealing tampering.

---

## 8. Smart Contract

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract VerificationRegistry {
    struct Record {
        bytes32 dataHash;
        uint256 timestamp;
        address submitter;
    }

    mapping(bytes32 => Record) public records;
    event RecordStored(bytes32 indexed dataHash, address indexed submitter, uint256 timestamp);

    function storeRecord(bytes32 _hash) public returns (bool) {
        require(_hash != bytes32(0), "Invalid zero hash");
        records[_hash] = Record(_hash, block.timestamp, msg.sender);
        emit RecordStored(_hash, msg.sender, block.timestamp);
        return true;
    }

    function verifyRecord(bytes32 _hash) public view returns (bool) {
        return records[_hash].dataHash == _hash && records[_hash].timestamp > 0;
    }

    function getRecord(bytes32 _hash) public view returns (bytes32 dataHash, uint256 timestamp, address submitter) {
        Record memory r = records[_hash];
        return (r.dataHash, r.timestamp, r.submitter);
    }
}
```

---

## 9. Setup & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Foundry/Anvil for the local EVM (`curl -L https://foundry.paradigm.xyz | bash`, then `foundryup`)
- A SerpApi API key for Google Lens and Google Search

### Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/your-username/facetrace.git
cd facetrace

# 2. Run automated setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# 3. Configure live services
cp .env.example .env
# Edit .env and set SERPAPI_API_KEY
```

---

## 10. Environment Variables

Create `.env`:

```bash
cp .env.example .env
```

```env
# Required live search API key
SERPAPI_API_KEY=your_serpapi_key

# Local Anvil EVM
LOCAL_RPC_URL=http://127.0.0.1:8545
PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80
CONTRACT_ADDRESS=<filled by scripts/deploy_contract.py>
```

---

## 11. Running the Project

### Start FastAPI Backend
```bash
.venv/bin/uvicorn backend.main:app --reload --port 8000
```
Backend API docs available at: `http://127.0.0.1:8000/docs`

### Start Local Blockchain
```bash
anvil --host 127.0.0.1 --port 8545
.venv/bin/python scripts/deploy_contract.py
```
Copy the printed `CONTRACT_ADDRESS` into `.env`.

### ArcFace Encoder
```bash
.venv/bin/pip install -r requirements-arcface.txt
```
The first run downloads InsightFace model weights into `~/.insightface`. Keep `strict_face_match=true` for real demos. Use `--no-strict-arcface` only when debugging without model support.

### Start Frontend UI
```bash
cd frontend
npm run dev
```
Open your browser at: `http://localhost:3000`

### Run CLI Demo Script
```bash
.venv/bin/python scripts/demo.py --image samples/demo_face.jpg --query "known public name or handle"
```

### Run Test Suite
```bash
.venv/bin/pytest tests/
```

---

## 12. Example Output

```
========================================================================
   FACETRACE — FACE IDENTIFICATION & BLOCKCHAIN VERIFICATION PIPELINE
========================================================================

[*] Loading input face image: samples/demo_face.jpg

==================================================
STEP 1: FACE DETECTION & EMBEDDING
==================================================
 [✓] Face detected successfully! Faces found: 1
 [✓] Primary face bounding box: [70, 39, 160, 215]
 [✓] 512-dimensional face embedding generated.
 [✓] Embedding model: insightface-arcface-buffalo_l

==================================================
STEP 2: FACE-FIRST PUBLIC WEB/PROFILE/VIDEO SEARCH
==================================================
 [*] Searching Google Lens full image, Google Lens face crop, and hinted public profile/video pages...
 [✓] Discovery completed. Raw candidates discovered: 18
     Provider: GoogleLensSearcher:full-image -> 7 raw results
     Provider: GoogleLensSearcher:face-crop -> 4 raw results
     Provider: SerpApiPublicWebProfilesVideos -> 7 raw results
     #1 Instagram: Hackathon Demo Post... (Sim: 92.4%) -> Strong Match

==================================================
STEP 3: METADATA EXTRACTION & SHA-256 FINGERPRINT
==================================================
 [✓] Cryptographic Fingerprint (SHA-256):
     48df31ce5fa39e7024bb1c3261b83ef2b4ad03bf942448d467d12f4febe18da1

==================================================
STEP 4: BLOCKCHAIN UPLOAD & TRANSACTION RECORDING
==================================================
 [✓] Transaction Confirmed on Blockchain!
     Transaction Hash: 0x8b4bb55775c9acc06f7b8a46edb802b9d1175da98f9b287a451409dbd8a4de70
     Block Number:     7
     Submitter:        0x2f461654076bE5A4837434257026134Cc5F29BD6
     Contract:         0x...

==================================================
STEP 5: ON-CHAIN VERIFICATION
==================================================
     Local Computed Hash: 0x48df31ce5fa39e7024bb1c3261b83ef2b4ad03bf942448d467d12f4febe18da1
     On-Chain Hash:       0x48df31ce5fa39e7024bb1c3261b83ef2b4ad03bf942448d467d12f4febe18da1
     Result:              MATCH (Verified: True)
 [✓] BLOCKCHAIN VERIFIED: Data is authentic and unmodified.

==================================================
STEP 6: TAMPERING DEMONSTRATION
==================================================
     Original Caption: 'Excited to share insights at the 2026 Innovation Summit today!'
     Tampered Caption: 'Tampered metadata text inserted by attacker'
     Original Hash:    0x48df31ce5fa39e70...
     Recalculated:     0xcf007fa7f84f34e1...
 [!] ❌ HASH MISMATCH — DATA TAMPERED
```

---

## 13. Privacy & Security Considerations

- **Ephemeral Processing**: Input images are processed in-memory during execution and are not permanently stored in a facial surveillance database.
- **Zero Biometrics On-Chain**: Only 32-byte cryptographic hashes of public metadata are recorded on the smart contract. Facial vectors and personal identities never touch the blockchain.
- **Consented Public Demonstration**: Intended for consented imagery and content the operator is allowed to inspect. Do not use it to identify or track people without permission.
- **Similarity vs Identity**: High similarity scores indicate visual alignment, not absolute real-world legal identity.

---

## 14. Limitations & Future Improvements

- **Search Rate Limits**: SerpApi enforces query and upload limits; the live pipeline requires a valid `SERPAPI_API_KEY`.
- **Public Coverage Only**: FaceTrace cannot search private accounts, logged-in feeds, deleted content, or every new reel/post before it appears in public indexes.
- **Candidate Availability**: Many social platforms block image downloads or omit public OpenGraph images, so some results may be rejected before scoring.
- **No Custom Training**: "Train it" is implemented as pretrained ArcFace embeddings, not a custom biometric model trained on private faces.
- **Local Chain Scope**: The primary proof target is local Anvil for reproducible judging. It demonstrates real EVM transactions, but it is not a public permanent chain.
- **Future Improvements**:
  - Decentralized storage pinning via IPFS / Filecoin for original canonical metadata records.
  - Multi-chain verification (Arbitrum, Optimism, Polygon).
  - Merkle Tree batching for high-throughput multi-result verification.
