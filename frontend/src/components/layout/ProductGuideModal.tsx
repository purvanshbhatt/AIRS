import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, ShieldCheck, Activity, PieChart, ShieldAlert } from 'lucide-react';

interface ProductGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProductGuideModal({ isOpen, onClose }: ProductGuideModalProps) {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    // Prevent background scrolling when modal is active
    document.body.style.overflow = 'hidden';

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen || typeof document === 'undefined') return null;

  return createPortal(
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 sm:p-6 bg-black/75 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
      aria-modal="true"
      role="dialog"
    >
      <div 
        className="bg-surface-container-low dark:bg-surface-container-low rounded-2xl max-w-4xl w-full max-h-[88vh] flex flex-col border border-outline-variant/40 shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-5 border-b border-outline-variant/30 flex justify-between items-center bg-surface-container dark:bg-surface-container shrink-0">
          <div>
            <h2 className="text-xl font-bold text-on-surface">ResilAI Product Guide</h2>
            <p className="text-xs text-on-surface-variant mt-0.5">
              Deterministic incident readiness for healthcare operations and executive decision-making.
            </p>
          </div>
          <button 
            onClick={onClose}
            className="p-2 hover:bg-surface-container-highest rounded-full text-on-surface-variant hover:text-on-surface transition-colors"
            aria-label="Close Product Guide"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        
        {/* Body Content */}
        <div className="p-6 md:p-8 space-y-10 overflow-y-auto flex-1 text-on-surface">
          {/* Section 1: What is ResilAI */}
          <section className="space-y-4">
            <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ready-emerald/10 text-ready-emerald flex items-center justify-center text-xs font-mono font-bold">1</span>
              What Is ResilAI?
            </h3>
            <div className="grid gap-4 md:grid-cols-2 text-sm text-on-surface-variant leading-relaxed">
              <div className="bg-surface-container p-5 rounded-xl border border-surface-bright">
                <h4 className="font-semibold text-on-surface mb-2">What ResilAI does:</h4>
                <p>ResilAI continuously checks whether the security protections your organization already relies on are actively operating and producing hard evidence. It connects to your existing tools (like Splunk, Microsoft 365, Veeam, and Wazuh) and mathematically verifies that they are protecting critical assets.</p>
              </div>
              <div className="bg-surface-container p-5 rounded-xl border border-surface-bright">
                <h4 className="font-semibold text-on-surface mb-2">What problem it solves:</h4>
                <p>Most ransomware attacks and data breaches occur not from lack of security software, but because tools were silently misconfigured, uninstalled, or disabled. ResilAI discovers these silent visibility and configuration gaps before adversaries exploit them.</p>
              </div>
            </div>
          </section>

          {/* Section 2: How it works */}
          <section className="space-y-4">
            <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ready-emerald/10 text-ready-emerald flex items-center justify-center text-xs font-mono font-bold">2</span>
              The Continuous Verification Loop
            </h3>
            <p className="text-xs text-on-surface-variant">ResilAI executes an automated 4-stage readiness cycle:</p>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
              <div className="flex flex-col items-center text-center p-4 bg-surface-container rounded-xl border border-surface-bright">
                <div className="w-10 h-10 bg-surface-bright rounded-full flex items-center justify-center mb-2.5">
                  <Activity className="w-5 h-5 text-on-surface" />
                </div>
                <h4 className="font-bold text-xs text-on-surface mb-1">1. CONNECT</h4>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">Connects to your existing security and telemetry sources.</p>
              </div>
              <div className="flex flex-col items-center text-center p-4 bg-surface-container rounded-xl border border-surface-bright">
                <div className="w-10 h-10 bg-surface-bright rounded-full flex items-center justify-center mb-2.5">
                  <ShieldCheck className="w-5 h-5 text-ready-emerald" />
                </div>
                <h4 className="font-bold text-xs text-on-surface mb-1">2. VERIFY</h4>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">Gathers SHA-256 evidence to confirm controls are operational.</p>
              </div>
              <div className="flex flex-col items-center text-center p-4 bg-surface-container rounded-xl border border-surface-bright">
                <div className="w-10 h-10 bg-surface-bright rounded-full flex items-center justify-center mb-2.5">
                  <PieChart className="w-5 h-5 text-blue-400" />
                </div>
                <h4 className="font-bold text-xs text-on-surface mb-1">3. UNDERSTAND</h4>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">Computes deterministic readiness scores across verified operational controls.</p>
              </div>
              <div className="flex flex-col items-center text-center p-4 bg-surface-container rounded-xl border border-surface-bright">
                <div className="w-10 h-10 bg-surface-bright rounded-full flex items-center justify-center mb-2.5">
                  <ShieldAlert className="w-5 h-5 text-amber-500" />
                </div>
                <h4 className="font-bold text-xs text-on-surface mb-1">4. ACT</h4>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">Provides clear instructions to resolve failing controls.</p>
              </div>
            </div>
          </section>

          {/* Section 3: Understanding the score */}
          <section className="space-y-4">
            <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ready-emerald/10 text-ready-emerald flex items-center justify-center text-xs font-mono font-bold">3</span>
              Understanding Your Readiness Score
            </h3>
            <div className="bg-surface-container p-5 rounded-xl border border-surface-bright space-y-3 text-sm text-on-surface-variant">
              <p>Your Readiness Score (0 to 100%) is a direct reflection of verified operational controls.</p>
              <div className="p-4 bg-ready-emerald/10 border border-ready-emerald/30 rounded-xl text-on-surface text-xs leading-relaxed">
                <strong className="text-ready-emerald font-semibold">The Non-Negotiable Contract:</strong> LLMs never calculate scores or modify findings. Scores are 100% mathematical and traceable. Missing telemetry yields <em>&ldquo;Unable to verify&rdquo;</em> (0% confidence).
              </div>
            </div>
          </section>

          {/* Section 4: Explain "Verified" */}
          <section className="space-y-4">
            <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
              <span className="w-6 h-6 rounded-full bg-ready-emerald/10 text-ready-emerald flex items-center justify-center text-xs font-mono font-bold">4</span>
              Telemetry Verification States
            </h3>
            <div className="grid sm:grid-cols-2 gap-3 text-xs">
              <div className="flex items-start gap-3 p-3 bg-surface-container rounded-xl border border-surface-bright">
                <ShieldCheck className="w-5 h-5 text-ready-emerald shrink-0 mt-0.5" />
                <div>
                  <strong className="text-on-surface block mb-0.5">Verified:</strong> 
                  <span className="text-on-surface-variant">Fresh cryptographic evidence confirms the control is actively working.</span>
                </div>
              </div>
              <div className="flex items-start gap-3 p-3 bg-surface-container rounded-xl border border-surface-bright">
                <ShieldAlert className="w-5 h-5 text-critical-red shrink-0 mt-0.5" />
                <div>
                  <strong className="text-on-surface block mb-0.5">Unable to Verify:</strong> 
                  <span className="text-on-surface-variant">No active telemetry feed is proving this protection. Score impact applies.</span>
                </div>
              </div>
            </div>
          </section>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-outline-variant/30 bg-surface-container dark:bg-surface-container flex justify-end shrink-0">
          <button
            onClick={onClose}
            className="px-5 py-2 bg-ready-emerald text-on-primary-container font-semibold rounded-xl text-xs hover:brightness-110 transition-all shadow-sm"
          >
            Got It
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
