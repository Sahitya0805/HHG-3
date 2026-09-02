import React from 'react';
import { UserCheck, Globe, Fingerprint, Blocks, CheckCircle2 } from 'lucide-react';

export default function StepIndicator({ currentStep }) {
  const steps = [
    { id: 1, name: 'Face Input', icon: UserCheck },
    { id: 2, name: 'Web Search', icon: Globe },
    { id: 3, name: 'SHA-256 Hash', icon: Fingerprint },
    { id: 4, name: 'Blockchain', icon: Blocks },
    { id: 5, name: 'Verification', icon: CheckCircle2 },
  ];

  return (
    <div className="w-full max-w-5xl mx-auto my-6 px-4">
      <div className="grid grid-cols-2 md:grid-cols-5 gap-2.5 sm:gap-4">
        {steps.map((step) => {
          const Icon = step.icon;
          const isCompleted = currentStep > step.id;
          const isCurrent = currentStep === step.id;

          return (
            <div
              key={step.id}
              className={`flex items-center space-x-3 p-2.5 rounded-xl border transition-all duration-300 ${
                isCurrent
                  ? 'bg-cyan-950/40 border-cyan-500/80 shadow-lg shadow-cyan-500/10'
                  : isCompleted
                  ? 'bg-slate-900/80 border-emerald-500/50 text-slate-200'
                  : 'bg-slate-900/40 border-slate-800 text-slate-500'
              }`}
            >
              <div
                className={`h-8 w-8 rounded-lg flex items-center justify-center shrink-0 text-sm font-bold ${
                  isCurrent
                    ? 'bg-cyan-500 text-slate-950 font-extrabold'
                    : isCompleted
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
                    : 'bg-slate-800 text-slate-500'
                }`}
              >
                {isCompleted ? '✓' : `0${step.id}`}
              </div>
              <div className="min-w-0">
                <p className={`text-xs font-semibold truncate ${isCurrent ? 'text-cyan-300' : isCompleted ? 'text-slate-200' : 'text-slate-400'}`}>
                  {step.name}
                </p>
                <p className="text-[10px] text-slate-500 truncate">
                  {isCompleted ? 'Completed' : isCurrent ? 'Active' : 'Pending'}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
