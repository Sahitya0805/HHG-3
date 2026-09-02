import React, { useRef } from 'react';
import { Upload, User, CheckCircle, AlertTriangle, Sparkles, RefreshCw, XCircle, Ban, ArrowDown, Search, ShieldCheck } from 'lucide-react';

export default function ImageUpload({
  imagePreview,
  faceData,
  loading,
  searchQuery,
  onSearchQueryChange,
  onImageSelected,
  onLoadSample,
  onLoadNonFaceSample,
  onStartSearch,
}) {
  const fileInputRef = useRef(null);

  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onImageSelected(file);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 glow-blue border-slate-800">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center space-x-2">
          <span className="h-6 w-6 rounded-md bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-xs font-bold border border-cyan-500/30">
            01
          </span>
          <h2 className="text-base font-bold text-white tracking-wide uppercase">
            High-Accuracy Face Detection & Alignment
          </h2>
        </div>

        {/* Quick Sample Buttons */}
        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={onLoadSample}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/30 text-xs font-medium transition-all"
            title="Load valid portrait image"
          >
            <Sparkles className="h-3.5 w-3.5" />
            <span>Sample Face</span>
          </button>

          <button
            type="button"
            onClick={onLoadNonFaceSample}
            disabled={loading}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-medium transition-all"
            title="Test detection error with non-face image"
          >
            <Ban className="h-3.5 w-3.5" />
            <span>Test Non-Face</span>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
        {/* Dropzone & Upload Area */}
        <div className="md:col-span-6 flex flex-col justify-between">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileChange}
            accept=".jpg,.jpeg,.png,.webp"
            className="hidden"
          />

          <div
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-xl p-6 flex flex-col items-center justify-center cursor-pointer transition-all min-h-[220px] ${
              faceData && !faceData.face_detected
                ? 'border-rose-500/60 bg-rose-950/20 hover:border-rose-400'
                : imagePreview
                ? 'border-cyan-500/50 bg-slate-900/40 hover:border-cyan-400'
                : 'border-slate-700 hover:border-cyan-500 bg-slate-900/20 hover:bg-slate-900/40'
            }`}
          >
            <div className={`h-12 w-12 rounded-full flex items-center justify-center mb-3 ${
              faceData && !faceData.face_detected
                ? 'bg-rose-500/10 text-rose-400'
                : 'bg-cyan-500/10 text-cyan-400'
            }`}>
              {faceData && !faceData.face_detected ? (
                <XCircle className="h-6 w-6" />
              ) : (
                <Upload className="h-6 w-6" />
              )}
            </div>
            <p className="text-sm font-semibold text-slate-200 text-center">
              {imagePreview ? 'Click to upload a different image' : 'Click to upload face image'}
            </p>
            <p className="text-xs text-slate-500 mt-1 text-center">
              Supports .jpg, .jpeg, .png, .webp (Auto Multi-scale & CLAHE Lighting Normalization)
            </p>
          </div>

          {/* Optional social handle / name tag */}
          <div className="mt-3">
            <div className="flex items-center space-x-1.5 bg-slate-900/80 p-2 rounded-xl border border-slate-800 text-xs">
              <Search className="h-3.5 w-3.5 text-cyan-400 shrink-0" />
              <input
                type="text"
                placeholder="Optional name / handle tag (e.g. sahityasingh, @dev)..."
                value={searchQuery || ''}
                onChange={(e) => onSearchQueryChange(e.target.value)}
                className="bg-transparent border-none outline-none text-slate-200 text-xs w-full placeholder-slate-500"
              />
            </div>
          </div>
        </div>

        {/* Detection Results & Visual Bounding Box Preview */}
        <div className="md:col-span-6 flex flex-col justify-between bg-slate-900/70 rounded-xl p-4 border border-slate-800">
          {faceData ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Detection Status</span>
                {faceData.face_detected ? (
                  <div className="flex items-center space-x-1.5">
                    {faceData.confidence_percent && (
                      <span className="text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800/60">
                        {faceData.confidence_percent}% Conf
                      </span>
                    )}
                    <span className="flex items-center space-x-1 text-xs font-semibold text-emerald-400 bg-emerald-950/60 px-2.5 py-1 rounded-full border border-emerald-800/60 shadow-sm">
                      <CheckCircle className="h-3.5 w-3.5" />
                      <span>Face Detected ({faceData.faces_found})</span>
                    </span>
                  </div>
                ) : (
                  <span className="flex items-center space-x-1 text-xs font-semibold text-rose-400 bg-rose-950/80 px-2.5 py-1 rounded-full border border-rose-800/80 shadow-sm">
                    <XCircle className="h-3.5 w-3.5" />
                    <span>No Face Detected</span>
                  </span>
                )}
              </div>

              {/* Error Callout if Non-Face Image Uploaded */}
              {!faceData.face_detected && (
                <div className="bg-rose-950/50 border border-rose-500/60 rounded-xl p-4 text-rose-200 space-y-1">
                  <div className="flex items-center space-x-2 font-bold text-xs text-rose-300">
                    <AlertTriangle className="h-4 w-4 text-rose-400 shrink-0" />
                    <span>INVALID INPUT — NON-FACE IMAGE</span>
                  </div>
                  <p className="text-xs text-rose-300/90 pl-6">
                    {faceData.error || 'No human face detected in this image. Please upload a clear photo containing a human face.'}
                  </p>
                </div>
              )}

              {/* Image Preview & Aligned Face Crop */}
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-slate-950 rounded-lg p-2 border border-slate-800 flex flex-col items-center">
                  <span className="text-[10px] text-slate-400 mb-1">Landmarks & Bounding Box</span>
                  <img
                    src={faceData.annotated_image_b64 || imagePreview}
                    alt="Annotated Face"
                    className="h-28 object-contain rounded"
                  />
                </div>

                <div className="bg-slate-950 rounded-lg p-2 border border-slate-800 flex flex-col items-center">
                  <span className="text-[10px] text-slate-400 mb-1">Aligned & Scaled Face Crop</span>
                  {faceData.primary_crop_b64 ? (
                    <img
                      src={faceData.primary_crop_b64}
                      alt="Crop"
                      className="h-28 object-contain rounded border border-cyan-500/40"
                    />
                  ) : (
                    <div className="h-28 flex flex-col items-center justify-center text-xs text-slate-600 space-y-1">
                      <Ban className="h-5 w-5 text-slate-700" />
                      <span>No Face Cropped</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Vector Embedding Stats */}
              {faceData.embedding_generated && (
                <div className="bg-slate-950/80 rounded-lg p-2.5 border border-slate-800/80">
                  <div className="flex items-center justify-between text-xs text-slate-400 mb-1.5">
                    <span>Facial Embedding:</span>
                    <span className="font-mono text-cyan-400 font-bold">{faceData.embedding_dimensions} dims (L2 Normalized)</span>
                  </div>
                  <div className="text-[10px] font-mono text-slate-500 truncate bg-slate-900 p-1.5 rounded border border-slate-800">
                    [{faceData.sample_vector?.slice(0, 6).join(', ')}...]
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full min-h-[200px] flex flex-col items-center justify-center text-slate-500">
              <User className="h-10 w-10 text-slate-700 mb-2" />
              <p className="text-xs">Upload an image to inspect facial detection</p>
            </div>
          )}

          {faceData?.face_detected && (
            <button
              type="button"
              onClick={onStartSearch}
              disabled={loading}
              className="mt-4 w-full py-3 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-extrabold text-sm shadow-lg shadow-cyan-500/25 transition-all flex items-center justify-center space-x-2 animate-pulse hover:animate-none cursor-pointer"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-4 w-4 animate-spin text-slate-950" />
                  <span>Searching Public Web & Social Posts...</span>
                </>
              ) : (
                <>
                  <span>Proceed to Reverse Web Search</span>
                  <ArrowDown className="h-4 w-4" />
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
