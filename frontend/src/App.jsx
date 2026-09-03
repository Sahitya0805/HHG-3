import React, { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertCircle,
  Check,
  Copy,
  ExternalLink,
  Loader2,
  RefreshCw,
  Search,
  ShieldCheck,
  Upload,
} from 'lucide-react';
import {
  checkHealth,
  generateFingerprint,
  searchReverseImage,
  storeOnBlockchain,
  uploadAndDetectFace,
  verifyOnBlockchain,
} from './api';

const STEPS = [
  { id: 'image', label: 'Image' },
  { id: 'face', label: 'Face' },
  { id: 'search', label: 'Search' },
  { id: 'hash', label: 'Hash' },
  { id: 'chain', label: 'Chain' },
  { id: 'verify', label: 'Verify' },
];

const LOADING_TEXT = {
  face: 'Detecting the face and building the embedding',
  search: 'Sending the image to Google Lens and checking candidate faces',
  hash: 'Canonicalizing the discovered post metadata',
  chain: 'Writing the metadata hash to the local EVM contract',
  verify: 'Reading the contract record and comparing hashes',
};

function shortHash(value = '') {
  if (!value) return 'Not available';
  return `${value.slice(0, 14)}...${value.slice(-10)}`;
}

function StatusPill({ ok, children }) {
  return (
    <span className={`status-pill ${ok ? 'status-ok' : 'status-warn'}`}>
      <span className="status-dot" />
      {children}
    </span>
  );
}

function DataRow({ label, value, mono = false }) {
  return (
    <div className="data-row">
      <span>{label}</span>
      <strong className={mono ? 'font-mono break-all' : ''}>{value || 'Not available'}</strong>
    </div>
  );
}

