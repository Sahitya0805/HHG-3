import React, { useState, useEffect } from 'react';
import { AlertTriangle, XCircle, CheckCircle, RefreshCw, Undo, ShieldAlert } from 'lucide-react';
import { testTampering } from '../api';

export default function TamperDemo({
  originalMetadata,
  onChainHash,
  onClose,
}) {
  const [tamperedMetadata, setTamperedMetadata] = useState(
    JSON.parse(JSON.stringify(originalMetadata || {}))
  );
  const [tamperResult, setTamperResult] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    runTamperCheck(tamperedMetadata);
  }, []);

  const runTamperCheck = async (currentMetadata) => {
    if (!originalMetadata || !onChainHash) return;
    try {
      setLoading(true);
      const res = await testTampering(originalMetadata, currentMetadata, onChainHash);
      setTamperResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFieldChange = (field, value) => {
    const updated = { ...tamperedMetadata, [field]: value };
    setTamperedMetadata(updated);
    runTamperCheck(updated);
  };

  const handlePresetTamper = () => {
    const updated = {
      ...tamperedMetadata,
      caption: 'Tampered caption inserted by adversary (Unauthorized modification)',
    };
    setTamperedMetadata(updated);
    runTamperCheck(updated);
  };

  const handleReset = () => {
    const original = JSON.parse(JSON.stringify(originalMetadata || {}));
    setTamperedMetadata(original);
    runTamperCheck(original);
  };

  if (!originalMetadata) return null;

  return (
    <div className="glass-panel rounded-2xl p-6 glow-rose border-rose-900/60 space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="h-7 w-7 rounded-lg bg-rose-500/20 text-rose-400 flex items-center justify-center border border-rose-500/30">
            <ShieldAlert className="h-4 w-4" />
          </div>
          <h2 className="text-base font-bold text-white tracking-wide uppercase">
            Tampering Demonstration Lab
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <button
            type="button"
            onClick={handlePresetTamper}
            className="px-2.5 py-1 rounded-lg bg-rose-950 text-rose-300 border border-rose-800/60 text-xs font-semibold hover:bg-rose-900 transition"
          >
            Inject Sample Tamper
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 border border-slate-700 text-xs font-semibold hover:bg-slate-700 transition flex items-center space-x-1"
          >
            <Undo className="h-3 w-3" />
            <span>Reset</span>
          </button>
        </div>
      </div>

      <p className="text-xs text-slate-400">
        Modify any field below to see how even a single altered character changes the cryptographic SHA-256 fingerprint, triggering an instant tamper alert against the immutable on-chain record.
      </p>

      {/* Editable Fields Form */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="space-y-1">
          <label className="text-[11px] font-bold text-slate-400 uppercase">Post Title</label>
          <input
            type="text"
            value={tamperedMetadata.title || ''}
            onChange={(e) => handleFieldChange('title', e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded-lg p-2.5 text-slate-200"
          />
        </div>

        <div className="space-y-1">
          <label className="text-[11px] font-bold text-slate-400 uppercase">Post Caption / Snippet</label>
          <input
            type="text"
            value={tamperedMetadata.caption || ''}
            onChange={(e) => handleFieldChange('caption', e.target.value)}
            className="w-full text-xs bg-slate-950 border border-slate-700 focus:border-cyan-500 rounded-lg p-2.5 text-slate-200"
          />
        </div>
      </div>

      {/* Tamper Comparison Card */}
      {tamperResult && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-slate-950/90 p-3.5 rounded-xl border border-slate-800">
              <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                Immutable On-Chain Hash:
              </span>
              <span className="font-mono text-xs text-emerald-400 font-bold break-all block">
                {tamperResult.on_chain_hash}
              </span>
            </div>

            <div className={`p-3.5 rounded-xl border ${tamperResult.tamper_detected ? 'bg-rose-950/30 border-rose-500/50' : 'bg-slate-950/90 border-slate-800'}`}>
              <span className="text-[10px] font-bold text-slate-400 uppercase block mb-1">
                Recalculated Hash:
              </span>
              <span className={`font-mono text-xs font-bold break-all block ${tamperResult.tamper_detected ? 'text-rose-400' : 'text-emerald-400'}`}>
                {tamperResult.tampered_hash}
              </span>
            </div>
          </div>

          {/* Tamper Outcome Status */}
          <div
            className={`p-4 rounded-xl border flex items-center justify-between ${
              tamperResult.tamper_detected
                ? 'bg-rose-950/50 border-rose-500 text-rose-200'
                : 'bg-emerald-950/50 border-emerald-500 text-emerald-200'
            }`}
          >
            <div className="flex items-center space-x-3">
              {tamperResult.tamper_detected ? (
                <XCircle className="h-6 w-6 text-rose-400 shrink-0" />
              ) : (
                <CheckCircle className="h-6 w-6 text-emerald-400 shrink-0" />
              )}
              <div>
                <h4 className="text-sm font-extrabold tracking-wide">
                  {tamperResult.tamper_detected ? '❌ HASH MISMATCH — DATA TAMPERED' : '✓ HASH MATCH — AUTHENTIC DATA'}
                </h4>
                <p className="text-xs opacity-90 mt-0.5">
                  {tamperResult.tamper_detected
                    ? `Altered fields detected: ${tamperResult.altered_fields.map((f) => f.field).join(', ') || 'Metadata'}. Immutability check prevented forged verification.`
                    : 'Current data perfectly matches the immutable on-chain record.'}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
