import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Database, ShieldCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

// Domain Mock Data
const MOCK_BACKUP_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 92, assessment_id: 'asm-demo-1' },
  { date: '2026-07-29', name: 'Jul 29', score: 94, assessment_id: 'asm-demo-1' },
  { date: '2026-07-30', name: 'Jul 30', score: 95, assessment_id: 'asm-demo-1' },
  { date: '2026-07-31', name: 'Jul 31', score: 96, assessment_id: 'asm-demo-1' },
  { date: '2026-08-01', name: 'Aug 01', score: 97, assessment_id: 'asm-demo-1' },
  { date: '2026-08-02', name: 'Aug 02', score: 98, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 98, assessment_id: 'asm-demo-1' },
];

const MOCK_BACKUP_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 92, attested: 6, unverified: 2 },
  { date: 'Jul 30', verified: 95, attested: 4, unverified: 1 },
  { date: 'Aug 03', verified: 98, attested: 2, unverified: 0 },
];

const MOCK_BACKUP_EVENTS: TrustEvent[] = [
  {
    id: 'evt-b1',
    timestamp: '2026-08-03T23:45:00Z',
    connector: 'Veeam Backup API',
    controlId: 'BKP-01',
    controlName: 'Immutable Air-Gapped Vault Restore Validation',
    details: 'Automated synthetic restore test completed successfully for Primary EHR Database. 0 block corruption detected.',
    oldState: 'Not Verified',
    newState: 'Verified',
    status: "ready",
    evidenceHash: '0xa73f82e1d94b01c'
  },
  {
    id: 'evt-b2',
    timestamp: '2026-08-03T21:15:00Z',
    connector: 'AWS Backup / S3 Lock',
    controlId: 'BKP-02',
    controlName: 'Object Lock Immutability Enforcement',
    details: 'S3 Object Lock compliance retention verified on 1,420 snapshots with compliance mode expiration set to 90 days.',
    oldState: 'Self-Attested',
    newState: 'Verified',
    status: "ready",
    evidenceHash: '0xb942c1ef6510a8e'
  }
];

const MOCK_BACKUP_ACTION = {
  id: 'action-bkp-1',
  title: 'Secondary Offsite Air-Gap Backup Mirroring Lag',
  severity: 'high' as const,
  impact_narrative: 'Offsite replica in secondary region US-West is 18 minutes behind primary RPO threshold due to network throttling.',
  evidence: 'Connector: AWS Backup S3 Replication\nLag: 18 minutes (SLA threshold: 15 minutes)\nBytes Pending: 4.2 GB',
  recommendation: 'Increase inter-region replication bandwidth or prioritize transaction log replication streams.',
  can_be_undone: true,
  last_verified_at: '12 minutes ago',
  confidence_pct: 98,
  verification_method: 'AWS CloudWatch Metrics & Veeam Collector',
};

const MOCK_BACKUP_INVENTORY = [
  { name: 'EHR Primary Database (SQL Cluster)', type: 'Database Vault', target: 'Veeam Vault Alpha', rpo: '12m', status: 'Healthy', immutable: true },
  { name: 'PACS Medical Imaging Vault', type: 'Object Store', target: 'AWS S3 Glacier Flexible', rpo: '15m', status: 'Healthy', immutable: true },
  { name: 'Active Directory System State', type: 'Domain Controller', target: 'Azure Backup Center', rpo: '5m', status: 'Healthy', immutable: true },
  { name: 'User Workstation Profiles', type: 'Endpoint Agent', target: 'Druva Endpoint', rpo: '1h', status: 'Warning', immutable: false },
];

import { SimulatedTelemetryBanner } from '../../components/common/SimulatedTelemetryBanner';

export function BackupsPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SimulatedTelemetryBanner domainName="Backups & Disaster Recovery" />

      {/* Executive Summary Card ("So What?") */}
      <SummaryCard
        domainName="Backups & Disaster Recovery"
        status="ready"
        readinessScore={98}
        soWhat="100% of critical healthcare databases and user backups are verified recoverable with RPO < 15m and guaranteed ransomware immutability."
        lastVerifiedText="Verified 4m ago via Veeam API & AWS S3 Object Lock"
        icon={Database}
        keyMetrics={[
          { label: 'RPO Compliance', value: '12m avg', status: 'good', subtitle: 'Target < 15m' },
          { label: 'RTO SLA', value: '45m avg', status: 'good', subtitle: 'Target < 60m' },
          { label: 'Immutability', value: '100% Enforced', status: 'good' },
          { label: 'Test Restores', value: 'Passed (24/24)', status: 'good' },
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
            <ScoreTrendChart data={MOCK_BACKUP_TREND} height={220} />
          </div>
          <Card className="p-6 flex flex-col justify-between">
            <CardHeader className="p-0 pb-3">
              <CardTitle className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-emerald-600" />
                Backup Safeguards
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Air-Gapped Secondary</span>
                <TrustBadge status="verified" text="Active" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Ransomware Object Lock</span>
                <TrustBadge status="verified" text="Active" />
              </div>
              <div className="p-3 rounded-xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-100 dark:border-amber-900/30 flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-800 dark:text-slate-200">Offsite Replication SLA</span>
                <span className="text-xs font-bold text-amber-700 dark:text-amber-400">18m Lag</span>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'events' && (
        <EvidenceTimeline
          trendData={MOCK_BACKUP_TRUST_TREND}
          events={MOCK_BACKUP_EVENTS}
        />
      )}

      {activeTab === 'issues' && (
        <div className="space-y-4">
          <StatusCard
            variant="story"
            action={MOCK_BACKUP_ACTION}
            onFix={async () => { new Promise(r => setTimeout(r, 1000)); }}
          />
        </div>
      )}

      {activeTab === 'inventory' && (
        <Card className="overflow-hidden">
          <CardHeader className="p-5 border-b border-slate-100 dark:border-slate-800">
            <CardTitle className="text-base font-bold text-slate-900 dark:text-white">
              Backup Jobs & Vault Inventory
            </CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200 dark:border-slate-800">
                  <tr>
                    <th className="px-6 py-3">Asset Name</th>
                    <th className="px-6 py-3">Vault Type</th>
                    <th className="px-6 py-3">Destination</th>
                    <th className="px-6 py-3">Current RPO</th>
                    <th className="px-6 py-3">Immutability</th>
                    <th className="px-6 py-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-medium">
                  {MOCK_BACKUP_INVENTORY.map((item, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50 dark:hover:bg-slate-900/50">
                      <td className="px-6 py-4 font-bold text-slate-900 dark:text-slate-100">{item.name}</td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{item.type}</td>
                      <td className="px-6 py-4 text-slate-600 dark:text-slate-300">{item.target}</td>
                      <td className="px-6 py-4 font-mono text-slate-800 dark:text-slate-200">{item.rpo}</td>
                      <td className="px-6 py-4">
                        {item.immutable ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400">Enforced</span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-bold bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400">Standard</span>
                        )}
                      </td>
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

export default BackupsPage;
