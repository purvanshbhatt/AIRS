import { useState } from 'react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer 
} from 'recharts';
import { 
  Clock, 
  Copy, 
  Check, 
  Terminal, 
  TrendingUp,
  Activity, 
  ArrowRight,
  ExternalLink
} from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Badge, Button } from '../ui';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

interface EvidenceTimelineProps {
  trendData: TrustTrendPoint[];
  events: TrustEvent[];
}

export default function EvidenceTimeline({ trendData, events }: EvidenceTimelineProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const handleCopyHash = async (eventId: string, hash: string) => {
    try {
      await navigator.clipboard.writeText(hash);
      setCopiedId(eventId);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy evidence hash:', err);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false,
      timeZone: 'UTC'
    }) + ' UTC';
  };

  return (
    <div className="space-y-6 text-left">
      {/* Verification Trend Chart (Recharts) */}
      <Card className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2 tracking-tight">
              <TrendingUp className="w-5 h-5 text-[#00C853]" />
              Trust Verification Trend
            </CardTitle>
            <Badge className="bg-[#00C853]/10 text-[#00C853] border-[#00C853]/20 text-[9px] font-bold">
              VERIFICATION OVER TIME
            </Badge>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Transition of subjective self-attested controls to continuous telemetry-verified security posture.
          </p>
        </CardHeader>
        <CardContent>
          <div className="h-64 w-full mt-4">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={trendData}
                margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
              >
                <defs>
                  <linearGradient id="colorVerified" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#00C853" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#00C853" stopOpacity={0.0} />
                  </linearGradient>
                  <linearGradient id="colorAttested" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#D97706" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#D97706" stopOpacity={0.0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" className="dark:stroke-slate-800" />
                <XAxis 
                  dataKey="date" 
                  tick={{ fill: '#64748B', fontSize: 10, fontWeight: 600 }}
                  axisLine={{ stroke: '#CBD5E1' }}
                />
                <YAxis 
                  tick={{ fill: '#64748B', fontSize: 10, fontWeight: 600 }}
                  axisLine={{ stroke: '#CBD5E1' }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    border: '1px stroke rgba(51, 65, 85, 0.8)',
                    borderRadius: '12px',
                    color: '#F8FAFC',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />
                <Area 
                  type="monotone" 
                  dataKey="verified" 
                  stackId="1"
                  stroke="#00C853" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorVerified)" 
                  name="Telemetry Verified"
                />
                <Area 
                  type="monotone" 
                  dataKey="attested" 
                  stackId="1"
                  stroke="#D97706" 
                  strokeWidth={2}
                  fillOpacity={1} 
                  fill="url(#colorAttested)" 
                  name="Self-Attested"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {/* Chronological Evidence Logs */}
      <Card className="bg-white/60 dark:bg-slate-950/20 backdrop-blur-[10px] border border-slate-200 dark:border-slate-800 rounded-3xl hover:shadow-md transition-all duration-300">
        <CardHeader className="pb-2">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-extrabold text-slate-900 dark:text-slate-100 flex items-center gap-2 tracking-tight">
              <Activity className="w-5 h-5 text-indigo-500" />
              Cryptographic Verification Logs
            </CardTitle>
            <span className="text-[9px] bg-slate-800 border border-slate-700 text-slate-400 font-mono px-2 py-0.5 rounded font-bold uppercase tracking-wider">
              TTY: VERIFIED_DAEMON_V2
            </span>
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 font-semibold">
            Deterministic record of control verification updates matching incoming SIEM alerts and active hooks.
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4 mt-4">
            {events.map((evt) => (
              <div 
                key={evt.id}
                className="p-4 bg-slate-50/50 dark:bg-slate-900/30 rounded-2xl border border-slate-200/50 dark:border-slate-800/40 space-y-3 relative hover:border-slate-350 dark:hover:border-slate-700 transition-all duration-200"
              >
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2.5">
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                    <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono font-bold">
                      {formatDate(evt.timestamp)}
                    </span>
                    <Badge className="bg-indigo-500/10 text-indigo-500 border-indigo-500/20 text-[8px] font-extrabold uppercase rounded px-1.5 py-0.5">
                      {evt.connector}
                    </Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-slate-450 font-bold uppercase tracking-wider">State Shift:</span>
                    <Badge variant="outline" className="text-[8px] font-bold border-slate-300 dark:border-slate-800">
                      {evt.oldState}
                    </Badge>
                    <ArrowRight className="w-3 h-3 text-slate-400" />
                    <Badge className="bg-[#00C853]/10 text-[#00C853] border-[#00C853]/20 text-[8px] font-bold">
                      {evt.newState}
                    </Badge>
                  </div>
                </div>

                <div className="space-y-1">
                  <h4 className="text-xs font-black text-slate-900 dark:text-slate-200">
                    {evt.controlId} &mdash; {evt.controlName}
                  </h4>
                  <p className="text-[11px] font-semibold text-slate-600 dark:text-slate-450 leading-relaxed">
                    {evt.details}
                  </p>
                </div>

                {/* Evidence Hash Segment */}
                <div className="flex items-center justify-between flex-wrap gap-2 pt-2 border-t border-slate-250/50 dark:border-slate-800/30">
                  <div className="flex items-center gap-1.5 text-[9px] font-mono text-slate-500 dark:text-slate-450 select-all bg-slate-100 dark:bg-slate-900 px-2 py-0.5 rounded border border-slate-200/50 dark:border-slate-800/40">
                    <Terminal className="w-3 h-3 text-[#00C853] shrink-0" />
                    <span className="text-slate-400 font-bold uppercase tracking-wider mr-1">EVIDENCE:</span>
                    <span>{evt.evidenceHash}</span>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      variant="secondary"
                      size="sm"
                      onClick={() => handleCopyHash(evt.id, evt.evidenceHash)}
                      className="gap-1 px-2.5 h-6 text-[9px] font-bold hover:bg-slate-200 dark:hover:bg-slate-850"
                    >
                      {copiedId === evt.id ? (
                        <>
                          <Check className="w-3 h-3 text-[#00C853]" />
                          Copied
                        </>
                      ) : (
                        <>
                          <Copy className="w-3 h-3 text-slate-400" />
                          Copy Hash
                        </>
                      )}
                    </Button>
                    
                    <a 
                      href={`/dashboard/compliance-drift?control=${evt.controlId}`} 
                      className="inline-flex items-center gap-1 px-2.5 h-6 text-[9px] font-bold bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-850 text-slate-700 dark:text-slate-350"
                    >
                      <ExternalLink className="w-3 h-3 text-slate-400" />
                      Verify Drift
                    </a>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
