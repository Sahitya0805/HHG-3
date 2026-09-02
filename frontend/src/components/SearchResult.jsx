import React from 'react';
import { Globe, ExternalLink, Award, Search, ArrowRight, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function SearchResult({
  searchData,
  loading,
  onProceedToHash,
}) {
  if (!searchData && !loading) return null;

  const getPlatformStyle = (source) => {
    const s = (source || '').toLowerCase();
    if (s.includes('instagram')) return 'bg-gradient-to-r from-purple-500/20 to-pink-500/20 text-pink-300 border-pink-500/40';
    if (s.includes('twitter') || s.includes('x')) return 'bg-slate-800 text-cyan-300 border-cyan-500/40';
    if (s.includes('linkedin')) return 'bg-blue-950 text-blue-300 border-blue-500/40';
    if (s.includes('facebook')) return 'bg-indigo-950 text-indigo-300 border-indigo-500/40';
    return 'bg-slate-800 text-slate-300 border-slate-700';
  };

  return (
    <div className="glass-panel rounded-2xl p-6 glow-blue border-slate-800 transition-all">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <span className="h-6 w-6 rounded-md bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-xs font-bold border border-cyan-500/30">
            02
          </span>
          <h2 className="text-base font-bold text-white tracking-wide uppercase">
            Genuine Reverse Image Search & Social Media Matching
          </h2>
        </div>

        {searchData && (
          <span className="text-xs text-slate-400 bg-slate-900 px-2.5 py-1 rounded-lg border border-slate-800">
            Search Mode: <span className="text-cyan-400 font-semibold">{searchData.provider_name}</span>
          </span>
        )}
      </div>

      {loading ? (
        <div className="py-12 flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <div className="h-16 w-16 rounded-full border-4 border-cyan-500/20 border-t-cyan-400 animate-spin" />
            <Search className="h-6 w-6 text-cyan-400 absolute inset-0 m-auto animate-pulse" />
          </div>
          <div className="text-center">
            <p className="text-sm font-semibold text-slate-200">Querying External Social Indexes & Visual Matches...</p>
            <p className="text-xs text-slate-500 mt-1">
              Locating matching public posts, downloading candidate imagery, and calculating facial cosine similarity
            </p>
          </div>
        </div>
      ) : searchData ? (
        <div className="space-y-6">
          {/* Best Match Highlight Banner */}
          {searchData.best_match && (
            <div className="bg-gradient-to-br from-cyan-950/40 via-slate-900/80 to-blue-950/30 rounded-xl p-4 sm:p-5 border border-cyan-500/40 shadow-lg">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-cyan-800/40 mb-3">
                <div className="flex items-center space-x-2">
                  <Award className="h-5 w-5 text-cyan-400" />
                  <span className="text-sm font-extrabold text-cyan-300 uppercase tracking-wider">
                    Strongest Public Match Found
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40">
                    Similarity: {searchData.best_match.similarity_percent}% ({searchData.best_match.match_label})
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-12 gap-4 items-center">
                <div className="sm:col-span-8 space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full border ${getPlatformStyle(searchData.best_match.source)}`}>
                      {searchData.best_match.source}
                    </span>
                    <a
                      href={searchData.best_match.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-cyan-400 hover:text-cyan-300 flex items-center space-x-1 truncate max-w-[280px]"
                    >
                      <span className="truncate">{searchData.best_match.url}</span>
                      <ExternalLink className="h-3 w-3 shrink-0" />
                    </a>
                  </div>
                  <h3 className="text-sm font-bold text-white line-clamp-1">
                    {searchData.best_match.title}
                  </h3>
                  <p className="text-xs text-slate-300 line-clamp-2 italic bg-slate-950/60 p-2.5 rounded-lg border border-slate-800/80">
                    "{searchData.best_match.snippet}"
                  </p>
                </div>

                <div className="sm:col-span-4 flex justify-end">
                  {searchData.best_match.image_url && (
                    <div className="relative">
                      <img
                        src={searchData.best_match.image_url}
                        alt="Discovered Match"
                        className="h-24 w-24 sm:h-28 sm:w-28 object-cover rounded-xl border border-cyan-500/40 shadow-md"
                      />
                      <span className="absolute bottom-1 right-1 bg-slate-950/90 text-[10px] text-cyan-300 px-1.5 py-0.5 rounded border border-slate-700">
                        {searchData.best_match.source}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Candidate Results Table/List */}
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5">
              All Discovered Public Candidates ({searchData.total_candidates})
            </h4>
            <div className="space-y-2">
              {searchData.candidates.map((cand) => (
                <div
                  key={cand.rank}
                  className="bg-slate-900/60 hover:bg-slate-900/90 p-3 rounded-xl border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 transition-colors"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <span className="text-xs font-mono font-bold text-slate-500 bg-slate-950 px-2 py-1 rounded">
                      #{cand.rank}
                    </span>
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2">
                        <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${getPlatformStyle(cand.source)}`}>
                          {cand.source}
                        </span>
                        <span className="text-[11px] text-slate-500">•</span>
                        <span className="text-xs text-slate-300 truncate max-w-[200px] sm:max-w-md font-medium">
                          {cand.title}
                        </span>
                      </div>
                      <a
                        href={cand.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[11px] text-cyan-400/80 hover:text-cyan-300 truncate block mt-0.5"
                      >
                        {cand.url}
                      </a>
                    </div>
                  </div>

                  {/* Similarity meter */}
                  <div className="flex items-center space-x-3 shrink-0 self-end sm:self-auto">
                    <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          cand.similarity >= 0.9
                            ? 'bg-emerald-400'
                            : cand.similarity >= 0.8
                            ? 'bg-amber-400'
                            : 'bg-slate-600'
                        }`}
                        style={{ width: `${cand.similarity_percent}%` }}
                      />
                    </div>
                    <span className="text-xs font-mono font-bold text-slate-200 w-12 text-right">
                      {cand.similarity_percent}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={onProceedToHash}
              className="w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-sm shadow-lg shadow-cyan-500/20 transition-all flex items-center justify-center space-x-2"
            >
              <span>Canonicalize Metadata & Generate SHA-256 Fingerprint →</span>
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
