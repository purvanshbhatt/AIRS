import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, ShieldCheck } from 'lucide-react';
import { SummaryCard } from '../../components/common/SummaryCard';
import { ScoreTrendChart } from '../../components/ScoreTrendChart';
import EvidenceTimeline from '../../components/dashboard/EvidenceTimeline';
import { StatusCard } from '../../components/readiness/StatusCard';
import { TrustBadge } from '../../components/readiness/TrustBadge';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui';
import type { ScoreTrendPoint } from '../../types';
import type { TrustEvent, TrustTrendPoint } from '../../hooks/useMockTrustData';

const MOCK_TREND: ScoreTrendPoint[] = [
  { date: '2026-07-28', name: 'Jul 28', score: 95, assessment_id: 'asm-demo-1' },
  { date: '2026-08-03', name: 'Aug 03', score: 99, assessment_id: 'asm-demo-1' },
];

const MOCK_TRUST_TREND: TrustTrendPoint[] = [
  { date: 'Jul 28', verified: 95, attested: 4, unverified: 1 },
  { date: 'Aug 03', verified: 99, attested: 1, unverified: 0 },
];

const MOCK_EVENTS: TrustEvent[] = [
  {
    id: 'evt-ai1',
    timestamp: '2026-08-03T23:10:00Z',
    connector: 'LLM Gateway Guardrails API',
    controlId: 'AI-01',
    controlName: 'PHI Ingestion Prevention & Model Watermarking',
    details: 'Verified zero unredacted Patient Health Information (PHI) transmitted in LLM prompt logs across all internal AI tools.',
    oldState: 'Not Verified',
    newState: 'Verified',
    status: "ready",
    evidenceHash: '0xa0918c72e34f901'
  }
];

const MOCK_ACTION = {
  id: 'action-ai-1',
  title: 'Internal Assistant Vector Database Encryption Audit Passed',
  severity: 'low' as const,
  impact_narrative: 'Vector embeddings in Pinecone DB verified encrypted with KMS customer-managed key.',
  evidence: 'Connector: Pinecone KMS Validator\nIndex: ehr-docs-v2\nEncryption: KMS AES-256',
  recommendation: 'Continuous automated validation active.',
  can_be_undone: true,
  last_verified_at: '5 minutes ago',
  confidence_pct: 100,
  verification_method: 'KMS Vector DB Guard',
};

const MOCK_INVENTORY = [
  { model: 'ResilAI Operational Guidance Engine', type: 'Fine-Tuned LLM', phiFilter: 'Enabled (Zero Data Retention)', auditLog: 'Cryptographic Stream', status: 'Healthy' },
  { model: 'EHR Summary Assistant (Azure OpenAI)', type: 'Private Tenant GPT-4o', phiFilter: 'Enabled (Presidio Redactor)', auditLog: '100% Immutable', status: 'Healthy' },
  { model: 'Internal Knowledge Retrieval (Pinecone)', type: 'Vector Database', phiFilter: 'Encrypted KMS', auditLog: 'Logged', status: 'Healthy' },
];

import { SimulatedTelemetryBanner } from '../../components/common/SimulatedTelemetryBanner';

export function AIPage() {
  const [activeTab, setActiveTab] = useState<'overview' | 'events' | 'issues' | 'inventory'>('overview');

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-6 text-left"
    >
      <SimulatedTelemetryBanner domainName="AI & Machine Learning Governance" />

      <SummaryCard
        domainName="AI & Machine Learning Governance"
        status="ready"
        readinessScore={99}
        soWhat="100% of AI models and LLM integrations feature real-time PHI redaction, zero data retention agreements, and cryptographic auditability."
        lastVerifiedText="Verified 1m ago via LLM Gateway Guardrails & Azure OpenAI API"
        icon={Cpu}
        keyMetrics={[
          { label: 'PHI Redaction Rate', value: '100.0%', status: 'good' },
          { label: 'Data Retention', value: '0 Days (No Training)', status: 'good' },
          { label: 'Private Subnets', value: '100% Isolated', status: 'good' },
          { label: 'Model Lineage', value: 'Verified', status: 'good' },
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
                <ShieldCheck className="w-5 h-5 text-emerald-600" /> AI Safeguards
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0 space-y-3">
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">Real-Time PHI Sanitizer</span>
                <TrustBadge status="verified" text="Active" />
              </div>
              <div className="p-3 rounded-xl bg-emerald-50/60 border border-emerald-100 flex items-center justify-between">
                <span className="text-xs font-semibold">Zero Training Opt-Out</span>
                <TrustBadge status="verified" text="Verified" />
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
            <CardTitle className="text-base font-bold">AI Model & LLM Endpoint Inventory</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 dark:bg-slate-900 text-xs font-bold uppercase text-slate-500 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3">Model / Endpoint</th>
                  <th className="px-6 py-3">Architecture</th>
                  <th className="px-6 py-3">PHI Guardrail</th>
                  <th className="px-6 py-3">Audit Log Stream</th>
                  <th className="px-6 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {MOCK_INVENTORY.map((item, idx) => (
                  <tr key={idx}>
                    <td className="px-6 py-4 font-bold">{item.model}</td>
                    <td className="px-6 py-4">{item.type}</td>
                    <td className="px-6 py-4 font-mono text-emerald-600">{item.phiFilter}</td>
                    <td className="px-6 py-4">{item.auditLog}</td>
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

export default AIPage;
