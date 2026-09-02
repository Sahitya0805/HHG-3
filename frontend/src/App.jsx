import React, { useState, useEffect, useRef } from 'react';
import Header from './components/Header';
import StepIndicator from './components/StepIndicator';
import ImageUpload from './components/ImageUpload';
import SearchResult from './components/SearchResult';
import BlockchainResult from './components/BlockchainResult';
import Verification from './components/Verification';
import TamperDemo from './components/TamperDemo';
import {
  checkHealth,
  uploadAndDetectFace,
  searchReverseImage,
  generateFingerprint,
  storeOnBlockchain,
  verifyOnBlockchain,
  runFullPipeline,
} from './api';
import { Play, RotateCcw, AlertCircle, Sparkles } from 'lucide-react';

export default function App() {
  const [health, setHealth] = useState(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [faceData, setFaceData] = useState(null);
  const [searchData, setSearchData] = useState(null);
  const [fingerprintData, setFingerprintData] = useState(null);
  const [blockchainData, setBlockchainData] = useState(null);
  const [verificationData, setVerificationData] = useState(null);
  const [showTamperLab, setShowTamperLab] = useState(false);

  const [loading, setLoading] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  const searchSectionRef = useRef(null);
  const blockchainSectionRef = useRef(null);
  const verificationSectionRef = useRef(null);

  useEffect(() => {
    checkHealth()
      .then(setHealth)
      .catch((err) => console.error('Health check error:', err));
  }, []);

  const handleImageSelected = async (file) => {
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setErrorMessage(null);
    setShowTamperLab(false);
    setSearchData(null);
    setFingerprintData(null);
    setBlockchainData(null);
    setVerificationData(null);
    setCurrentStep(1);

    try {
      setLoading(true);
      const data = await uploadAndDetectFace(file);
      setFaceData(data);
      if (!data.face_detected) {
        setErrorMessage(data.error || 'No human face detected. Please upload an image with a visible face.');
      } else {
        setErrorMessage(null);
        // Automatically trigger search
        executeSearch(data.embedding, data.primary_crop_b64, searchQuery);
      }
    } catch (err) {
      setFaceData({
        face_detected: false,
        faces_found: 0,
        error: err.message || 'No human face detected. Please upload an image with a visible face.',
      });
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const executeSearch = async (embedding, cropB64, query = null) => {
    try {
      setLoading(true);
      setCurrentStep(2);
      setTimeout(() => {
        searchSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);

      const targetQuery = query !== null ? query : searchQuery;
      const data = await searchReverseImage(embedding, cropB64, targetQuery);
      setSearchData(data);
      setCurrentStep(2);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadSample = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const res = await fetch('https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80');
      const blob = await res.blob();
      const file = new File([blob], 'consented_face_sample.jpg', { type: 'image/jpeg' });
      await handleImageSelected(file);
    } catch (err) {
      const response = await fetch('data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="300" height="300"><rect width="300" height="300" fill="%23f0f4f8"/><circle cx="150" cy="150" r="70" fill="%23fbcfe8"/><circle cx="125" cy="135" r="8" fill="%231e293b"/><circle cx="175" cy="135" r="8" fill="%231e293b"/><path d="M 130 180 Q 150 200 170 180" stroke="%23e11d48" stroke-width="4" fill="none"/></svg>');
      const blob = await response.blob();
      const file = new File([blob], 'demo_face.jpg', { type: 'image/jpeg' });
      await handleImageSelected(file);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadNonFaceSample = async () => {
    try {
      setLoading(true);
      setErrorMessage(null);
      const canvas = document.createElement('canvas');
      canvas.width = 400;
      canvas.height = 300;
      const ctx = canvas.getContext('2d');
      ctx.fillStyle = '#1e293b';
      ctx.fillRect(0, 0, 400, 300);
      ctx.fillStyle = '#0284c7';
      ctx.fillRect(80, 120, 240, 80);
      ctx.fillStyle = '#0f172a';
      ctx.beginPath();
      ctx.arc(130, 210, 25, 0, Math.PI * 2);
      ctx.arc(270, 210, 25, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 20px sans-serif';
      ctx.fillText('NON-FACE OBJECT (CAR)', 70, 80);

      canvas.toBlob(async (blob) => {
        const file = new File([blob], 'non_face_car.png', { type: 'image/png' });
        await handleImageSelected(file);
      }, 'image/png');
    } catch (err) {
      setErrorMessage('Could not generate non-face test image');
    } finally {
      setLoading(false);
    }
  };

  const handleStartSearch = async () => {
    if (!faceData?.embedding) return;
    await executeSearch(faceData.embedding, faceData.primary_crop_b64, searchQuery);
  };

  const handleProceedToHash = async () => {
    if (!searchData?.metadata) return;
    try {
      setLoading(true);
      setErrorMessage(null);
      setCurrentStep(3);
      const data = await generateFingerprint(searchData.metadata);
      setFingerprintData(data);
      setTimeout(() => {
        blockchainSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUploadBlockchain = async () => {
    if (!fingerprintData?.hash) return;
    try {
      setLoading(true);
      setErrorMessage(null);
      setCurrentStep(4);
      const data = await storeOnBlockchain(fingerprintData.hash);
      setBlockchainData(data);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyBlockchain = async () => {
    if (!fingerprintData?.hash) return;
    try {
      setLoading(true);
      setErrorMessage(null);
      setCurrentStep(5);
      const data = await verifyOnBlockchain(fingerprintData.hash);
      setVerificationData(data);
      setTimeout(() => {
        verificationSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 100);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRunFullPipeline = async () => {
    let targetFile = imageFile;
    if (!targetFile || (faceData && !faceData.face_detected)) {
      try {
        const res = await fetch('https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&auto=format&fit=crop&q=80');
        const blob = await res.blob();
        targetFile = new File([blob], 'consented_face_sample.jpg', { type: 'image/jpeg' });
        setImageFile(targetFile);
        setImagePreview(URL.createObjectURL(targetFile));
      } catch (e) {
        return;
      }
    }

    try {
      setPipelineRunning(true);
      setErrorMessage(null);

      const fullData = await runFullPipeline(targetFile);
      setFaceData({
        face_detected: true,
        faces_found: fullData.face.faces_found,
        embedding_generated: true,
        embedding_dimensions: fullData.face.embedding_dimensions,
        primary_crop_b64: fullData.face.primary_crop_b64,
        annotated_image_b64: fullData.face.annotated_image_b64,
        sample_vector: fullData.face.sample_vector,
      });
      setSearchData({
        provider_name: fullData.search.provider,
        total_candidates: fullData.search.candidates.length,
        candidates: fullData.search.candidates,
        best_match: fullData.search.best_match,
        metadata: fullData.metadata,
      });
      setFingerprintData(fullData.fingerprint);
      setBlockchainData(fullData.blockchain);
      setVerificationData(fullData.verification);
      setCurrentStep(5);

      setTimeout(() => {
        verificationSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }, 200);
    } catch (err) {
      setErrorMessage(err.message);
    } finally {
      setPipelineRunning(false);
    }
  };

  const handleReset = () => {
    setImageFile(null);
    setImagePreview(null);
    setSearchQuery('');
    setFaceData(null);
    setSearchData(null);
    setFingerprintData(null);
    setBlockchainData(null);
    setVerificationData(null);
    setShowTamperLab(false);
    setErrorMessage(null);
    setCurrentStep(1);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col justify-between">
      <div>
        <Header health={health} />
        <StepIndicator currentStep={currentStep} />

        <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-6">
          {/* Quick Actions Bar */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-2xl border border-slate-800">
            <div className="flex items-center space-x-2">
              <span className="h-2 w-2 rounded-full bg-cyan-400 animate-pulse" />
              <span className="text-xs font-semibold text-slate-300">
                Privacy-First Automated Verification Pipeline
              </span>
            </div>

            <div className="flex items-center space-x-2 w-full sm:w-auto">
              <button
                type="button"
                onClick={handleRunFullPipeline}
                disabled={pipelineRunning || loading}
                className="flex-1 sm:flex-none flex items-center justify-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs shadow-lg shadow-cyan-500/20 transition-all cursor-pointer"
              >
                <Play className="h-3.5 w-3.5 fill-current" />
                <span>{pipelineRunning ? 'Executing Pipeline...' : 'Run 1-Click Complete Pipeline'}</span>
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 text-xs transition cursor-pointer"
                title="Reset All"
              >
                <RotateCcw className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Error Message Toast */}
          {errorMessage && (
            <div className="bg-rose-950/70 border border-rose-500/60 rounded-xl p-4 flex items-center space-x-3 text-rose-200 text-xs shadow-lg shadow-rose-950/30">
              <AlertCircle className="h-5 w-5 text-rose-400 shrink-0" />
              <span className="font-semibold">{errorMessage}</span>
            </div>
          )}

          {/* Step 1: Face Detection */}
          <ImageUpload
            imagePreview={imagePreview}
            faceData={faceData}
            loading={loading}
            searchQuery={searchQuery}
            onSearchQueryChange={setSearchQuery}
            onImageSelected={handleImageSelected}
            onLoadSample={handleLoadSample}
            onLoadNonFaceSample={handleLoadNonFaceSample}
            onStartSearch={handleStartSearch}
          />

          {/* Step 2: Reverse Search */}
          <div ref={searchSectionRef} id="step-search-results">
            {faceData?.face_detected && (currentStep >= 2 || searchData || loading) && (
              <SearchResult
                searchData={searchData}
                loading={loading && currentStep === 2}
                onProceedToHash={handleProceedToHash}
              />
            )}
          </div>

          {/* Step 3 & 4: Fingerprint & Blockchain Registration */}
          <div ref={blockchainSectionRef}>
            {faceData?.face_detected && (currentStep >= 3 || fingerprintData) && (
              <BlockchainResult
                fingerprintData={fingerprintData}
                blockchainData={blockchainData}
                loading={loading && (currentStep === 3 || currentStep === 4)}
                onUploadBlockchain={handleUploadBlockchain}
                onVerifyBlockchain={handleVerifyBlockchain}
              />
            )}
          </div>

          {/* Step 5: On-Chain Verification */}
          <div ref={verificationSectionRef}>
            {faceData?.face_detected && (currentStep >= 5 || verificationData) && (
              <Verification
                verificationData={verificationData}
                fingerprintData={fingerprintData}
                onOpenTamperLab={() => setShowTamperLab(true)}
              />
            )}
          </div>

          {/* Step 6: Interactive Tampering Demonstration Lab */}
          {faceData?.face_detected && showTamperLab && searchData?.metadata && (
            <TamperDemo
              originalMetadata={searchData.metadata}
              onChainHash={verificationData?.on_chain_hash || fingerprintData?.bytes32_hash}
              onClose={() => setShowTamperLab(false)}
            />
          )}
        </main>
      </div>

      <footer className="max-w-5xl mx-auto w-full px-4 py-6 text-center text-xs text-slate-500 border-t border-slate-900 mt-8">
        FaceTrace Pipeline • Built for Hackathon Evaluation • Privacy-preserving Biometric Blockchain Verification
      </footer>
    </div>
  );
}
