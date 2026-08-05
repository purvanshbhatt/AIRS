import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Laptop, ShieldCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

const MOCK_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 91, assessment_id: 'asm-demo-1' },
  { date: '2026-07-30', name: 'Jul 30', score: 93, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 97, assessment_id: 'asm-demo-1' },
];

const MOCK_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 91, attested: 8, unverified: 1 },
  { date: 'Aug 03', verified: 97, attested: 3, unverified: 0 },
];

const MOCK_EVENTS: TrustEvent[] = [
  {
    id: 'evt-d1',
    timestamp: '2026-08-03T21:00:00Z',
    connector: 'CrowdStrike Falcon API',
    controlId: 'DEV-01',
    controlName: 'EDR Agent Health & EOL OS Isolation',
    details: '1,840 fleet devices confirmed reporting active telemetry with zero unpatched zero-day exploits detected.',
    oldState: 'Not Verified',
    newState: 'Verified',
    status: 'success',
    evidenceHash: '0xd41901a89c2f109'
  }
];

const MOCK_ACTION = {
  id: 'action-dev-1',
  title: 'Outdated Endpoint EDR Agent Version on 4 Workstations',
  severity: 'low' as const,
  impact_narrative: '4 developer laptops are running EDR version 7.11 which is one minor release behind current baseline 7.12.',
  evidence: 'Connector: CrowdStrike EDR\nAffected Host IDs: [host-401, host-402, host-403, host-404]',
  recommendation: 'Push background update policy via Intune MDM.',
  can_be_undone: true,
  last_verified_at: '30 minutes ago',
  confidence_pct: 99,
  verification_method: 'CrowdStrike API Collector',
};

const MOCK_INVENTORY = [
  { name: 'Corporate Laptops (MacBook Pro / ThinkPad)', count: 1420, edr: '100% Active', diskEncryption: '100% BitLocker/FileVault', status: 'Healthy' },
  { name: 'Clinical Workstations & Kiosks', count: 350, edr: '100% Active', diskEncryption: '100% Enforced', status: 'Healthy' },
  { name: 'Mobile Devices (iOS / Android MDM)', count: 680, edr: '99.2% Active', diskEncryption: '100% Enforced', status: 'Healthy' },
];

export function DevicesPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SummaryCard
        domainName="Devices & Endpoints"
        status="ready"
        readinessScore={97}
        soWhat="100% of workforce laptops and clinical workstations are encrypted, monitored by EDR, and compliant with endpoint security policies."
        lastVerifiedText="Verified 3m ago via Microsoft Intune & CrowdStrike API"
        icon={Laptop}
        keyMetrics={[
          { label: 'EDR Coverage', value: '100.0%', status: 'good' },
          { label: 'Disk Encryption', value: '100.0%', status: 'good' },
          { label: 'OS Patch SLA', value: '98.5%', status: 'good' },
          { label: 'Unmanaged Devices', value: '0 Detected', status: 'good' },
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
                <ShieldCheck className="w-5 h-5 text-emerald-600" /> Endpoint Health
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">CrowdStrike EDR</span>
                <TrustBadge status="verified" text="100% Active" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">Intune MDM Compliance</span>
                <TrustBadge status="verified" text="Compliant" />
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
            <CardTitle className="text-base font-bold">Managed Endpoint Fleet Inventory</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Fleet Group</th>
                  <th className="px-6 py-3">Count</th>
                  <th className="px-6 py-3">EDR Status</th>
                  <th className="px-6 py-3">Encryption</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {MOCK_INVENTORY.map((item, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 font-bold">{item.name}</td>
                    <td className="px-6 py-4">{item.count}</td>
                    <td className="px-6 py-4 font-mono text-emerald-600">{item.edr}</td>
                    <td className="px-6 py-4">{item.diskEncryption}</td>
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

export default DevicesPage;
