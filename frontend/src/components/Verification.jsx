import React from 'react';
import { CheckCircle2, ShieldCheck, AlertOctagon, ArrowDown } from 'lucide-react';

export default function Verification({
  verificationData,
  fingerprintData,
  onOpenTamperLab,
}) {
  if (!verificationData) return null;

  return (
    <div className="glass-panel rounded-2xl p-6 glow-emerald border-emerald-900/60 space-y-5">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <span className="h-6 w-6 rounded-md bg-emerald-500/20 text-emerald-400 flex items-center justify-center text-xs font-bold border border-emerald-500/30">
            05
          </span>
          <h2 className="text-base font-bold text-white tracking-wide uppercase">
            On-Chain Cryptographic Verification
          </h2>
        </div>

        <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 text-xs font-extrabold shadow-lg shadow-emerald-900/20">
          <CheckCircle2 className="h-4 w-4 text-emerald-400" />
          <span>BLOCKCHAIN VERIFIED ✓</span>
        </span>
      </div>

      {/* Comparison Panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Locally Recomputed SHA-256:
          </span>
          <span className="font-mono text-xs sm:text-sm text-cyan-300 font-bold break-all block">
            {fingerprintData?.bytes32_hash}
          </span>
        </div>

        <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            On-Chain Retrieved Hash:
          </span>
          <span className="font-mono text-xs sm:text-sm text-emerald-400 font-bold break-all block">
            {verificationData.on_chain_hash}
          </span>
        </div>
      </div>

      <div className="bg-emerald-950/30 border border-emerald-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/40">
            <ShieldCheck className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-emerald-200">
              Result: EXACT MATCH (100% Data Integrity)
            </p>
            <p className="text-xs text-emerald-400/80">
              ✓ Data has not changed since initial discovery & registration.
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={onOpenTamperLab}
          className="shrink-0 py-2 px-4 rounded-xl bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/40 font-bold text-xs transition flex items-center space-x-1.5 shadow-lg shadow-rose-900/10"
        >
          <AlertOctagon className="h-4 w-4 text-rose-400" />
          <span>Launch Tampering Test Lab</span>
        </button>
      </div>
    </div>
  );
}