export default function App() {
  const fileInputRef = useRef(null);
  const [health, setHealth] = useState(null);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [activeStep, setActiveStep] = useState('image');
  const [completedSteps, setCompletedSteps] = useState([]);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [errorMessage, setErrorMessage] = useState('');
  const [faceData, setFaceData] = useState(null);
  const [searchData, setSearchData] = useState(null);
  const [fingerprintData, setFingerprintData] = useState(null);
  const [blockchainData, setBlockchainData] = useState(null);
  const [verificationData, setVerificationData] = useState(null);
  const [copied, setCopied] = useState(false);

  const isRunning = Boolean(loadingMessage);

  useEffect(() => {
    checkHealth().then(setHealth).catch(() => setHealth(null));
  }, []);

  const chainReady = Boolean(health?.blockchain?.connected);
  const backendReady = health?.status === 'healthy';
  const searchReady = Boolean(health?.search?.configured);

  const bestMatch = searchData?.best_match;
  const canRunFace = imageFile && !isRunning;
  const canRunPipeline = imageFile && !isRunning && searchReady && chainReady;

  const stepState = useMemo(() => {
    return STEPS.reduce((acc, step) => {
      acc[step.id] = completedSteps.includes(step.id)
        ? 'done'
        : activeStep === step.id
          ? 'active'
          : 'idle';
      return acc;
    }, {});
  }, [activeStep, completedSteps]);

  function resetResults() {
    setCompletedSteps([]);
    setActiveStep('image');
    setLoadingMessage('');
    setErrorMessage('');
    setFaceData(null);
    setSearchData(null);
    setFingerprintData(null);
    setBlockchainData(null);
    setVerificationData(null);
    setCopied(false);
  }

  function handleFileSelected(file) {
    if (!file) return;
    resetResults();
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setCompletedSteps(['image']);
  }

  async function runPipeline() {
    if (!imageFile || !searchReady || !chainReady) return;

    try {
      resetResults();
      setCompletedSteps(['image']);

      setActiveStep('face');
      setLoadingMessage(LOADING_TEXT.face);
      const face = await uploadAndDetectFace(imageFile);
      if (!face.face_detected) {
        throw new Error(face.error || 'No face was detected in this image.');
      }
      setFaceData(face);
      setCompletedSteps(['image', 'face']);

      setActiveStep('search');
      setLoadingMessage(LOADING_TEXT.search);
      const search = await searchReverseImage(face.embedding, face.primary_crop_b64, searchQuery.trim() || null);
      if (!search.success) {
        throw new Error(search.error || 'No matching public result passed candidate verification.');
      }
      setSearchData(search);
      setCompletedSteps(['image', 'face', 'search']);

      setActiveStep('hash');
      setLoadingMessage(LOADING_TEXT.hash);
      const fingerprint = await generateFingerprint(search.metadata);
      setFingerprintData(fingerprint);
      setCompletedSteps(['image', 'face', 'search', 'hash']);

      setActiveStep('chain');
      setLoadingMessage(LOADING_TEXT.chain);
      const blockchain = await storeOnBlockchain(fingerprint.hash);
      setBlockchainData(blockchain);
      setCompletedSteps(['image', 'face', 'search', 'hash', 'chain']);

      setActiveStep('verify');
      setLoadingMessage(LOADING_TEXT.verify);
      const verification = await verifyOnBlockchain(fingerprint.hash);
      setVerificationData(verification);
      setCompletedSteps(['image', 'face', 'search', 'hash', 'chain', 'verify']);
      setActiveStep('verify');
      setLoadingMessage('');
    } catch (err) {
      setErrorMessage(err.message || 'Pipeline failed.');
      setLoadingMessage('');
    }
  }

  async function runFaceOnly() {
    if (!imageFile) return;

    try {
      resetResults();
      setCompletedSteps(['image']);
      setActiveStep('face');
      setLoadingMessage(LOADING_TEXT.face);
      const face = await uploadAndDetectFace(imageFile);
      if (!face.face_detected) {
        throw new Error(face.error || 'No face was detected in this image.');
      }
      setFaceData(face);
      setCompletedSteps(['image', 'face']);
      setLoadingMessage('');
    } catch (err) {
      setErrorMessage(err.message || 'Face detection failed.');
      setLoadingMessage('');
    }
  }

  async function copyHash() {
    if (!fingerprintData?.bytes32_hash) return;
    await navigator.clipboard.writeText(fingerprintData.bytes32_hash);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <main className="min-h-screen bg-stone-50 text-stone-950">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col gap-4 px-4 py-5 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">FaceTrace</h1>
            <p className="mt-1 text-sm text-stone-600">Face scan to verified public post record.</p>
          </div>
          <div className="flex flex-wrap gap-2 text-xs">
            <StatusPill ok={backendReady}>Backend {backendReady ? 'online' : 'offline'}</StatusPill>
            <StatusPill ok={searchReady}>Search {searchReady ? 'ready' : 'key missing'}</StatusPill>
            <StatusPill ok={chainReady}>Local chain {chainReady ? 'ready' : 'not connected'}</StatusPill>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-6xl px-4 py-6">
        <div className="mb-5 grid grid-cols-3 gap-2 sm:grid-cols-6">
          {STEPS.map((step) => (
            <div key={step.id} className={`step ${stepState[step.id]}`}>
              <span>{step.label}</span>
              {stepState[step.id] === 'done' && <Check className="h-4 w-4" />}
              {stepState[step.id] === 'active' && <Loader2 className="h-4 w-4 animate-spin" />}
            </div>
          ))}
        </div>

        {loadingMessage && (
          <div className="mb-5 flex items-center gap-3 rounded-md border border-blue-200 bg-blue-50 px-4 py-3 text-sm text-blue-900">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>{loadingMessage}</span>
          </div>
        )}

        {(!searchReady || !chainReady) && (
          <div className="mb-5 rounded-md border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-950">
            <div className="flex items-start gap-3">
              <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
              <div>
                <p className="font-medium">Full pipeline setup is incomplete.</p>
                <p className="mt-1 text-amber-900">
                  {!searchReady ? 'Add SERPAPI_API_KEY to .env. ' : ''}
                  {!chainReady ? 'Start Anvil and deploy the contract. ' : ''}
                  Face detection can still be tested now.
                </p>
              </div>
            </div>
          </div>
        )}

        {errorMessage && (
          <div className="mb-5 flex items-start gap-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}

        <div className="grid gap-5 lg:grid-cols-[380px_1fr]">
          <section className="panel">
            <div className="panel-header">
              <h2>Input</h2>
              <button type="button" className="icon-button" onClick={resetResults} title="Reset results">
                <RefreshCw className="h-4 w-4" />
              </button>
            </div>

            <input
              ref={fileInputRef}
              type="file"
              accept=".jpg,.jpeg,.png,.webp"
              className="hidden"
              onChange={(event) => handleFileSelected(event.target.files?.[0])}
            />

            <button type="button" className="upload-box" onClick={() => fileInputRef.current?.click()}>
              {imagePreview ? (
                <img src={imagePreview} alt="Selected input" />
              ) : (
                <span className="flex flex-col items-center gap-2 text-stone-500">
                  <Upload className="h-8 w-8" />
                  Select a face image
                </span>
              )}
            </button>

            <label className="mt-4 block text-sm font-medium text-stone-700" htmlFor="search-query">
              Search hint
            </label>
            <div className="mt-2 flex items-center gap-2 rounded-md border border-stone-300 bg-white px-3 py-2">
              <Search className="h-4 w-4 text-stone-400" />
              <input
                id="search-query"
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Optional name, handle, or context"
                className="w-full bg-transparent text-sm outline-none placeholder:text-stone-400"
              />
            </div>

            <button type="button" className="secondary-button mt-4" onClick={runFaceOnly} disabled={!canRunFace}>
              Test face detection
            </button>

            <button type="button" className="primary-button mt-3" onClick={runPipeline} disabled={!canRunPipeline}>
              {isRunning ? 'Running pipeline' : 'Run full pipeline'}
            </button>

            {(!searchReady || !chainReady) && (
              <p className="mt-3 text-xs leading-5 text-stone-500">
                Full pipeline requires SerpApi search and the local EVM contract.
              </p>
            )}
          </section>

          <section className="space-y-5">
            <div className="panel">
              <div className="panel-header">
                <h2>Face</h2>
                {faceData?.face_detected && <Check className="h-4 w-4 text-emerald-600" />}
              </div>
              {faceData ? (
                <div className="grid gap-4 md:grid-cols-[220px_1fr]">
                  <img
                    src={faceData.annotated_image_b64 || imagePreview}
                    alt="Detected face"
                    className="h-48 w-full rounded-md border border-stone-200 object-contain"
                  />
                  <div>
                    <DataRow label="Faces found" value={faceData.faces_found} />
                    <DataRow label="Detector" value={faceData.detection_method} />
                    <DataRow label="Embedding" value={`${faceData.embedding_dimensions} dimensions`} />
                    <DataRow label="Model" value={faceData.embedding_model || 'OpenCV fallback'} />
                  </div>
                </div>
              ) : (
                <p className="empty-text">No face processed yet.</p>
              )}
            </div>

            <div className="panel">
              <div className="panel-header">
                <h2>Matched Post</h2>
                {bestMatch?.url && (
                  <a href={bestMatch.url} target="_blank" rel="noreferrer" className="link-button">
                    Open <ExternalLink className="h-3.5 w-3.5" />
                  </a>
                )}
              </div>
              {bestMatch ? (
                <div className="grid gap-4 md:grid-cols-[140px_1fr]">
                  <img
                    src={bestMatch.candidate_face_preview || bestMatch.image_url}
                    alt="Candidate face"
                    className="h-36 w-full rounded-md border border-stone-200 object-cover"
                  />
                  <div>
                    <DataRow label="Source" value={bestMatch.source} />
                    <DataRow label="Title" value={bestMatch.title} />
                    <DataRow label="Similarity" value={`${bestMatch.similarity_percent}% (${bestMatch.match_label})`} />
                    <DataRow label="Evidence" value={bestMatch.match_evidence} />
                  </div>
                </div>
              ) : (
                <p className="empty-text">No search result selected yet.</p>
              )}
            </div>

            <div className="grid gap-5 xl:grid-cols-2">
              <div className="panel">
                <div className="panel-header">
                  <h2>Fingerprint</h2>
                  {fingerprintData?.bytes32_hash && (
                    <button type="button" className="icon-button" onClick={copyHash} title="Copy hash">
                      {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                    </button>
                  )}
                </div>
                {fingerprintData ? (
                  <>
                    <DataRow label="Algorithm" value={fingerprintData.algorithm} />
                    <DataRow label="Hash" value={shortHash(fingerprintData.bytes32_hash)} mono />
                  </>
                ) : (
                  <p className="empty-text">No hash generated yet.</p>
                )}
              </div>

              <div className="panel">
                <div className="panel-header">
                  <h2>Blockchain</h2>
                  {verificationData?.verified && <ShieldCheck className="h-4 w-4 text-emerald-600" />}
                </div>
                {blockchainData ? (
                  <>
                    <DataRow label="Transaction" value={shortHash(blockchainData.transaction_hash)} mono />
                    <DataRow label="Block" value={blockchainData.block_number} />
                    <DataRow label="Contract" value={shortHash(blockchainData.contract_address)} mono />
                    <DataRow label="Verified" value={verificationData?.verified ? 'Yes' : 'Pending'} />
                  </>
                ) : (
                  <p className="empty-text">No chain record yet.</p>
                )}
              </div>
            </div>
          </section>
        </div>
      </section>
    </main>
  );
}
