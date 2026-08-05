import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Mail, ShieldCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

const MOCK_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 94, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 99, assessment_id: 'asm-demo-1' },
];

const MOCK_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 94, attested: 5, unverified: 1 },
  { date: 'Aug 03', verified: 99, attested: 1, unverified: 0 },
];

const MOCK_EVENTS: TrustEvent[] = [
  {
    id: 'evt-e1',
    timestamp: '2026-08-03T20:45:00Z',
    connector: 'Proofpoint / Exchange Online API',
    controlId: 'EML-01',
    controlName: 'DMARC Reject Policy & DKIM Signature Alignment',
    details: '100% of outbound company domains validated with DMARC p=reject and strict DKIM alignment.',
    oldState: 'Self-Attested',
    newState: 'Verified',
    status: 'success',
    evidenceHash: '0xe8201fa7b99c43d'
  }
];

const MOCK_ACTION = {
  id: 'action-eml-1',
  title: 'External Inbound Banner Rule Disabled for 1 Subdomain',
  severity: 'low' as const,
  impact_narrative: 'Inbound external sender warning banner rule is inactive for vendor portal subdomain.',
  evidence: 'Connector: Exchange Transport Rules\nRule ID: ETR-9021\nStatus: Disabled',
  recommendation: 'Re-enable ETR-9021 external tag banner rule in Exchange Admin Center.',
  can_be_undone: true,
  last_verified_at: '45 minutes ago',
  confidence_pct: 99,
  verification_method: 'Exchange Online PowerShell Daemon',
};

const MOCK_INVENTORY = [
  { domain: 'resilai.org', dmarc: 'p=reject (100%)', spf: 'pass', dkim: 'valid (2048-bit)', status: 'Healthy' },
  { domain: 'mail.resilai.org', dmarc: 'p=reject (100%)', spf: 'pass', dkim: 'valid (2048-bit)', status: 'Healthy' },
  { domain: 'health-connect.org', dmarc: 'p=reject (100%)', spf: 'pass', dkim: 'valid (2048-bit)', status: 'Healthy' },
];

export function EmailPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SummaryCard
        domainName="Email Security & Delivery"
        status="ready"
        readinessScore={99}
        soWhat="All outbound email domains enforce DMARC p=reject, preventing email spoofing and securing patient communications."
        lastVerifiedText="Verified 5m ago via Exchange Online & Proofpoint API"
        icon={Mail}
        keyMetrics={[
          { label: 'DMARC Enforced', value: '100% (p=reject)', status: 'good' },
          { label: 'Phishing Intercept', value: '99.9%', status: 'good' },
          { label: 'Inbound DLP', value: 'Active', status: 'good' },
          { label: 'Domain Impersonation', value: '0 Breaches', status: 'good' },
        ]}
      />

      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-6 text-sm font-bold text-slate-500 dark:text-slate-400">
        {(['overview', 'events', 'issues', 'inventory'] as const).map((tab) => (
          <button
            key={tab}
            className={`pb-3 capitalize border-b-2 transition-all ${
              activeTab === tab ? 'text-indigo-600 border-indigo-600 dark:text-indigo-400 font-extrabold' : 'border-transparent'
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ScoreTrendChart data={MOCK_TREND} height={220} />
          </div>
          <Card className="p-6">
            <CardHeader className="p-0 pb-3">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" /> Email Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">DMARC p=reject</span>
                <TrustBadge status="verified" text="100% Enforced" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">Attachment Sandbox</span>
                <TrustBadge status="verified" text="Active" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'events' && (
        <EvidenceTimeline
          trendData={MOCK_TRUST_TREND}
          events={MOCK_EVENTS}
        />
      )}

      {activeTab === 'issues' && (
        <StatusCard variant="story" action={MOCK_ACTION} onFix={async () => { new Promise(r => setTimeout(r, 1000)); }} />
      )}

      {activeTab === 'inventory' && (
        <Card className="overflow-hidden">
          <CardHeader className="p-5 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-base font-bold">Email Domain Authentication Inventory</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Domain</th>
                  <th className="px-6 py-3">DMARC Policy</th>
                  <th className="px-6 py-3">SPF</th>
                  <th className="px-6 py-3">DKIM</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {MOCK_INVENTORY.map((item, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 font-bold">{item.domain}</td>
                    <td className="px-6 py-4 font-mono text-emerald-600">{item.dmarc}</td>
                    <td className="px-6 py-4 uppercase font-semibold">{item.spf}</td>
                    <td className="px-6 py-4">{item.dkim}</td>
                    <td className="px-6 py-4"><TrustBadge status="verified" text={item.status} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}

export default EmailPage;
