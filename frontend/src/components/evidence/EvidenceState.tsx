import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Clock, Activity, HelpCircle, ShieldAlert } from 'lucide-react';
import { Badge } from '../ui';

export type EvidenceState = 
  | 'loading' 
  | 'verified' 
  | 'partially_verified' 
  | 'stale' 
  | 'degraded' 
  | 'no_evidence' 
  | 'unavailable';

export interface DataStateProps {
  state: EvidenceState;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

/**
 * DataState handles wrapping standard content and replacing it with loading or unavailable states
 * when the evidence cannot be trusted.
 */
export function DataState({ state, children, fallback }: DataStateProps) {
  if (state === 'loading') {
    return <div className="animate-pulse h-6 w-16 bg-surface-bright rounded"></div>;
  }
  if (state === 'no_evidence' || state === 'unavailable') {
    return <>{fallback || <UnavailableState />}</>;
  }
  // Even if stale or degraded, we might still show the data, but ideally wrapped with warnings.
  // The child components (like VerifiedValue) can style themselves based on the state.
  return <>{children}</>;
}

export function UnavailableState({ message = 'Evidence unavailable' }: { message?: string }) {
  return (
    <div className="flex items-center gap-1.5 text-surface-dim text-sm italic">
      <HelpCircle className="w-4 h-4 opacity-70" />
      <span>{message}</span>
    </div>
  );
}

interface VerifiedValueProps {
  value: React.ReactNode;
  state: EvidenceState;
  fallback?: React.ReactNode;
  className?: string;
}

/**
 * VerifiedValue is the core primitive preventing the `|| 98` anti-pattern.
 * If data is unavailable, no_evidence, or loading, it displays a strict placeholder.
 */
export function VerifiedValue({ value, state, fallback = '—', className = '' }: VerifiedValueProps) {
  if (state === 'loading') {
    return <span className={`animate-pulse h-[1em] w-8 bg-surface-bright rounded inline-block align-middle ${className}`}></span>;
  }
  
  if (state === 'unavailable' || state === 'no_evidence' || value === undefined || value === null) {
    return <span className={`text-surface-dim ${className}`}>{fallback}</span>;
  }

  // Visual cues for stale or degraded data
  if (state === 'stale' || state === 'degraded' || state === 'partially_verified') {
    return (
      <span className={`inline-flex items-center gap-1 text-drift-amber ${className}`}>
        <AlertTriangle className="w-[1em] h-[1em]" />
        {value}
      </span>
    );
  }

  return <span className={`text-on-surface ${className}`}>{value}</span>;
}

interface EvidenceFreshnessProps {
  timestamp: string | Date | undefined;
  state: EvidenceState;
}

/**
 * Displays when the evidence was last gathered, emphasizing the deterministic nature.
 */
export function EvidenceFreshness({ timestamp, state }: EvidenceFreshnessProps) {
  if (state === 'loading') {
    return <div className="animate-pulse h-4 w-24 bg-surface-bright rounded"></div>;
  }
  
  if (!timestamp || state === 'unavailable' || state === 'no_evidence') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-surface-dim">
        <Clock className="w-3.5 h-3.5" />
        <span>Freshness unknown</span>
      </div>
    );
  }

  // Calculate relative time (simplified for example, would normally use date-fns)
  let timeStr = typeof timestamp === 'string' ? timestamp : 'recently';
  
  // Format as relative if it's a date object
  if (timestamp instanceof Date) {
    const mins = Math.floor((new Date().getTime() - timestamp.getTime()) / 60000);
    if (mins < 1) timeStr = 'just now';
    else if (mins < 60) timeStr = `${mins} min${mins !== 1 ? 's' : ''} ago`;
    else if (mins < 1440) timeStr = `${Math.floor(mins/60)} hr${Math.floor(mins/60) !== 1 ? 's' : ''} ago`;
    else timeStr = `${Math.floor(mins/1440)} day${Math.floor(mins/1440) !== 1 ? 's' : ''} ago`;
  }

  const isStale = state === 'stale';

  return (
    <div className={`flex items-center gap-1.5 text-xs ${isStale ? 'text-drift-amber font-medium' : 'text-surface-dim'}`}>
      <Clock className="w-3.5 h-3.5" />
      <span>{isStale ? 'Stale evidence: ' : 'Last verified: '}{timeStr}</span>
    </div>
  );
}

interface ConnectorStatusProps {
  name: string;
  state: EvidenceState;
  showIcon?: boolean;
}

/**
 * Standardizes the display of integration/connector health.
 */
export function ConnectorStatus({ name, state, showIcon = true }: ConnectorStatusProps) {
  if (state === 'loading') {
    return <Badge variant="outline" className="animate-pulse w-24 h-5"></Badge>;
  }

  const getVariant = () => {
    switch (state) {
      case 'verified': return 'ready';
      case 'partially_verified': 
      case 'stale':
      case 'degraded': return 'drift';
      case 'unavailable': 
      case 'no_evidence': return 'critical';
      default: return 'outline';
    }
  };

  const getIcon = () => {
    if (!showIcon) return null;
    switch (state) {
      case 'verified': return <CheckCircle2 className="w-3 h-3 mr-1" />;
      case 'partially_verified':
      case 'stale':
      case 'degraded': return <AlertTriangle className="w-3 h-3 mr-1" />;
      case 'unavailable':
      case 'no_evidence': return <XCircle className="w-3 h-3 mr-1" />;
      default: return null;
    }
  };

  const getLabel = () => {
    switch (state) {
      case 'verified': return 'Connected';
      case 'partially_verified': return 'Partial';
      case 'stale': return 'Stale';
      case 'degraded': return 'Degraded';
      case 'unavailable': return 'Unavailable';
      case 'no_evidence': return 'Disconnected';
      default: return 'Unknown';
    }
  };

  return (
    <Badge variant={getVariant()} className="inline-flex items-center font-medium">
      {getIcon()}
      {name}: {getLabel()}
    </Badge>
  );
}
