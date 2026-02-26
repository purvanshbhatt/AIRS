/**
 * Tooltip — lightweight, accessible tooltip component.
 *
 * Renders content on hover/focus in a positioned bubble.
 * Uses pure CSS — no external dependencies.
 */

import { ReactNode, useState, useRef, useEffect } from 'react';

type Placement = 'top' | 'bottom' | 'left' | 'right';

interface TooltipProps {
  /** Tooltip content (string or JSX) */
  content: ReactNode;
  /** Placement relative to trigger */
  placement?: Placement;
  /** Optional max-width in px */
  maxWidth?: number;
  children: ReactNode;
}

export function Tooltip({
  content,
  placement = 'top',
  maxWidth = 280,
  children,
}: TooltipProps) {
  const [visible, setVisible] = useState(false);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const show = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    setVisible(true);
  };
  const hide = () => {
    timeoutRef.current = setTimeout(() => setVisible(false), 120);
  };

  useEffect(() => () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  }, []);

  const placementClasses: Record<Placement, string> = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  };

  return (
    <span
      className="relative inline-flex"
      onMouseEnter={show}
      onMouseLeave={hide}
      onFocus={show}
      onBlur={hide}
    >
      {children}
      {visible && (
        <span
          role="tooltip"
          className={`
            absolute z-50 px-3 py-2 rounded-lg text-xs leading-relaxed font-normal
            bg-gray-900 dark:bg-slate-100 text-white dark:text-gray-900
            shadow-medium pointer-events-none animate-fade-up
            ${placementClasses[placement]}
          `}
          style={{ maxWidth, whiteSpace: 'normal' }}
        >
          {content}
        </span>
      )}
    </span>
  );
}
