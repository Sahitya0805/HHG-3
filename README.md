# FaceTrace — Face Identification & Blockchain Verification Pipeline

A privacy-conscious pipeline that detects a face from an input image, performs a genuine reverse-image/web search to locate matching public content, and records a cryptographic fingerprint of the discovered content on an EVM blockchain for tamper-evident verification.

---

## 1. What It Does

Finding where an image appears online usually requires manually performing reverse-image searches and then checking whether the discovered content has been modified.

**FaceTrace** automates this end-to-end:
1. **Face Detection & Encoding**: Detects human faces in an uploaded image, isolates the primary face crop, and extracts a normalized 512-dimensional facial embedding vector.
2. **Genuine Reverse Image / Web Search**: Queries external visual search endpoints (Google Lens / SerpApi / Visual Search / Wikimedia Open Media) to discover public web appearances.
3. **Candidate Face Matching & Verification**: Downloads discovered candidate images, extracts facial features, and computes cosine similarity scores to select the strongest authentic public match.
4. **Canonical Cryptographic Fingerprinting**: Serializes discovered metadata (URL, domain/source, title, snippet caption, timestamp) into deterministic canonical JSON and computes a SHA-256 fingerprint.
5. **Blockchain Registration**: Submits the 32-byte cryptographic hash to an EVM smart contract (`VerificationRegistry.sol`) with block timestamp and submitter address.
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
 │ (OpenCV /    │            │ (Google Lens │            │ Blockchain   │
 │  512-dim)    │            │  / SerpApi)  │            │ Verifier     │
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
                      │ Testnet / Simulated EVM    │
                      └────────────────────────────┘
```

---

## 3. Features

- **Consented Demonstration Mode**: Privacy-conscious by design; raw biometric embeddings and full private content are never posted on-chain.
- **Multi-tiered Face Detector**: Multi-scale face detection with bounding box annotations, primary face isolation, and normalized 512-dimensional embedding generation.
- **Genuine Reverse Image Search**: Modular `ReverseImageSearcher` interface supporting Google Lens (SerpApi), Bing Visual Search, and live open web visual search.
- **Cosine Similarity Scoring**: Computes $\cos(\theta) = \frac{u \cdot v}{\|u\| \|v\|}$ against candidate images with classification thresholds:
  - $\ge 90\%$: **Strong Match**
  - $80\% - 89\%$: **Possible Match**
  - $< 80\%$: **Reject**
- **Canonical Hashing**: Deterministic JSON serialization and SHA-256 hashing to guarantee reproducible fingerprints across platforms.
- **EVM Smart Contract Integration**: Web3.py client connected to `VerificationRegistry.sol` supporting live EVM testnets (Sepolia, Holesky, Polygon Amoy) and automatic zero-config local simulated EVM execution.
- **Interactive Tampering Demonstration Lab**: Live metadata editing with real-time SHA-256 recalculation, visual hash diffing, and tamper status badge.

---

## 4. Tech Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Computer Vision & Math**: OpenCV (`opencv-python-headless`), NumPy, Pillow
- **Web & Visual Search**: Requests, BeautifulSoup4, SerpApi / Google Lens / Bing Visual / Wikimedia APIs
- **Blockchain**: Web3.py, `eth-account`, Solidity (`VerificationRegistry.sol`)
- **Frontend**: React 18, Vite, Tailwind CSS, Lucide Icons
- **Testing**: Pytest, HTTPX

---

## 5. How Face Detection & Matching Works

1. **Detection**: The input image is converted to grayscale, histogram-equalized, and processed to identify facial regions.
2. **Isolation & Alignment**: Bounding boxes are determined with margin padding, extracting the primary face crop.
3. **Embedding Generation**: The face crop is resized to a standardized dimension. Spatial block variance, Discrete Cosine Transform (DCT) structural frequency coefficients, and facial zone histograms are concatenated and $L_2$-normalized to form a 512-dimensional vector.
4. **Candidate Verification**: For each candidate URL discovered during web search, candidate images are evaluated and the cosine similarity between the original face vector and candidate vector is computed.

---

## 6. How Reverse Image Search Works

FaceTrace abstracts search providers behind the `ReverseImageSearcher` base class:
- **`GoogleLensSearcher`**: Uses SerpApi Google Lens engine to search web indexes and extract visual match links.
- **`LiveWebSearcher`**: Performs live public image queries and open web visual searches against public domains.
- **`ResultParser`**: Evaluates candidates, downloads images where permitted, executes face detection, computes similarity metrics, and extracts minimal canonical metadata.

---

## 7. How Blockchain Verification Works

1. Minimal discovered metadata is canonicalized:
   ```json
   {"caption":"...","discovered_at":"2026-08-31T...","image_url":"https://...","source":"Instagram","title":"...","url":"https://..."}
   ```
2. The canonical payload is UTF-8 encoded and hashed with SHA-256, generating a 32-byte hash (`0x...`).
3. The hash is recorded in the `VerificationRegistry` contract via `storeRecord(bytes32 _hash)`.
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

### Quick Setup

```bash
# 1. Clone repository
git clone https://github.com/your-username/facetrace.git
cd facetrace

# 2. Run automated setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

---

## 10. Environment Variables

Create `.env` (optional — works out of the box with local simulation):

```bash
cp .env.example .env
```

```env
# Optional Search API Keys
SERPAPI_API_KEY=your_serpapi_key

# Optional Live EVM Testnet (Sepolia, Holesky, Polygon Amoy, Base Sepolia)
RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY
PRIVATE_KEY=your_wallet_private_key
CONTRACT_ADDRESS=0x71C67Ed3855aa521e0704673057e6250BE602876
```

---

## 11. Running the Project

### Start FastAPI Backend
```bash
.venv/bin/uvicorn backend.main:app --reload --port 8000
```
Backend API docs available at: `http://127.0.0.1:8000/docs`

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
 [✓] 512-dimensional face embedding generated (L2 Norm: 1.0)

==================================================
STEP 2: GENUINE REVERSE IMAGE SEARCH & MATCHING
==================================================
 [*] Querying search provider: LiveWebSearcher...
 [✓] Reverse search completed! Discovered candidates: 3
     #1 Instagram: Public Profile Media (Sim: 93.7%) -> Strong Match
     #2 LinkedIn: Speaker Spotlight (Sim: 88.4%) -> Possible Match

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
     Block Number:     4829100
     Submitter:        0x2f461654076bE5A4837434257026134Cc5F29BD6

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

- **Search Rate Limits**: External search APIs enforce query rate limits; multiple fallbacks are built in.
- **Future Improvements**:
  - Decentralized storage pinning via IPFS / Filecoin for original canonical metadata records.
  - Multi-chain verification (Arbitrum, Optimism, Polygon).
  - Merkle Tree batching for high-throughput multi-result verification.
