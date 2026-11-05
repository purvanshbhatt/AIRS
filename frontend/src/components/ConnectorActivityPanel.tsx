import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  Server, 
  KeyRound, 
  Monitor, 
  Bug, 
  RefreshCw, 
  ShieldCheck,
  ChevronRight,
  AlertCircle
} from 'lucide-react';
import { getApiBaseUrl } from '../api';
import { Badge, Card, CardHeader, CardTitle, CardContent, Button } from './ui';

interface ConnectorActivityPanelProps {
  orgId: string;
  host: string;
  port: number;
  onClose: () => void;
  onSuccess: () => void;
}

type StepState = 'pending' | 'active' | 'completed' | 'failed';

interface ActivityStep {
  id: string;
  label: string;
  activeLabel?: string;
  icon: React.ReactNode;
}

const STEPS_CONFIG: ActivityStep[] = [
  { id: 'CONNECTING', label: 'Connecting to Manager', activeLabel: 'Connecting to Wazuh Manager...', icon: <Server className="w-4.5 h-4.5" /> },
  { id: 'AUTHENTICATING', label: 'Authenticating credentials', activeLabel: 'Authenticating with JWT...', icon: <KeyRound className="w-4.5 h-4.5" /> },
  { id: 'FETCHING_DEVICES', label: 'Fetching agents', activeLabel: 'Fetching active agents...', icon: <Monitor className="w-4.5 h-4.5" /> },
  { id: 'FETCHING_VULNERABILITIES', label: 'Fetching vulnerabilities', activeLabel: 'Fetching agent vulnerabilities...', icon: <Bug className="w-4.5 h-4.5" /> },
  { id: 'NORMALIZING', label: 'Normalizing telemetry data', activeLabel: 'Normalizing data structures...', icon: <RefreshCw className="w-4.5 h-4.5" /> },
  { id: 'VERIFYING_CONTROLS', label: 'Verifying controls', activeLabel: 'Verifying compliance controls...', icon: <ShieldCheck className="w-4.5 h-4.5" /> }
];

