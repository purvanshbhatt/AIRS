import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Users, ShieldCheck, UserCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

const MOCK_IDENTITY_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 90, assessment_id: 'asm-demo-1' },
  { date: '2026-07-29', name: 'Jul 29', score: 92, assessment_id: 'asm-demo-1' },
  { date: '2026-07-30', name: 'Jul 30', score: 93, assessment_id: 'asm-demo-1' },
  { date: '2026-07-31', name: 'Jul 31', score: 95, assessment_id: 'asm-demo-1' },
  { date: '2026-08-01', name: 'Aug 01', score: 96, assessment_id: 'asm-demo-1' },
  { date: '2026-08-02', name: 'Aug 02', score: 96, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 96, assessment_id: 'asm-demo-1' },
];

const MOCK_IDENTITY_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 90, attested: 8, unverified: 2 },
  { date: 'Jul 30', verified: 93, attested: 5, unverified: 2 },
  { date: 'Aug 03', verified: 96, attested: 3, unverified: 1 },
];

const MOCK_IDENTITY_EVENTS: TrustEvent[] = [
  {
    id: 'evt-i1',
    timestamp: '2026-08-03T22:10:00Z',
    connector: 'Okta / Azure AD API',
    controlId: 'IDN-01',
    controlName: 'Phishing-Resistant MFA Enforcement',
    details: 'Enforced FIDO2 / WebAuthn security key requirement on 45 executive and administrator identities.',
    oldState: 'Not Verified',
    newState: 'Verified',
    status: "ready",
    evidenceHash: '0x918f4a2b6d19c02'
  },
  {
    id: 'evt-i2',
    timestamp: '2026-08-03T18:30:00Z',
    connector: 'CyberArk PAM Vault',
    controlId: 'IDN-02',
    controlName: 'Privileged Account Rotation & Just-in-Time Access',
    details: 'Domain Admin emergency credentials successfully rotated; automatic session timeout set to 15m.',
    oldState: 'Self-Attested',
    newState: 'Verified',
    status: "ready",
    evidenceHash: '0xc31e782a4d091fb'
  }
];

const MOCK_IDENTITY_ACTION = {
  id: 'action-idn-1',
  title: 'Stale Contractor Account Pending Offboarding',
  severity: 'medium' as const,
  impact_narrative: '3 contractor identity accounts remain active past contract expiration date without MFA challenge logs in 30 days.',
  evidence: 'Connector: Microsoft Entra ID\nInactive Users: 3\nLast Login: > 30 days ago',
  recommendation: 'Trigger automated identity de-provisioning workflow to disable inactive accounts.',
  can_be_undone: true,
  last_verified_at: '25 minutes ago',
  confidence_pct: 95,
  verification_method: 'Entra ID Graph API Collector',
};

const MOCK_IDENTITY_INVENTORY = [
  { provider: 'Okta Enterprise IDP', scope: 'Workforce SSO', activeUsers: 2450, mfaRate: '99.8%', status: 'Healthy' },
  { provider: 'Microsoft Entra ID (Azure AD)', scope: 'Cloud & Office 365', activeUsers: 2450, mfaRate: '99.4%', status: 'Healthy' },
  { provider: 'CyberArk PAM', scope: 'Privileged Infrastructure', activeUsers: 32, mfaRate: '100.0%', status: 'Healthy' },
  { provider: 'PingFederate', scope: 'Legacy Systems', activeUsers: 140, mfaRate: '94.2%', status: 'Warning' },
];

import { SimulatedTelemetryBanner } from '../../components/common/SimulatedTelemetryBanner';

export function IdentityPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SimulatedTelemetryBanner domainName="Identity & Access" />

      {/* Executive Summary Card ("So What?") */}
      <SummaryCard
        domainName="Identity & Access Management"
        status="ready"
        readinessScore={96}
        soWhat="99.4% of workforce accounts enforce phishing-resistant MFA, and zero unauthenticated privileged accounts exist across company environments."
        lastVerifiedText="Verified 2m ago via Okta & Entra ID Connectors"
        icon={Users}
        keyMetrics={[
          { label: 'MFA Coverage', value: '99.4%', status: 'good', subtitle: 'Target 99%+' },
          { label: 'Privileged Access', value: '100% Monitored', status: 'good' },
          { label: 'Suspicious Logins', value: '0 Active', status: 'good' },
          { label: 'Offboard Delay', value: '3 Pending', status: "drift" },
        ]}
      />

      {/* Domain Navigation Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-6 text-sm font-bold text-slate-500 dark:text-slate-400">
        {(['overview', 'events', 'issues', 'inventory'] as const).map((tab) => (
          <button
            key={tab}
            className={`pb-3 capitalize border-b-2 transition-all relative ${
              activeTab === tab
                ? 'text-indigo-600 border-indigo-600 dark:text-indigo-400 dark:border-indigo-400 font-extrabold'
                : 'border-transparent hover:text-slate-900 dark:hover:text-slate-200'
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <ScoreTrendChart data={MOCK_IDENTITY_TREND} height={220} />
          </div>
          <Card className="p-6 flex flex-col justify-between">
            <CardHeader className="p-0 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <UserCheck className="w-5 h-5 text-indigo-600" />
                Identity Posture
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">FIDO2 Hardware Keys</span>
                <TrustBadge status="verified" text="Enforced" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">PAM Vault Rotation</span>
                <TrustBadge status="verified" text="Automated" />
              </div>
              <div className="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Contractor Deprovision</span>
                <span className="text-xs font-bold text-amber-700 dark:text-amber-400">3 Pending</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'events' && (
        <EvidenceTimeline
          trendData={MOCK_IDENTITY_TRUST_TREND}
          events={MOCK_IDENTITY_EVENTS}
        />
      )}

      {activeTab === 'issues' && (
        <div className="space-y-4">
          <StatusCard
            variant="story"
            action={MOCK_IDENTITY_ACTION}
            onFix={async () => { new Promise(r => setTimeout(r, 1000)); }}
          />
        </div>
      )}

      {activeTab === 'inventory' && (
        <Card className="overflow-hidden">
          <CardHeader className="p-5 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-base font-bold text-slate-900 dark:text-white">
              Identity Providers & Directory Systems
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-6 py-3">Provider</th>
                    <th className="px-6 py-3">Scope</th>
                    <th className="px-6 py-3">Active Identities</th>
                    <th className="px-6 py-3">MFA Rate</th>
                    <th className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                  {MOCK_IDENTITY_INVENTORY.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/50">
                      <td className="px-6 py-4 font-bold text-slate-900 dark:text-slate-100">{item.provider}</td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{item.scope}</td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{item.activeUsers}</td>
                      <td className="px-6 py-4 font-mono font-bold text-emerald-600 dark:text-emerald-400">{item.mfaRate}</td>
                      <td className="px-6 py-4">
                        <TrustBadge status="verified" text={item.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}
    </motion.div>
  );
}

export default IdentityPage;
