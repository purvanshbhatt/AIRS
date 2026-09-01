import React, { useState } from 'react';
import {
  KeyRound,
  HardDrive,
  ShieldCheck,
  ShieldAlert,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Sparkles,
  ExternalLink,
  ChevronRight,
  Plus,
  ArrowRight,
  ArrowLeft,
  Lock,
  Activity,
  Check,
} from 'lucide-react';
import type { SecurityConnectorState, OnboardingMode } from '../../types/onboarding';

interface Step2ConnectorsProps {
  connectors: SecurityConnectorState[];
  onUpdateConnector: (connectorId: string, updated: Partial<SecurityConnectorState>) => void;
  mode: OnboardingMode;
  onNext: () => void;
  onPrev: () => void;
}

export function Step2Connectors({
  connectors,
  onUpdateConnector,
  mode,
  onNext,
  onPrev,
}: Step2ConnectorsProps) {
  const isDemo = mode === 'demo';
  const [activeConfigId, setActiveConfigId] = useState<string | null>(null);
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; success: boolean; message: string } | null>(null);

  const getConnectorIcon = (iconName: string) => {
    switch (iconName) {
      case 'KeyRound':
        return KeyRound;
      case 'HardDrive':
        return HardDrive;
      case 'ShieldCheck':
        return ShieldCheck;
      case 'ShieldAlert':
        return ShieldAlert;
      default:
        return Activity;
    }
  };

  const handleTestConnection = (connector: SecurityConnectorState) => {
    setTestingId(connector.id);
    setTestResult(null);
    setTimeout(() => {
      setTestingId(null);
      setTestResult({
        id: connector.id,
        success: true,
        message: `Successfully established secure TLS handshake with ${connector.name}. Telemetry stream active.`,
      });
      onUpdateConnector(connector.id, {
        status: 'connected',
        lastSync: 'Just now',
      });
    }, 900);
  };

  const connectedCount = connectors.filter((c) => c.status === 'connected').length;

  return (
    <div className="space-y-8 animate-in fade-in duration-300">
      {/* Top Banner */}
      <div className="bg-surface-container p-5 rounded-2xl border border-outline-variant/50 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
            <RefreshCw className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-on-surface">
              {isDemo ? 'Live Security Connectors (Acme Health Systems Telemetry)' : 'Connect Your Security Platforms'}
            </h3>
            <p className="text-xs text-on-surface-variant mt-0.5 max-w-2xl leading-relaxed">
              ResilAI hooks directly into Microsoft 365, Veeam, CrowdStrike, and SentinelOne via read-only APIs and MCP forwarders to continuously harvest control evidence.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs font-mono font-bold px-3 py-1.5 rounded-xl bg-surface-container-high border border-outline-variant/50 text-on-surface">
            {connectedCount} of {connectors.length} Connected
          </span>
        </div>
      </div>

      {/* Grid of 4 Primary Connectors */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {connectors.map((conn) => {
          const Icon = getConnectorIcon(conn.iconName);
          const isConnected = conn.status === 'connected';
          const isConfiguring = activeConfigId === conn.id;
          const isTesting = testingId === conn.id;

          return (
            <div
              key={conn.id}
              className={`p-5 rounded-2xl border transition-all flex flex-col justify-between ${
                isConnected
                  ? 'bg-surface-container border-ready-emerald/30 shadow-md shadow-ready-emerald/5'
                  : 'bg-surface-container-low border-outline-variant/40 hover:border-outline-variant'
              }`}
            >
              <div>
                {/* Card Header */}
                <div className="flex items-start justify-between gap-3 mb-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center border ${
                      isConnected
                        ? 'bg-ready-emerald/15 text-ready-emerald border-ready-emerald/30'
                        : 'bg-surface-container-high text-on-surface-variant border-outline-variant/40'
                    }`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-[10px] font-mono uppercase tracking-wider text-ready-emerald font-semibold block">
                        {conn.category}
                      </span>
                      <h4 className="text-sm font-bold text-on-surface">
                        {conn.name}
                      </h4>
                    </div>
                  </div>

                  {/* Status Badge */}
                  {isConnected ? (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30 flex items-center gap-1.5 shrink-0">
                      <span className="w-1.5 h-1.5 rounded-full bg-ready-emerald animate-pulse" />
                      Connected
                    </span>
                  ) : (
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-mono font-bold uppercase bg-surface-container-high text-on-surface-variant border border-outline-variant/40 shrink-0">
                      Ready to Link
                    </span>
                  )}
                </div>

                <p className="text-xs text-on-surface-variant leading-relaxed mb-4">
                  {conn.description}
                </p>

                {/* Verified Controls List */}
                <div className="space-y-1.5 mb-4">
                  <span className="text-[10px] font-mono uppercase text-on-surface-variant font-bold block">
                    Mathematically Verifies:
                  </span>
                  {conn.verifiedControls.map((ctrl, idx) => (
                    <div key={idx} className="flex items-center gap-2 text-xs text-on-surface">
                      <CheckCircle2 className="w-3.5 h-3.5 text-ready-emerald shrink-0" />
                      <span className="truncate">{ctrl}</span>
                    </div>
                  ))}
                </div>

                {/* Simulated Telemetry Metrics (Demo Mode) */}
                {isDemo && conn.simulatedTelemetry && (
                  <div className="p-3 bg-surface-container-lowest/80 rounded-xl border border-outline-variant/40 space-y-1.5 mb-3 text-[11px]">
                    <div className="flex items-center justify-between text-on-surface-variant">
                      <span>Monitored Objects:</span>
                      <strong className="text-on-surface font-mono">{conn.simulatedTelemetry.endpointCount} endpoints</strong>
                    </div>
                    <div className="flex items-center justify-between text-on-surface-variant">
                      <span>Telemetry Heartbeat:</span>
                      <strong className="text-ready-emerald font-mono">{conn.simulatedTelemetry.lastHeartbeat}</strong>
                    </div>
                    <div className="flex items-center justify-between text-on-surface-variant">
                      <span>Evidence SHA-256:</span>
                      <span className="font-mono text-ready-emerald truncate max-w-[160px]" title={conn.simulatedTelemetry.evidenceHash}>
                        {conn.simulatedTelemetry.evidenceHash.substring(0, 16)}...
                      </span>
                    </div>
                  </div>
                )}

                {/* Inline Real Org Configuration Drawer */}
                {!isDemo && isConfiguring && (
                  <div className="mt-4 p-4 bg-surface-container-lowest rounded-xl border border-ready-emerald/30 space-y-3 animate-in fade-in duration-200">
                    <h5 className="text-xs font-bold text-on-surface uppercase tracking-wider">
                      Configure Credentials for {conn.name}
                    </h5>
                    {conn.configFields.map((field) => (
                      <div key={field.key}>
                        <label className="block text-[11px] font-semibold text-on-surface-variant mb-1">
                          {field.label}
                        </label>
                        <input
                          type={field.type || 'text'}
                          placeholder={field.placeholder}
                          defaultValue={field.defaultValue || ''}
                          className="w-full px-3 py-2 bg-surface-container text-xs text-on-surface rounded-lg border border-outline-variant/50 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald"
                        />
                      </div>
                    ))}

                    {testResult && testResult.id === conn.id && (
                      <div className="p-2.5 bg-ready-emerald/10 border border-ready-emerald/30 rounded-lg text-ready-emerald text-xs flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 shrink-0" />
                        <span>{testResult.message}</span>
                      </div>
                    )}

                    <div className="flex items-center justify-end gap-2 pt-2">
                      <button
                        type="button"
                        onClick={() => setActiveConfigId(null)}
                        className="px-3 py-1.5 text-xs text-on-surface-variant hover:text-on-surface"
                      >
                        Cancel
                      </button>
                      <button
                        type="button"
                        onClick={() => handleTestConnection(conn)}
                        disabled={isTesting}
                        className="px-4 py-2 bg-ready-emerald text-slate-950 font-bold text-xs rounded-lg hover:brightness-110 flex items-center gap-1.5"
                      >
                        {isTesting ? (
                          <>
                            <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                            <span>Verifying API Handshake...</span>
                          </>
                        ) : (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Save & Test Connection</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Card Bottom Actions */}
              <div className="pt-4 mt-2 border-t border-outline-variant/30 flex items-center justify-between">
                <span className="text-[11px] text-on-surface-variant">
                  {isConnected ? `Verified ${conn.lastSync || '4m ago'}` : 'Requires API Read Scope'}
                </span>

                {!isDemo && (
                  <button
                    type="button"
                    onClick={() => setActiveConfigId(isConfiguring ? null : conn.id)}
                    className="text-xs font-semibold px-3 py-1.5 rounded-lg border border-outline-variant/60 hover:bg-surface-container-high text-on-surface transition-all flex items-center gap-1"
                  >
                    {isConnected ? 'Reconfigure' : 'Connect Now'}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Navigation Footer */}
      <div className="pt-4 border-t border-outline-variant/30 flex items-center justify-between">
        <button
          type="button"
          onClick={onPrev}
          className="px-5 py-2.5 rounded-xl border border-outline-variant/60 text-on-surface-variant hover:text-on-surface hover:bg-surface-container font-semibold text-xs transition-all flex items-center gap-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Profile</span>
        </button>

        <button
          type="button"
          onClick={onNext}
          className="px-6 py-3 bg-ready-emerald text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center gap-2"
        >
          <span>Continue to Step 3: See What Can Be Verified</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