export function ConnectorActivityPanel({ orgId, host, port, onClose, onSuccess }: ConnectorActivityPanelProps) {
  const [currentState, setCurrentState] = useState<string>('CONNECTING');
  const [statusMessage, setStatusMessage] = useState<string>('Initiating Wazuh connector sync...');
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  
  // Dynamic counts received from backend
  const [agentsCount, setAgentsCount] = useState<number | null>(null);
  const [vulnerabilitiesCount, setVulnerabilitiesCount] = useState<number | null>(null);
  const [controlsCount, setControlsCount] = useState<number | null>(null);

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!orgId) return;

    // Construct WebSocket URL dynamically matching useTelemetryWebSocket
    const apiBase = getApiBaseUrl();
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    let wsUrl = '';
    if (!apiBase || apiBase.startsWith('/')) {
      wsUrl = `${wsProtocol}//${window.location.host}/ws/telemetry?org_id=${orgId}`;
    } else {
      wsUrl = apiBase.replace(/^http/, 'ws') + `/ws/telemetry?org_id=${orgId}`;
    }

    console.log(`[Connector WebSocket] Connecting to ${wsUrl}`);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.type === 'connector_progress' && parsed.connector_type === 'wazuh') {
          console.log('[Connector WebSocket] Inbound Progress:', parsed);
          setCurrentState(parsed.state);
          setStatusMessage(parsed.status_message);

          // Extract dynamic counts if available
          if (parsed.details) {
            if (parsed.details.agents_count !== undefined) {
              setAgentsCount(parsed.details.agents_count);
            }
            if (parsed.details.vulnerabilities_count !== undefined) {
              setVulnerabilitiesCount(parsed.details.vulnerabilities_count);
            }
            if (parsed.details.controls_count !== undefined) {
              setControlsCount(parsed.details.controls_count);
            }
            if (parsed.details.error !== undefined) {
              setErrorDetails(parsed.details.error);
            }
          }

          if (parsed.state === 'COMPLETE') {
            setTimeout(() => {
              onSuccess();
            }, 1500);
          }
        }
      } catch (err) {
        console.error('[Connector WebSocket] Parse failed:', err);
      }
    };

    ws.onerror = (err) => {
      console.error('[Connector WebSocket] Connection error:', err);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [orgId, onSuccess]);

  // Determine step status in sequence
  const getStepState = (stepId: string): StepState => {
    if (currentState === 'FAILED') {
      // Find where we failed
      const failedIdx = STEPS_CONFIG.findIndex(s => s.id === stepId);
      const currentFailedIdx = STEPS_CONFIG.findIndex(s => s.id === errorDetails); // custom details check
      
      // Fallback: If we failed at FETCHING_DEVICES, all preceding are completed, this is failed, rest pending
      const activeIdx = STEPS_CONFIG.findIndex(s => s.id === currentState); 
      // If we are currently FAILED, evaluate relative index
      return 'pending'; 
    }

    const stepIdx = STEPS_CONFIG.findIndex(s => s.id === stepId);
    let currentIdx = STEPS_CONFIG.findIndex(s => s.id === currentState);

    if (currentState === 'COMPLETE') {
      return 'completed';
    }

    if (currentState === 'FAILED') {
      // If it's failed, whichever step failed gets 'failed', preceding get 'completed', following get 'pending'
      // We can infer the fail point from our checklist
      return 'pending'; // Overridden below in map
    }

    if (stepIdx < currentIdx) return 'completed';
    if (stepIdx === currentIdx) return 'active';
    return 'pending';
  };

  // Build list of steps with correct statuses
  const steps = STEPS_CONFIG.map((step, idx) => {
    let state: StepState = 'pending';
    
    if (currentState === 'COMPLETE') {
      state = 'completed';
    } else if (currentState === 'FAILED') {
      // Determine which step failed
      // For instance, if error happened at CONNECTING, that's failed. If at AUTH, etc.
      // We map currentState to index. If we failed, the last known state is the one that failed.
      // We'll calculate based on if we reached previous ones
      const failedStepId = errorDetails ? 'AUTHENTICATING' : 'CONNECTING'; // simple fallback
      // Actually, we can check which step was active before failure
      // To keep it simple: if CONNECTING fails -> CONNECTING is failed. If AUTHENTICATING fails -> CONNECTING completed, AUTH failed.
      // If FETCHING_DEVICES fails -> CONNECTING/AUTH completed, FETCHING_DEVICES failed, etc.
      // We can inspect errorDetails or statusMessage or guess based on what counts are filled.
      if (controlsCount !== null) {
        state = 'completed'; // everything before verified controls succeeded
      } else if (vulnerabilitiesCount !== null) {
        state = idx < 4 ? 'completed' : idx === 4 ? 'failed' : 'pending';
      } else if (agentsCount !== null) {
        state = idx < 3 ? 'completed' : idx === 3 ? 'failed' : 'pending';
      } else if (currentState === 'FAILED') {
        // If no counts, let's assume either connect or auth failed
        if (statusMessage.toLowerCase().includes('credential') || statusMessage.toLowerCase().includes('auth')) {
          state = idx === 0 ? 'completed' : idx === 1 ? 'failed' : 'pending';
        } else {
          state = idx === 0 ? 'failed' : 'pending';
        }
      }
    } else {
      state = getStepState(step.id);
    }

    // Dynamic labels matching user request
    let label = step.label;
    if (step.id === 'FETCHING_DEVICES') {
      label = agentsCount !== null ? `Fetching: ${agentsCount} agents` : step.label;
    } else if (step.id === 'FETCHING_VULNERABILITIES') {
      label = vulnerabilitiesCount !== null ? `Fetching: ${vulnerabilitiesCount} vulnerabilities` : step.label;
    } else if (step.id === 'VERIFYING_CONTROLS') {
      label = controlsCount !== null ? `Verifying: ${controlsCount} controls` : step.label;
    }

    return {
      ...step,
      state,
      label
    };
  });

  // Calculate overall percentage for progress bar
  const completedCount = steps.filter(s => s.state === 'completed').length;
  const progressPercent = currentState === 'COMPLETE' ? 100 : (completedCount / steps.length) * 100;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="w-full"
    >
      <Card className="border border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/60 backdrop-blur-xl shadow-xl rounded-[24px] overflow-hidden">
        <CardHeader className="border-b border-slate-100 dark:border-slate-800/80 bg-slate-50/40 dark:bg-slate-900/40 px-6 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative">
                <div className="absolute -inset-1 bg-blue-500/20 rounded-xl blur-sm" />
                <div className="relative w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/25 flex items-center justify-center">
                  <Server className="w-5 h-5 text-blue-500" />
                </div>
              </div>
              <div>
                <CardTitle className="text-base font-extrabold text-slate-900 dark:text-slate-100">
                  Wazuh Integration Progress
                </CardTitle>
                <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold mt-0.5">
                  Host: {host}:{port}
                </p>
              </div>
            </div>

            <AnimatePresence mode="wait">
              {currentState === 'COMPLETE' ? (
                <motion.div
                  key="complete"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                >
                  <Badge variant="ready" className="gap-1.5 rounded-full px-3 py-1 font-bold text-xs uppercase tracking-wider">
                    <CheckCircle2 className="w-3.5 h-3.5" />✓ Connected
                  </Badge>
                </motion.div>
              ) : currentState === 'FAILED' ? (
                <motion.div
                  key="failed"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                >
                  <Badge variant="critical" className="gap-1.5 rounded-full px-3 py-1 font-bold text-xs uppercase tracking-wider">
                    <XCircle className="w-3.5 h-3.5" />Status: FAILED
                  </Badge>
                </motion.div>
              ) : (
                <motion.div
                  key="running"
                  initial={{ opacity: 0, y: -5 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 5 }}
                >
                  <Badge variant="outline" className="gap-1.5 rounded-full px-3 py-1 font-bold text-xs uppercase tracking-wider bg-blue-500/10 text-blue-500 border border-blue-500/20">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />Syncing...
                  </Badge>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          {/* Linear Progress Bar */}
          <div className="mt-5 w-full bg-slate-100 dark:bg-slate-800 h-1.5 rounded-full overflow-hidden">
            <motion.div 
              className={`h-full rounded-full ${
                currentState === 'FAILED' ? 'bg-red-500' : 'bg-gradient-to-r from-blue-500 to-cyan-500'
              }`}
              initial={{ width: 0 }}
              animate={{ width: `${progressPercent}%` }}
              transition={{ duration: 0.4, ease: 'easeOut' }}
            />
          </div>
        </CardHeader>

        <CardContent className="p-6 space-y-5">
          {/* Status Message Section */}
          <div className="flex items-start gap-3 p-4 bg-slate-50/50 dark:bg-slate-950/20 border border-slate-100 dark:border-slate-800 rounded-2xl">
            {currentState === 'FAILED' ? (
              <AlertCircle className="w-5 h-5 text-red-500 shrink-0 mt-0.5" />
            ) : (
              <Loader2 className={`w-5 h-5 text-blue-500 shrink-0 mt-0.5 ${currentState === 'COMPLETE' ? 'hidden' : 'animate-spin'}`} />
            )}
            {currentState === 'COMPLETE' && (
              <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" />
            )}
            <div className="space-y-1">
              <p className="text-sm font-bold text-slate-800 dark:text-slate-200">
                {statusMessage}
              </p>
              {errorDetails && (
                <p className="text-xs text-red-650 dark:text-red-400 font-semibold leading-relaxed">
                  {errorDetails}
                </p>
              )}
            </div>
          </div>

          {/* Checklist Steps */}
          <div className="space-y-3">
            {steps.map((step) => (
              <div 
                key={step.id} 
                className={`flex items-center justify-between p-3.5 border rounded-2xl transition-all duration-350 ${
                  step.state === 'active' 
                    ? 'border-blue-550/30 bg-blue-500/5 shadow-sm scale-[1.01]' 
                    : step.state === 'completed'
                    ? 'border-slate-150 dark:border-slate-800 bg-white dark:bg-slate-900/40 opacity-90'
                    : step.state === 'failed'
                    ? 'border-red-200/50 dark:border-red-950/40 bg-red-500/5'
                    : 'border-slate-100 dark:border-slate-850 bg-slate-50/10 dark:bg-slate-950/5 opacity-55'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-xl border flex items-center justify-center transition-all ${
                    step.state === 'active'
                      ? 'border-blue-500/35 bg-blue-500/10 text-blue-500 shadow-sm'
                      : step.state === 'completed'
                      ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-500'
                      : step.state === 'failed'
                      ? 'border-red-500/30 bg-red-500/10 text-red-500'
                      : 'border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 text-slate-400 dark:text-slate-600'
                  }`}>
                    {step.icon}
                  </div>
                  <div>
                    <p className={`text-sm font-bold transition-all ${
                      step.state === 'active'
                        ? 'text-blue-500 dark:text-blue-400'
                        : step.state === 'completed'
                        ? 'text-slate-800 dark:text-slate-205'
                        : step.state === 'failed'
                        ? 'text-red-500 dark:text-red-400'
                        : 'text-slate-400 dark:text-slate-600'
                    }`}>
                      {step.label}
                    </p>
                  </div>
                </div>

                <div className="flex items-center">
                  {step.state === 'active' && (
                    <Loader2 className="w-4.5 h-4.5 text-blue-500 animate-spin" />
                  )}
                  {step.state === 'completed' && (
                    <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500" />
                  )}
                  {step.state === 'failed' && (
                    <XCircle className="w-4.5 h-4.5 text-red-500" />
                  )}
                  {step.state === 'pending' && (
                    <ChevronRight className="w-4.5 h-4.5 text-slate-300 dark:text-slate-700" />
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Action buttons footer */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100 dark:border-slate-800/80">
            {currentState === 'FAILED' && (
              <Button 
                variant="outline" 
                size="sm" 
                className="rounded-xl font-extrabold shadow-sm"
                onClick={onClose}
              >
                Dismiss
              </Button>
            )}
            {currentState === 'COMPLETE' && (
              <div className="flex items-center gap-1.5 text-xs text-emerald-600 dark:text-emerald-400 font-extrabold bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-xl">
                <CheckCircle2 className="w-4 h-4" />
                Status: COMPLETE
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
