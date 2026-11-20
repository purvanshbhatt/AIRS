import React, { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { X, ShieldCheck } from 'lucide-react';

export interface VideoModalProps {
  isOpen: boolean;
  onClose: () => void;
  videoSrc: string;
  posterSrc?: string;
  title?: string;
  caption?: string;
}

export const VideoModal: React.FC<VideoModalProps> = ({
  isOpen,
  onClose,
  videoSrc,
  posterSrc,
  title = "ResilAI Product Video",
  caption = "Sample data. The practice, accounts and answers shown are examples, not a customer.",
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const closeButtonRef = useRef<HTMLButtonElement | null>(null);

  // Keyboard navigation (Escape key) and body scroll locking
  useEffect(() => {
    if (!isOpen) return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    // Auto-focus close button or video player on open
    const timer = setTimeout(() => {
      closeButtonRef.current?.focus();
      if (videoRef.current) {
        videoRef.current.play().catch(() => {
          // Autoplay policy fallback: video remains ready for user click
        });
      }
    }, 50);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
      clearTimeout(timer);
    };
  }, [isOpen, onClose]);

  // Pause and reset video playback when modal closes
  useEffect(() => {
    if (!isOpen && videoRef.current) {
      videoRef.current.pause();
      videoRef.current.currentTime = 0;
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const modalContent = (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="video-modal-title"
      aria-describedby="video-modal-description"
      data-testid="video-modal"
    >
      {/* High-fidelity obsidian backdrop */}
      <div
        className="fixed inset-0 bg-slate-950/85 backdrop-blur-md transition-opacity"
        onClick={onClose}
        aria-hidden="true"
        data-testid="video-modal-backdrop"
      />

      {/* Modal Dialog Card */}
      <div className="relative w-full max-w-4xl rounded-2xl bg-[#090D16] border border-slate-800 shadow-2xl overflow-hidden z-10 transition-all transform duration-200">
        
        {/* Header Bar */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-800/80 bg-slate-900/60">
          <div className="flex items-center gap-3">
            <span className="flex h-6 w-6 items-center justify-center rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <ShieldCheck className="h-3.5 w-3.5" />
            </span>
            <div>
              <h3 id="video-modal-title" className="text-sm sm:text-base font-bold text-white tracking-tight flex items-center gap-2">
                <span>{title}</span>
                <span className="text-[10px] font-mono font-semibold px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 uppercase">
                  0:20 · Sample data
                </span>
              </h3>
            </div>
          </div>

          <button
            ref={closeButtonRef}
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500"
            aria-label="Close video modal"
            data-testid="video-modal-close"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Video Player Canvas */}
        <div className="relative bg-black aspect-video w-full flex items-center justify-center">
          <video
            ref={videoRef}
            src={videoSrc}
            poster={posterSrc}
            controls
            playsInline
            preload="auto"
            className="w-full h-full object-contain"
            data-testid="video-modal-player"
          >
            Your browser does not support high-definition HTML5 video playback.
          </video>
        </div>

        {/* Honest Copy & Governance Caption Footer */}
        <div className="px-5 py-3.5 bg-slate-900/90 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 text-xs">
          <p id="video-modal-description" data-testid="video-modal-description" className="text-slate-400 leading-relaxed font-normal">
            <span className="font-semibold text-slate-300">Note:</span> {caption}
          </p>
          <div className="flex items-center gap-2 text-[11px] font-mono text-slate-400 shrink-0">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            <span>Deterministic Scoring Engine</span>
          </div>
        </div>

      </div>
    </div>
  );

  // Render via portal when available, otherwise direct render
  return typeof document !== 'undefined' ? createPortal(modalContent, document.body) : modalContent;
};

export default VideoModal;
