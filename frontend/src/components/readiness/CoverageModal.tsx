import React from 'react';
import { X, CheckCircle2, ShieldAlert } from 'lucide-react';
import type { CoverageReport } from '../../types/readiness';

interface CoverageModalProps {
  isOpen: boolean;
  onClose: () => void;
  coverage: CoverageReport;
}

export function CoverageModal({ isOpen, onClose, coverage }: CoverageModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-sm">
      <div 
        className="bg-white rounded-3xl shadow-xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
      >
        <div className="p-6 border-b border-slate-100 flex items-center justify-between">
          <h2 className="text-xl font-bold text-slate-800">What We Can Verify</h2>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-slate-100 transition-colors text-slate-500"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6">
          <p className="text-slate-600 mb-8">
            This represents our visibility into your systems. Unmonitored items represent potential blind spots in your readiness assessment.
          </p>
          
          <div className="space-y-6">
            {coverage.areas.map((area, index) => (
              <div key={index} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-slate-800">{area.name}</h3>
                  <span className="text-sm font-medium text-slate-500">{area.percentage}% Monitored</span>
                </div>
                
                {/* Progress bar */}
                <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden flex">
                  <div 
                    className="h-full bg-emerald-500 transition-all duration-1000"
                    style={{ width: `${area.percentage}%` }}
                  />
                  <div 
                    className="h-full bg-amber-400/50 transition-all duration-1000"
                    style={{ width: `${100 - area.percentage}%` }}
                  />
                </div>
                
                <div className="flex items-center gap-6 text-sm">
                  <div className="flex items-center gap-1.5 text-emerald-600">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{area.monitored_items} items monitored</span>
                  </div>
                  {area.unmonitored_items > 0 && (
                    <div className="flex items-center gap-1.5 text-amber-600">
                      <ShieldAlert className="w-4 h-4" />
                      <span>{area.unmonitored_items} items unmonitored</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="p-6 bg-slate-50 border-t border-slate-100 flex justify-end">
          <button 
            onClick={onClose}
            className="px-6 py-2.5 bg-slate-900 text-white font-medium rounded-xl hover:bg-slate-800 transition-colors"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
