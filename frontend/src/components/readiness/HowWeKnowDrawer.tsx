import React from 'react';
import { X, ShieldCheck, Clock, FileCode } from 'lucide-react';
import type { ActionCard } from '../../types/readiness';
import { TrustBadge } from './TrustBadge';

interface HowWeKnowDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  action: ActionCard;
}

export function HowWeKnowDrawer({ isOpen, onClose, action }: HowWeKnowDrawerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-900/20 backdrop-blur-sm">
      <div className="w-full max-w-md bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-800">How We Know</h2>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-slate-100 text-slate-500 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          <div className="space-y-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">Verification Source</h3>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div>
                <p className="font-medium text-slate-900">{action.verification_method}</p>
                <p className="text-sm text-slate-500">Automated Connector</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">Confidence</h3>
            <div className="flex items-center gap-4">
              <div className="text-3xl font-light text-slate-900">{action.confidence_pct}%</div>
              <TrustBadge 
                status="verified" 
                text={action.confidence_pct >= 90 ? "High Confidence" : "Needs Review"} 
              />
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">Last Verified</h3>
            <div className="flex items-center gap-2 text-slate-700">
              <Clock className="w-4 h-4 text-slate-400" />
              {action.last_verified_at}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-sm font-bold tracking-wider text-slate-400 uppercase">Raw Evidence</h3>
            <div className="bg-slate-900 rounded-xl p-4 overflow-x-auto">
              <pre className="text-emerald-400 text-xs font-mono whitespace-pre-wrap leading-relaxed">
                {action.evidence}
              </pre>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
