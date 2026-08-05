import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Cloud, ShieldCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

const MOCK_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 93, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 98, assessment_id: 'asm-demo-1' },
];

const MOCK_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 93, attested: 6, unverified: 1 },
  { date: 'Aug 03', verified: 98, attested: 2, unverified: 0 },
];

const MOCK_EVENTS: TrustEvent[] = [
  {
    id: 'evt-c1',
    timestamp: '2026-08-03T21:50:00Z',
    connector: 'AWS Security Hub / Wiz API',
    controlId: 'CLD-01',
    controlName: 'Public S3 Bucket & Unencrypted Storage Audit',
    details: 'Zero publicly accessible cloud storage buckets or unencrypted EBS volumes across AWS & Azure accounts.',
    oldState: 'Not Verified',
    newState: 'Verified',
    status: 'success',
    evidenceHash: '0xc1029a7e6b541d0'
  }
];

const MOCK_ACTION = {
  id: 'action-cld-1',
  title: 'AWS CloudTrail Log File Integrity Validation Enabled',
  severity: 'low' as const,
  impact_narrative: 'CloudTrail log digest validation automatically verified for tamper-proof audit trails.',
  evidence: 'Connector: AWS CloudTrail\nDigest Validation: Enabled\nBucket: resilai-audit-logs',
  recommendation: 'Maintain continuous validation stream.',
  can_be_undone: true,
  last_verified_at: '10 minutes ago',
  confidence_pct: 99,
  verification_method: 'AWS CloudTrail API Daemon',
};

const MOCK_INVENTORY = [
  { provider: 'AWS Production (us-east-1)', resources: '142 EC2 / EKS Clusters', publicExposure: '0 Public Buckets', encryption: '100% KMS KMS-CMK', status: 'Healthy' },
  { provider: 'AWS DR Region (us-west-2)', resources: '48 Replica Nodes', publicExposure: '0 Public Buckets', encryption: '100% KMS CMK', status: 'Healthy' },
  { provider: 'Azure Healthcare Tenant', resources: '38 Managed Subscriptions', publicExposure: '0 Public Blobs', encryption: '100% Customer-Managed Key', status: 'Healthy' },
];

export function CloudPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SummaryCard
        domainName="Cloud Infrastructure Security"
        status="ready"
        readinessScore={98}
        soWhat="Zero publicly accessible cloud storage buckets or unencrypted cloud volumes exist across AWS & Azure accounts."
        lastVerifiedText="Verified 3m ago via AWS Security Hub & Wiz API"
        icon={Cloud}
        keyMetrics={[
          { label: 'Public Exposure', value: '0 Public Buckets', status: 'good' },
          { label: 'KMS Encryption', value: '100.0%', status: 'good' },
          { label: 'IAM Misconfig', value: '0 Critical', status: 'good' },
          { label: 'GuardDuty Status', value: 'Active All Regions', status: 'good' },
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
                <ShieldCheck className="w-5 h-5 text-emerald-600" /> Cloud Posture
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">GuardDuty Threat Detection</span>
                <TrustBadge status="verified" text="Active" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">KMS Key Rotation</span>
                <TrustBadge status="verified" text="Enforced" />
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
            <CardTitle className="text-base font-bold">Cloud Accounts & Resource Subscriptions</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Account / Tenant</th>
                  <th className="px-6 py-3">Workloads</th>
                  <th className="px-6 py-3">Public Exposure</th>
                  <th className="px-6 py-3">KMS Encryption</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {MOCK_INVENTORY.map((item, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 font-bold">{item.provider}</td>
                    <td className="px-6 py-4">{item.resources}</td>
                    <td className="px-6 py-4 font-mono text-emerald-600">{item.publicExposure}</td>
                    <td className="px-6 py-4">{item.encryption}</td>
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

export default CloudPage;
