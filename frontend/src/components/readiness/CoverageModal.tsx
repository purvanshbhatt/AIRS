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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <div 
        className="bg-surface-container-low border border-outline-variant rounded-3xl shadow-2xl w-full max-w-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200"
      >
        <div className="p-6 border-b border-outline-variant/60 flex items-center justify-between">
          <h2 className="text-xl font-bold text-on-surface">What We Can Verify</h2>
          <button 
            onClick={onClose}
            className="p-2 rounded-full hover:bg-surface-container-high transition-colors text-on-surface-variant cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6">
          <p className="text-on-surface-variant text-sm mb-8 leading-relaxed">
            This represents our visibility into your systems. Unmonitored items represent potential blind spots in your readiness assessment.
          </p>
          
          <div className="space-y-6">
            {coverage.areas.map((area, index) => (
              <div key={index} className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-semibold text-on-surface text-sm">{area.name}</h3>
                  <span className="text-xs font-mono font-medium text-on-surface-variant">{area.percentage}% Monitored</span>
                </div>
                
                {/* Progress bar */}
                <div className="h-3 w-full bg-surface-container-highest rounded-full overflow-hidden flex">
                  <div 
                    className="h-full bg-ready-emerald transition-all duration-1000"
                    style={{ width: `${area.percentage}%` }}
                  />
                  <div 
                    className="h-full bg-drift-amber/50 transition-all duration-1000"
                    style={{ width: `${100 - area.percentage}%` }}
                  />
                </div>
                
                <div className="flex items-center gap-6 text-xs">
                  <div className="flex items-center gap-1.5 text-ready-emerald font-medium">
                    <CheckCircle2 className="w-4 h-4" />
                    <span>{area.monitored_items} items monitored</span>
                  </div>
                  {area.unmonitored_items > 0 && (
                    <div className="flex items-center gap-1.5 text-drift-amber font-medium">
                      <ShieldAlert className="w-4 h-4" />
                      <span>{area.unmonitored_items} items unmonitored</span>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        <div className="p-6 bg-surface-container border-t border-outline-variant/60 flex justify-end">
          <button 
            onClick={onClose}
            className="px-6 py-2.5 bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-semibold text-sm rounded-xl border border-outline-variant/60 transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
}
