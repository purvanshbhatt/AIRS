import { useEffect, useState } from 'react';
import { getDailyReadinessReport, getIntegrationStatus } from '../api';
import { useActiveOrgId } from '../hooks/useActiveOrgId';

interface SystemEvent {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERR' | 'FATAL';
  source: string;
  message: string;
}

export default function ITWorkspacePage() {
  const orgId = useActiveOrgId();
  const [loading, setLoading] = useState(true);
  const [report, setReport] = useState<any>(null);
  const [logFilter, setLogFilter] = useState<'ALL' | 'ERRORS'>('ALL');

  const systemEvents: SystemEvent[] = [
    { timestamp: '14:02:11.432', level: 'ERR', source: 'auth_svc', message: 'Failed authentication attempt from IP 192.168.1.104 - Invalid signature' },
    { timestamp: '14:02:10.112', level: 'WARN', source: 'db_sync', message: 'High latency detected on replica region-us-east-1 (420ms)' },
    { timestamp: '14:02:08.005', level: 'INFO', source: 'node_mgr', message: 'Node wkr-04 successfully re-registered to cluster' },
    { timestamp: '14:02:05.991', level: 'FATAL', source: 'policy_enf', message: 'Policy violation: Unauthorized lateral movement attempt detected source=wkr-02 dest=db-master' },
    { timestamp: '14:02:01.220', level: 'INFO', source: 'sys_mon', message: 'Routine memory garbage collection completed (freed 4.2GB)' },
    { timestamp: '14:01:55.801', level: 'INFO', source: 'wazuh_agent', message: 'Wazuh active response sweep completed on 14 endpoints' },
    { timestamp: '14:01:48.330', level: 'INFO', source: 'splunk_mcp', message: 'Splunk MCP query search execution: 4 searches returned 0 critical findings' },
  ];

  useEffect(() => {
    async function loadWorkspace() {
      try {
        const [rep] = await Promise.all([
          getDailyReadinessReport(orgId),
          getIntegrationStatus(orgId),
        ]);
        setReport(rep);
      } catch (err) {
        console.error('Failed to load IT workspace telemetry:', err);
      } finally {
        setLoading(false);
      }
    }
    loadWorkspace();
  }, [orgId]);

  const filteredEvents = logFilter === 'ERRORS' 
    ? systemEvents.filter(e => e.level === 'ERR' || e.level === 'FATAL')
    : systemEvents;

  return (
    <div className="space-y-8 animate-fade-up">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-outline-variant/40 pb-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight mb-2">IT Workspace & Telemetry</h1>
          <p className="text-base text-on-surface-variant max-w-2xl">
            Deep-dive technical workspace for IT administrators and MSPs. Real-time system logs, forensic snapshots, and network topology.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={() => alert('Exporting PCAP telemetry stream...')}
            className="px-4 py-2 bg-surface-container-high border border-outline-variant/50 text-on-surface hover:text-ready-emerald text-xs font-mono rounded-lg transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm" data-icon="download">
              download
            </span>
            Export Telemetry PCAP
          </button>
        </div>
      </div>

      {/* Top Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
        <div className="bg-surface-container-low border border-surface-bright rounded-xl p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-on-surface-variant uppercase tracking-wider block mb-1">Ingress Rate</span>
            <span className="text-3xl font-bold text-on-surface font-mono">42.8 <span className="text-sm text-ready-emerald">MB/s</span></span>
          </div>
          <span className="material-symbols-outlined text-ready-emerald text-3xl" data-icon="swap_calls">
            swap_calls
          </span>
        </div>

        <div className="bg-surface-container-low border border-surface-bright rounded-xl p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-on-surface-variant uppercase tracking-wider block mb-1">Active Blocks</span>
            <span className="text-3xl font-bold text-on-surface font-mono">1,204</span>
          </div>
          <span className="material-symbols-outlined text-critical-red text-3xl" data-icon="shield_locked">
            shield_locked
          </span>
        </div>

        <div className="bg-surface-container-low border border-surface-bright rounded-xl p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-mono text-on-surface-variant uppercase tracking-wider block mb-1">EDR Endpoints</span>
            <span className="text-3xl font-bold text-ready-emerald font-mono">14/14</span>
          </div>
          <span className="material-symbols-outlined text-ready-emerald text-3xl" data-icon="computer">
            computer
          </span>
        </div>
      </div>

      {/* Bottom Grid: Live System Events & Forensic Snapshots */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Live System Events (Span 7) */}
        <div className="lg:col-span-7 bg-surface-container-low border border-surface-bright rounded-xl flex flex-col overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-bright flex justify-between items-center bg-surface-container">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-ready-emerald text-lg" data-icon="list_alt">
                list_alt
              </span>
              <h3 className="text-sm font-semibold text-on-surface">Live System Telemetry Stream</h3>
            </div>
            <div className="flex gap-2">
              <button 
                onClick={() => setLogFilter(logFilter === 'ALL' ? 'ERRORS' : 'ALL')}
                className={`px-2.5 py-1 rounded text-xs font-mono border transition-all ${logFilter === 'ERRORS' ? 'bg-critical-red/20 text-critical-red border-critical-red/40' : 'bg-surface-container-high text-on-surface-variant border-outline-variant/40'}`}
              >
                {logFilter === 'ERRORS' ? 'ERRORS ONLY' : 'ALL LOGS'}
              </button>
            </div>
          </div>

          <div className="p-4 font-mono text-xs space-y-2 overflow-y-auto max-h-[400px]">
            {filteredEvents.map((evt, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded bg-surface-container/50 hover:bg-surface-container transition-colors">
                <span className="text-on-surface-variant shrink-0">{evt.timestamp}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold shrink-0 ${
                  evt.level === 'FATAL' || evt.level === 'ERR' ? 'bg-critical-red/20 text-critical-red border border-critical-red/40' :
                  evt.level === 'WARN' ? 'bg-drift-amber/20 text-drift-amber border border-drift-amber/40' :
                  'bg-ready-emerald/20 text-ready-emerald border border-ready-emerald/40'
                }`}>
                  [{evt.level}]
                </span>
                <span className="text-ready-emerald font-semibold shrink-0">{evt.source}</span>
                <span className="text-on-surface truncate">{evt.message}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Forensic Snapshots (Span 5) */}
        <div className="lg:col-span-5 bg-surface-container-low border border-surface-bright rounded-xl flex flex-col overflow-hidden">
          <div className="px-5 py-3 border-b border-surface-bright flex justify-between items-center bg-surface-container">
            <div className="flex items-center gap-2">
              <span className="material-symbols-outlined text-ready-emerald text-lg" data-icon="shield_with_heart">
                shield_with_heart
              </span>
              <h3 className="text-sm font-semibold text-on-surface">Forensic Snapshots</h3>
            </div>
          </div>

          <div className="p-4 space-y-3">
            <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-ready-emerald font-bold block mb-0.5">SNP-992-A</span>
                <span className="text-xs text-on-surface-variant">Policy Breach Sweep Snapshot</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-critical-red/10 text-critical-red border border-critical-red/30">
                Breach Audit
              </span>
            </div>

            <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-ready-emerald font-bold block mb-0.5">SNP-991-B</span>
                <span className="text-xs text-on-surface-variant">Routine Overnight Ledger Snapshot</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30">
                Verified
              </span>
            </div>

            <div className="p-4 rounded-lg bg-surface-container border border-outline-variant/30 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-ready-emerald font-bold block mb-0.5">SNP-990-C</span>
                <span className="text-xs text-on-surface-variant">Wazuh EDR Endpoint Telemetry Snapshot</span>
              </div>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono uppercase bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30">
                Verified
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
