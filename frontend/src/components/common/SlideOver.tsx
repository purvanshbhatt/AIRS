import React, { ReactNode } from 'react';
import { X, AlertCircle } from 'lucide-react';
import { Button } from '../ui';

interface SlideOverProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  isLoading?: boolean;
  isEmpty?: boolean;
  error?: string | null;
  emptyMessage?: string;
  errorMessage?: string;
  onRetry?: () => void;
}

export function SlideOver({
  isOpen,
  onClose,
  title,
  children,
  isLoading = false,
  isEmpty = false,
  error = null,
  emptyMessage = "No details available.",
  errorMessage = "Failed to load details. Please try again.",
  onRetry,
}: SlideOverProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden" aria-labelledby="slide-over-title" role="dialog" aria-modal="true">
      <div className="absolute inset-0 overflow-hidden">
        {/* Glassmorphic Backdrop overlay */}
        <div 
          className="absolute inset-0 bg-slate-950/40 backdrop-blur-[4px] transition-opacity duration-300" 
          onClick={onClose}
        />

        <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10">
          <div className="pointer-events-auto w-screen max-w-md transform transition-all duration-300 ease-in-out">
            {/* SlideOver Panel (Glassmorphic design system) */}
            <div className="flex h-full flex-col bg-white/80 dark:bg-slate-900/80 backdrop-blur-[20px] shadow-2xl border-l border-slate-200 dark:border-slate-800 text-left">
              {/* Header */}
              <div className="px-6 py-5 border-b border-slate-200 dark:border-slate-800 flex items-center justify-between">
                <h2 className="text-lg font-bold text-slate-900 dark:text-slate-100" id="slide-over-title">
                  {title}
                </h2>
                <button
                  type="button"
                  className="rounded-lg p-1.5 text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
                  onClick={onClose}
                >
                  <span className="sr-only">Close panel</span>
                  <X className="h-5 w-5" aria-hidden="true" />
                </button>
              </div>

              {/* Body Content */}
              <div className="relative flex-1 overflow-y-auto p-6">
                {isLoading ? (
                  <div className="flex flex-col items-center justify-center h-48 space-y-3">
                    <svg className="animate-spin h-8 w-8 text-primary-500" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">Retrieving driver audit trail...</p>
                  </div>
                ) : error ? (
                  <div className="flex flex-col items-center justify-center h-48 text-center px-4 space-y-4">
                    <div className="p-3 bg-danger-500/10 rounded-full">
                      <AlertCircle className="h-8 w-8 text-danger-500" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-slate-900 dark:text-slate-100">Error Loading Details</h4>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{error || errorMessage}</p>
                    </div>
                    {onRetry && (
                      <Button size="sm" onClick={onRetry}>
                        Retry Request
                      </Button>
                    )}
                  </div>
                ) : isEmpty ? (
                  <div className="flex flex-col items-center justify-center h-48 text-center px-4 space-y-3">
                    <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">{emptyMessage}</p>
                  </div>
                ) : (
                  children
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SlideOver;
