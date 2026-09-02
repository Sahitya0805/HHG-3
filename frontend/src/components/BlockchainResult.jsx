import React, { useState } from 'react';
import { Fingerprint, Blocks, Copy, Check, ShieldCheck, Database, RefreshCw } from 'lucide-react';

export default function BlockchainResult({
  fingerprintData,
  blockchainData,
  loading,
  onUploadBlockchain,
  onVerifyBlockchain,
}) {
  const [copiedHash, setCopiedHash] = useState(false);
  const [copiedTx, setCopiedTx] = useState(false);

  if (!fingerprintData && !loading) return null;

  const copyToClipboard = (text, type) => {
    navigator.clipboard.writeText(text);
    if (type === 'hash') {
      setCopiedHash(true);
      setTimeout(() => setCopiedHash(false), 2000);
    } else if (type === 'tx') {
      setCopiedTx(true);
      setTimeout(() => setCopiedTx(false), 2000);
    }
  };

  return (
    <div className="glass-panel rounded-2xl p-6 glow-blue border-slate-800 space-y-6">
      {/* Step 3: Fingerprinting Header */}
      <div>
        <div className="flex items-center space-x-2 mb-4">
          <span className="h-6 w-6 rounded-md bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-xs font-bold border border-cyan-500/30">
            03
          </span>
          <h2 className="text-base font-bold text-white tracking-wide uppercase">
            Cryptographic Fingerprint (SHA-256)
          </h2>
        </div>

        {fingerprintData && (
          <div className="space-y-3">
            <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                Canonical JSON Payload (Deterministic UTF-8 serialization):
              </span>
              <pre className="text-xs font-mono text-cyan-300 bg-slate-900 p-2.5 rounded-lg overflow-x-auto border border-slate-800 whitespace-pre-wrap">
                {fingerprintData.canonical_payload}
              </pre>
            </div>

            <div className="bg-slate-950/80 rounded-xl p-4 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="min-w-0">
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                  SHA-256 Fingerprint Hash:
                </span>
                <span className="font-mono text-xs sm:text-sm text-emerald-400 font-bold break-all">
                  {fingerprintData.bytes32_hash}
                </span>
              </div>
              <button
                onClick={() => copyToClipboard(fingerprintData.bytes32_hash, 'hash')}
                className="shrink-0 flex items-center space-x-1 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition"
              >
                {copiedHash ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Copy className="h-3.5 w-3.5" />}
                <span>{copiedHash ? 'Copied' : 'Copy'}</span>
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Step 4: Blockchain Registration */}
      <div className="pt-4 border-t border-slate-800">
        <div className="flex items-center space-x-2 mb-4">
          <span className="h-6 w-6 rounded-md bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-xs font-bold border border-cyan-500/30">
            04
          </span>
          <h2 className="text-base font-bold text-white tracking-wide uppercase">
            Blockchain Record & Transaction
          </h2>
        </div>

        {!blockchainData ? (
          <button
            type="button"
            onClick={onUploadBlockchain}
            disabled={loading}
            className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm shadow-lg shadow-emerald-500/20 transition-all flex items-center justify-center space-x-2"
          >
            {loading ? (
              <>
                <RefreshCw className="h-4 w-4 animate-spin text-slate-950" />
                <span>Broadcasting Transaction to EVM...</span>
              </>
            ) : (
              <>
                <Blocks className="h-4 w-4" />
                <span>Upload Fingerprint to Blockchain →</span>
              </>
            )}
          </button>
        ) : (
          <div className="space-y-4">
            <div className="bg-emerald-950/20 border border-emerald-500/40 rounded-xl p-4 space-y-3">
              <div className="flex items-center justify-between pb-2 border-b border-emerald-800/30">
                <span className="flex items-center space-x-1.5 text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  <ShieldCheck className="h-4 w-4" />
                  <span>Transaction Confirmed On-Chain</span>
                </span>
                <span className="text-[11px] font-semibold text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                  {blockchainData.mode}
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                <div>
                  <span className="text-slate-400 block mb-0.5">Transaction Hash:</span>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-cyan-300 font-semibold truncate max-w-[200px] sm:max-w-xs">
                      {blockchainData.transaction_hash}
                    </span>
                    <button
                      onClick={() => copyToClipboard(blockchainData.transaction_hash, 'tx')}
                      className="text-slate-400 hover:text-slate-200"
                    >
                      {copiedTx ? <Check className="h-3 w-3 text-emerald-400" /> : <Copy className="h-3 w-3" />}
                    </button>
                  </div>
                </div>

                <div>
                  <span className="text-slate-400 block mb-0.5">Block Number:</span>
                  <span className="font-mono text-slate-200 font-semibold">
                    #{blockchainData.block_number}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block mb-0.5">Submitter Wallet:</span>
                  <span className="font-mono text-slate-300 truncate block">
                    {blockchainData.submitter}
                  </span>
                </div>

                <div>
                  <span className="text-slate-400 block mb-0.5">Verification Registry Contract:</span>
                  <span className="font-mono text-slate-300 truncate block">
                    {blockchainData.contract_address}
                  </span>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={onVerifyBlockchain}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center space-x-2"
            >
              <span>Perform On-Chain Verification →</span>
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
