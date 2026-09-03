# FaceTrace — Face Identification & Blockchain Verification Pipeline

A privacy-conscious pipeline that detects a face from an input image, performs a genuine reverse-image/web search to locate matching public content, and records a cryptographic fingerprint of the discovered content on an EVM blockchain for tamper-evident verification.

---

## 1. What It Does

Finding where an image appears online usually requires manually performing reverse-image searches and then checking whether the discovered content has been modified.

**FaceTrace** automates this end-to-end:
1. **Face Detection & Encoding**: Detects human faces in an uploaded image, isolates the primary face crop, and extracts a normalized 512-dimensional facial embedding vector.
2. **Genuine Reverse Image / Web Search**: Uploads the input image to SerpApi's Image API, queries Google Lens visual matches, and receives public web/social result candidates.
3. **Candidate Face Matching & Verification**: Downloads discovered candidate images, detects faces, extracts embeddings, and computes cosine similarity scores to select the strongest authentic public match.
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
- **ArcFace-Preferred Encoding**: Uses InsightFace/ArcFace when installed, with a deterministic OpenCV structural encoder fallback for lightweight local execution.
- **Genuine Reverse Image Search**: SerpApi Google Lens upload/search flow using `SERPAPI_API_KEY`; no hardcoded/pre-picked result is accepted.
- **Cosine Similarity Scoring**: Computes $\cos(\theta) = \frac{u \cdot v}{\|u\| \|v\|}$ against candidate images with classification thresholds:
  - $\ge 90\%$: **Strong Match**
  - $80\% - 89\%$: **Possible Match**
  - $< 80\%$: **Reject**
- **Canonical Hashing**: Deterministic JSON serialization and SHA-256 hashing to guarantee reproducible fingerprints across platforms.
- **EVM Smart Contract Integration**: Web3.py client connected to `VerificationRegistry.sol` on a local Anvil chain.
- **Interactive Tampering Demonstration Lab**: Live metadata editing with real-time SHA-256 recalculation, visual hash diffing, and tamper status badge.

---

## 4. Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Computer Vision & Math**: OpenCV (`opencv-python-headless`), NumPy, Pillow, optional InsightFace/ONNX Runtime
- **Web & Visual Search**: Requests, BeautifulSoup4, SerpApi Google Lens
- **Blockchain**: Web3.py, Anvil, Solidity (`VerificationRegistry.sol`)
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons
- **Testing**: Pytest, HTTPX

---

## 5. How Face Detection & Matching Works

1. **Detection**: The input image is converted to grayscale, histogram-equalized, and processed to identify facial regions.
2. **Isolation & Alignment**: Bounding boxes are determined with margin padding, extracting the primary face crop.
3. **Embedding Generation**: If optional ArcFace dependencies are installed, InsightFace generates a normalized 512-dimensional recognition embedding. Otherwise, the face crop is resized and encoded with deterministic OpenCV structural features.
4. **Candidate Verification**: For each candidate URL discovered during web search, candidate images are evaluated and the cosine similarity between the original face vector and candidate vector is computed.

---

## 6. How Reverse Image Search Works

FaceTrace abstracts search providers behind the `ReverseImageSearcher` base class:
- **`GoogleLensSearcher`**: Uses SerpApi Image API upload plus Google Lens visual matches. `SERPAPI_API_KEY` is required for the live pipeline.
- **`ResultParser`**: Downloads each candidate image where permitted, executes face detection, computes real embedding similarity, and extracts minimal canonical metadata.
- Candidates without a downloadable image or detectable face are rejected before blockchain registration.

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
- A SerpApi API key for Google Lens

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

### Optional ArcFace Encoder
```bash
.venv/bin/pip install -r requirements-arcface.txt
```

### Start Frontend UI
```bash
cd frontend
npm run dev
```
Open your browser at: `http://localhost:3000`

### Run CLI Demo Script
```bash
.venv/bin/python scripts/demo.py --image samples/demo_face.jpg
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
STEP 2: GENUINE REVERSE IMAGE SEARCH & MATCHING
==================================================
 [*] Querying search provider: GoogleLensSearcher...
 [✓] Reverse image search completed! Candidates discovered: 2
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
- **Consented Public Demonstration**: Intended exclusively for consented demonstration imagery and public figure content with appropriate rights.
- **Similarity vs Identity**: High similarity scores indicate visual alignment, not absolute real-world legal identity.

---

## 14. Limitations & Future Improvements

- **Search Rate Limits**: SerpApi enforces query and upload limits; the live pipeline requires a valid `SERPAPI_API_KEY`.
- **Candidate Availability**: Many social platforms block image downloads or omit public OpenGraph images, so some Lens results may be rejected before scoring.
- **Local Chain Scope**: The primary proof target is local Anvil for reproducible judging. It demonstrates real EVM transactions, but it is not a public permanent chain.
- **Future Improvements**:
  - Decentralized storage pinning via IPFS / Filecoin for original canonical metadata records.
  - Multi-chain verification (Arbitrum, Optimism, Polygon).
  - Merkle Tree batching for high-throughput multi-result verification.
