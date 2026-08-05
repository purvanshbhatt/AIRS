import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Network, ShieldCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

const MOCK_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 92, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 97, assessment_id: 'asm-demo-1' },
];

const MOCK_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 92, attested: 7, unverified: 1 },
  { date: 'Aug 03', verified: 97, attested: 3, unverified: 0 },
];

const MOCK_EVENTS: TrustEvent[] = [
  {
    id: 'evt-n1',
    timestamp: '2026-08-03T21:20:00Z',
    connector: 'Palo Alto Panorama API',
    controlId: 'NET-01',
    controlName: 'Zero-Trust Microsegmentation Enforcement',
    details: 'SD-WAN edge firewalls confirmed active zero-trust inspection across 12 clinic subnets.',
    oldState: 'Not Verified',
    newState: 'Verified',
    status: 'success',
    evidenceHash: '0xf7102a39d88b401'
  }
];

const MOCK_ACTION = {
  id: 'action-net-1',
  title: 'Guest Wi-Fi Subnet Isolation Audit Pending',
  severity: 'low' as const,
  impact_narrative: 'Clinic guest Wi-Fi network routing rules re-evaluated after firmware upgrade.',
  evidence: 'Connector: Cisco Meraki API\nNetwork: Guest-VLAN-40\nIsolation: Verified',
  recommendation: 'Confirm automated egress rule audit.',
  can_be_undone: true,
  last_verified_at: '15 minutes ago',
  confidence_pct: 98,
  verification_method: 'Meraki Collector',
};

const MOCK_INVENTORY = [
  { site: 'Main Hospital Campus', firewalls: 'Palo Alto HA Cluster', zeroTrust: 'Enforced', vpnMfa: 'Active (FIDO2)', status: 'Healthy' },
  { site: 'Outpatient Clinic East', firewalls: 'Meraki MX85', zeroTrust: 'Enforced', vpnMfa: 'Active', status: 'Healthy' },
  { site: 'Outpatient Clinic West', firewalls: 'Meraki MX85', zeroTrust: 'Enforced', vpnMfa: 'Active', status: 'Healthy' },
];

export function NetworkPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SummaryCard
        domainName="Network & Zero Trust Infrastructure"
        status="ready"
        readinessScore={97}
        soWhat="Zero-trust microsegmentation isolates clinical devices from open internet traffic, preventing lateral movement across all clinics."
        lastVerifiedText="Verified 2m ago via Palo Alto Panorama & Meraki API"
        icon={Network}
        keyMetrics={[
          { label: 'Zero-Trust Status', value: '100% Enforced', status: 'good' },
          { label: 'VPN MFA Rate', value: '100.0%', status: 'good' },
          { label: 'Edge Firewalls', value: '12/12 Online', status: 'good' },
          { label: 'Unchecked Traffic', value: '0 Rules', status: 'good' },
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
                <ShieldCheck className="w-5 h-5 text-emerald-600" /> Network Controls
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">Microsegmentation</span>
                <TrustBadge status="verified" text="Enforced" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">TLS Inspection</span>
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
            <CardTitle className="text-base font-bold">Network Infrastructure & Firewall Site List</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Site</th>
                  <th className="px-6 py-3">Firewall Model</th>
                  <th className="px-6 py-3">Zero Trust</th>
                  <th className="px-6 py-3">VPN Authentication</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {MOCK_INVENTORY.map((item, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 font-bold">{item.site}</td>
                    <td className="px-6 py-4">{item.firewalls}</td>
                    <td className="px-6 py-4 font-mono text-emerald-600">{item.zeroTrust}</td>
                    <td className="px-6 py-4">{item.vpnMfa}</td>
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

export default NetworkPage;
