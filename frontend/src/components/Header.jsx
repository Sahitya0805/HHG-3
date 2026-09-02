import React from 'react';
import { ShieldCheck, Cpu, Database, Globe } from 'lucide-react';

export default function Header({ health }) {
  const isOnline = Boolean(health?.status === 'healthy');
  const chainMode = health?.blockchain?.mode === 'live_testnet' ? 'EVM Testnet' : 'Local EVM (Simulated)';

  return (
    <header className="border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <ShieldCheck className="h-6 w-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white">
                FACETRACE
              </h1>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-cyan-950 text-cyan-400 border border-cyan-800/60 uppercase tracking-wider">
                Pipeline v1.0
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Face Identification & Blockchain Verification Pipeline
            </p>
          </div>
        </div>

        {/* System & Privacy Badges */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800/90 border border-slate-700/60 text-slate-300">
            <span className={`h-2 w-2 rounded-full ${isOnline ? 'bg-emerald-400 animate-pulse' : 'bg-rose-500'}`} />
            <span>Backend: {isOnline ? 'Connected' : 'Offline'}</span>
          </div>

          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-slate-800/90 border border-slate-700/60 text-slate-300">
            <Database className="h-3.5 w-3.5 text-cyan-400" />
            <span>{chainMode}</span>
          </div>

          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-lg bg-cyan-950/60 border border-cyan-800/50 text-cyan-300">
            <ShieldCheck className="h-3.5 w-3.5 text-cyan-400" />
            <span className="font-medium">Consented Demo • Zero Biometrics On-Chain</span>
          </div>
        </div>
      </div>
    </header>
  );
}
