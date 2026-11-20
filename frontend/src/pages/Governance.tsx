import React, { useCallback, useEffect, useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  Shield,
  ShieldCheck,
  ShieldAlert,
  Gavel,
  Scale,
  FileText,
  CheckCircle2,
  AlertTriangle,
  Info,
  Search,
  Copy,
  Check,
  ExternalLink,
  Clock,
  X,
  RefreshCw,
  Eye,
  Activity,
  Cpu,
  Lock,
  Server,
  ArrowRight,
  Sparkles,
  Plug,
  Settings as SettingsIcon,
} from 'lucide-react';
import {
  getApplicableFrameworks,
  getFrameworkCoverage,
  getGovernanceHealthIndex,
  FrameworkCoverageItem,
  GHIResponse,
} from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { LoadingState, ErrorState } from '../components/readiness/ReadinessStates';
import type { ApplicableFramework } from '../types';
import { DataState, UnavailableState } from '../components/evidence/EvidenceState';
import { ContextualDemoBanner } from '../components/common/ContextualDemoBanner';

export interface GovernanceFramework {
  id: string;
  name: string;
  shortCode: string;
  alignmentFraming: string;
  description: string;
  status: 'aligned' | 'minor_drift' | 'review_needed';
  statusLabel: string;
  score: number;
  coveredControls: number;
  totalControls: number;
  lastScan: string;
  icon: 'nist' | 'ai' | 'cis' | 'soc2' | 'iso' | 'hipaa';
  telemetrySources: string[];
  sampleControls: Array<{
    id: string;
    label: string;
    status: 'verified' | 'drift' | 'unverified';
    evidence: string;
  }>;
}

export interface DriftRow {
  domain: string;
  icon: 'iam' | 'crypto' | 'logs' | 'endpoint' | 'ai' | 'backup';
  baseline: string;
  currentState: string;
  status: 'aligned' | 'drift' | 'review';
  variance: string;
  evidenceHash: string;
  source: string;
}

const CANONICAL_FRAMEWORKS: GovernanceFramework[] = [
  {
    id: 'fw-nist-csf',
    name: 'NIST CSF 2.0',
    shortCode: 'NIST CSF 2.0',
    alignmentFraming: 'Readiness evidence aligned to NIST CSF 2.0',
    description:
      'National Institute of Standards and Technology Cybersecurity Framework 2.0 across Govern, Identify, Protect, Detect, Respond, and Recover functions.',
    status: 'aligned',
    statusLabel: 'Aligned',
    score: 96,
    coveredControls: 104,
    totalControls: 108,
    lastScan: '2 hours ago',
    icon: 'nist',
    telemetrySources: ['Microsoft 365 Graph', 'Veeam Backup', 'CrowdStrike Falcon', 'Wazuh SIEM'],
    sampleControls: [
      { id: 'GV.OC-01', label: 'Organizational Context & Mission Readiness', status: 'verified', evidence: 'Verified via Org Profile & Clinical SLA Registry' },
      { id: 'PR.AA-01', label: 'Identity & Access Management (MFA)', status: 'verified', evidence: '100% conditional access policy enforcement verified' },
      { id: 'DE.CM-01', label: 'Continuous Network & Host Monitoring', status: 'verified', evidence: 'Active EDR telemetry heartbeat on all workstations' },
      { id: 'RC.RP-01', label: 'Incident Recovery Execution & Runbooks', status: 'verified', evidence: '42-minute synthetic RTO test executed successfully' },
    ],
  },
  {
    id: 'fw-nist-ai',
    name: 'NIST AI RMF 1.0',
    shortCode: 'NIST AI RMF',
    alignmentFraming: 'Readiness evidence aligned to NIST AI RMF',
    description:
      'Artificial Intelligence Risk Management Framework covering Govern, Map, Measure, and Manage functions for trustworthy and verifiable AI telemetry.',
    status: 'aligned',
    statusLabel: 'Aligned',
    score: 92,
    coveredControls: 48,
    totalControls: 52,
    lastScan: '3 hours ago',
    icon: 'ai',
    telemetrySources: ['Deterministic Scoring Engine', 'Audit Trail Logger', 'Model Gateway'],
    sampleControls: [
      { id: 'GOVERN-1.1', label: 'AI Safety & Objective Scoring', status: 'verified', evidence: 'Scores calculated on secure backend, immune to client tampering' },
      { id: 'MAP-2.1', label: 'Clinical Disruption Impact Mapping', status: 'verified', evidence: 'Automated triage prioritizing patient care risk' },
      { id: 'MEASURE-3.2', label: 'Explainability & Evidence Grounding', status: 'verified', evidence: 'All executive explanations backed by verified system telemetry' },
    ],
  },
  {
    id: 'fw-cis-v8',
    name: 'CIS Critical Security Controls v8',
    shortCode: 'CIS Controls v8',
    alignmentFraming: 'Readiness evidence aligned to CIS Controls v8',
    description:
      'Implementation Groups 1 & 2 (IG1/IG2) prescriptive cyber defense benchmarks prioritizing asset hygiene, configuration baselines, and data protection.',
    status: 'aligned',
    statusLabel: 'Aligned',
    score: 94,
    coveredControls: 82,
    totalControls: 87,
    lastScan: '1 hour ago',
    icon: 'cis',
    telemetrySources: ['CrowdStrike Falcon', 'M365 Defender', 'AWS Config'],
    sampleControls: [
      { id: 'CIS-01', label: 'Inventory & Control of Enterprise Assets', status: 'verified', evidence: 'Daily host discovery sync via active EDR connectors' },
      { id: 'CIS-04', label: 'Secure Configuration of Enterprise Assets', status: 'verified', evidence: 'Baseline configuration posture benchmarked' },
      { id: 'CIS-10', label: 'Malware Defenses & Automated Remediation', status: 'verified', evidence: '100% active EDR coverage across clinical endpoints' },
    ],
  },
  {
    id: 'fw-soc2',
    name: 'SOC 2 Type II Criteria',
    shortCode: 'SOC 2 Type II',
    alignmentFraming: 'Readiness evidence aligned to SOC 2 Trust Services Criteria',
    description:
      'Continuous control evidence mapped to Security, Availability, Processing Integrity, Confidentiality, and Privacy Trust Services Principles.',
    status: 'aligned',
    statusLabel: 'Aligned',
    score: 98,
    coveredControls: 64,
    totalControls: 65,
    lastScan: '4 hours ago',
    icon: 'soc2',
    telemetrySources: ['AWS S3 Object Lock', 'Veeam Backup', 'Microsoft Entra ID'],
    sampleControls: [
      { id: 'CC6.1', label: 'Logical Access Controls & Perimeter Security', status: 'verified', evidence: 'Multi-factor authentication mandatory for all staff' },
      { id: 'CC7.2', label: 'Security Anomaly Detection & Incident Logging', status: 'verified', evidence: 'Real-time SIEM log ingestion with zero ingestion drops' },
      { id: 'A1.2', label: 'Data Recovery & Infrastructure Availability', status: 'verified', evidence: 'Daily verified backups with air-gap verification' },
    ],
  },
  {
    id: 'fw-iso-27001',
    name: 'ISO/IEC 27001:2022',
    shortCode: 'ISO 27001',
    alignmentFraming: 'Readiness evidence aligned to ISO/IEC 27001:2022',
    description:
      'Information Security Management System (ISMS) requirements and Annex A technical control evidence for healthcare and clinical SaaS environments.',
    status: 'minor_drift',
    statusLabel: 'Minor Drift',
    score: 88,
    coveredControls: 82,
    totalControls: 93,
    lastScan: '30 mins ago',
    icon: 'iso',
    telemetrySources: ['Wazuh SIEM', 'AWS IAM', 'Certificate Manager'],
    sampleControls: [
      { id: 'A.5.15', label: 'Access Control & Privileged Identity', status: 'verified', evidence: 'Role-based access controls mapped across active users' },
      { id: 'A.8.24', label: 'Use of Cryptography & Key Management', status: 'drift', evidence: '3 secondary staging volumes flagged for KMS encryption update' },
      { id: 'A.8.14', label: 'Redundancy of Information Processing', status: 'verified', evidence: 'Dual-site replication and verified snapshot integrity' },
    ],
  },
  {
    id: 'fw-hipaa',
    name: 'HIPAA Security & Privacy Rule',
    shortCode: 'HIPAA',
    alignmentFraming: 'Readiness evidence aligned to HIPAA Safeguards (45 CFR Part 164)',
    description:
      'Automated technical, physical, and administrative safeguards verification for protecting Electronic Protected Health Information (ePHI).',
    status: 'aligned',
    statusLabel: 'Aligned',
    score: 99,
    coveredControls: 42,
    totalControls: 42,
    lastScan: '15 mins ago',
    icon: 'hipaa',
    telemetrySources: ['EHR Database Telemetry', 'Microsoft 365 HIPAA Audit', 'Veeam WORM Backup'],
    sampleControls: [
      { id: '§ 164.312(a)', label: 'Access Control & Unique User Identification', status: 'verified', evidence: '100% staff assigned unique MFA credentials' },
      { id: '§ 164.312(b)', label: 'Audit Controls & ePHI Access Logging', status: 'verified', evidence: 'Immutable audit logs with 365-day retention lock' },
      { id: '§ 164.312(e)', label: 'Transmission Security & TLS 1.3 Encryption', status: 'verified', evidence: 'End-to-end TLS 1.3 encryption on all patient endpoints' },
    ],
  },
];

const CANONICAL_DRIFT_ROWS: DriftRow[] = [
  {
    domain: 'IAM & Multi-Factor Authentication',
    icon: 'iam',
    baseline: 'Strict (MFA Required for 100% accounts)',
    currentState: '100% Enforced via Microsoft 365',
    status: 'aligned',
    variance: '0.0%',
    evidenceHash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    source: 'Microsoft Entra ID Connector',
  },
  {
    domain: 'Data at Rest Encryption (ePHI Volumes)',
    icon: 'crypto',
    baseline: 'AES-256 / KMS Managed Mandatory',
    currentState: '98.8% Encrypted (3 Staging Volumes Pending)',
    status: 'drift',
    variance: '-1.2% (3 Volumes)',
    evidenceHash: 'sha256:9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72',
    source: 'AWS CloudTrail & KMS Audit',
  },
  {
    domain: 'Audit Log Retention & Immutability',
    icon: 'logs',
    baseline: '365 Days Write-Once (WORM) Locked',
    currentState: '365 Days Active on AWS S3 Object Lock',
    status: 'aligned',
    variance: '0.0%',
    evidenceHash: 'sha256:4d1a3b89ef72635489a1c2d3e4f5b6a7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3',
    source: 'Veeam Backup & AWS S3',
  },
  {
    domain: 'Clinical Endpoint Protection & EDR',
    icon: 'endpoint',
    baseline: 'Active Agent on 100% Workstations',
    currentState: '99.4% Active (1 Offline Kiosk)',
    status: 'aligned',
    variance: '-0.6%',
    evidenceHash: 'sha256:88e2a149c719854746f332912448375e1a3d3c457193238a2e58494191d84bcf',
    source: 'CrowdStrike Falcon API',
  },
  {
    domain: 'AI Safety & Deterministic Contract Moat',
    icon: 'ai',
    baseline: 'Zero LLM Hallucinated Scores / Human Oversight',
    currentState: '100% Mathematical Scoring Invariant Enforced',
    status: 'aligned',
    variance: '0.0%',
    evidenceHash: 'sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
    source: 'ResilAI Deterministic Engine',
  },
  {
    domain: 'Automated Disaster Recovery SLAs',
    icon: 'backup',
    baseline: 'RTO < 60 mins / Air-Gap Storage Verified',
    currentState: 'RTO 42 mins Benchmark / Air-Gap Active',
    status: 'aligned',
    variance: '+18 mins margin',
    evidenceHash: 'sha256:fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321',
    source: 'Veeam Synthetic Recovery Engine',
  },
];

/**
 * Governance page.
 *
 * The demo workspace shows the bundled sample walkthrough (`GovernanceDemoView`),
 * tagged "Sample data". A real organisation only ever sees what the backend
 * returned for it (`GovernanceLiveView`), or a plain statement that nothing
 * has been measured yet.
 */
export default function GovernancePage() {
  const { orgId, isDemo, loading } = useActiveOrg();
  if (isDemo) return <GovernanceDemoView orgId={orgId} />;
  if (loading) return <LoadingState message="Loading governance..." />;
  return <GovernanceLiveView orgId={orgId} />;
}

/** Sample walkthrough. Demo workspace only: every figure below is illustrative. */
function GovernanceDemoView({ orgId }: { orgId: string }) {
  const [loading, setLoading] = useState(true);
  const [governanceData, setGovernanceData] = useState<GHIResponse | null>(null);
  const [frameworks, setFrameworks] = useState<GovernanceFramework[]>(CANONICAL_FRAMEWORKS);
  const [driftRows, setDriftRows] = useState<DriftRow[]>(CANONICAL_DRIFT_ROWS);
  const [error, setError] = useState(false);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFramework, setSelectedFramework] = useState<GovernanceFramework | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    async function loadGovernance() {
      try {
        setLoading(true);
        const [ghi, fwResp] = await Promise.all([
          getGovernanceHealthIndex(orgId).catch(() => null),
          getApplicableFrameworks(orgId).catch(() => null),
        ]);

        if (!active) return;
        if (ghi) setGovernanceData(ghi);

        // Merge dynamic frameworks with canonical target set
        if (fwResp && Array.isArray(fwResp.frameworks) && fwResp.frameworks.length > 0) {
          const merged = CANONICAL_FRAMEWORKS.map((canonical) => {
            const match = fwResp.frameworks.find((f: any) =>
              (f.name && (f.name.toLowerCase().includes(canonical.shortCode.toLowerCase()) || canonical.name.toLowerCase().includes(f.name.toLowerCase()))) ||
              (f.id && (f.id.toLowerCase().includes(canonical.id.toLowerCase()) || canonical.id.toLowerCase().includes(f.id.toLowerCase())))
            );
            if (match) {
              return {
                ...canonical,
                score: match.score ?? canonical.score,
                lastScan: match.lastScan ?? canonical.lastScan,
              };
            }
            return canonical;
          });
          setFrameworks(merged);
        } else {
          setFrameworks(CANONICAL_FRAMEWORKS);
        }
      } catch (err) {
        console.error('Failed to load governance data:', err);
        setError(true);
      } finally {
        if (active) setLoading(false);
      }
    }
    loadGovernance();
    return () => {
      active = false;
    };
  }, [orgId]);

  const handleCopyEvidence = (hash: string, domain: string) => {
    try {
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(hash);
      }
    } catch {
      // ignore clipboard error in test environments
    }
    setCopiedHash(hash);
    setToastMessage(`Evidence hash saved to clipboard for ${domain}`);
    setTimeout(() => {
      setCopiedHash(null);
      setToastMessage(null);
    }, 3000);
  };

  const filteredFrameworks = useMemo(() => {
    if (!searchQuery) return frameworks;
    const q = searchQuery.toLowerCase();
    return frameworks.filter(
      (fw) =>
        fw.name.toLowerCase().includes(q) ||
        fw.shortCode.toLowerCase().includes(q) ||
        fw.description.toLowerCase().includes(q) ||
        fw.alignmentFraming.toLowerCase().includes(q)
    );
  }, [frameworks, searchQuery]);

  const overallAlignmentScore = governanceData?.ghi ?? 96;
  const isPostureReady = overallAlignmentScore >= 80;

  return (
    <div className="space-y-8 animate-fade-up max-w-7xl mx-auto pb-16">
      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="governance" />

      {/* Page Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant/30 pb-6">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">
              Governance & Framework Alignment
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-ready-emerald animate-pulse" />
              Continuous Telemetry
            </span>
            <span
              data-testid="sample-data-tag"
              className="px-2 py-0.5 rounded text-[10px] uppercase font-mono font-bold tracking-wider bg-drift-amber/10 text-drift-amber border border-drift-amber/30"
            >
              Sample data
            </span>
          </div>
          <p className="text-sm md:text-base text-on-surface-variant mt-1.5 max-w-3xl">
            Executive summary of technical evidence mapping, regulatory alignment baselines, and real-time policy drift tracking.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search frameworks..."
              className="bg-surface-container-low border border-outline-variant/40 rounded-xl pl-9 pr-3 py-2 text-xs text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-ready-emerald transition-all w-52 sm:w-64"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Toast Feedback */}
      {toastMessage && (
        <div className="p-4 bg-surface-container-high border border-ready-emerald/40 rounded-xl text-on-surface text-xs flex items-center justify-between animate-in fade-in shadow-lg shadow-black/20">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-ready-emerald" />
            <span className="font-semibold">{toastMessage}</span>
          </div>
          <button onClick={() => setToastMessage(null)} className="text-on-surface-variant hover:text-on-surface">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Mandatory Non-Certification Disclaimer Banner */}
      <aside
        aria-label="Framework Alignment Disclaimer"
        className="rounded-xl bg-surface-container-low border border-outline-variant/40 p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm"
      >
        <div className="flex items-start gap-3.5">
          <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0 mt-0.5">
            <Info className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-xs font-bold font-mono uppercase tracking-wider text-on-surface flex items-center gap-2">
              <span>Readiness Evidence Mapping Disclaimer</span>
              <span className="px-2 py-0.5 rounded bg-surface-container text-[10px] text-on-surface-variant border border-outline-variant/30">
                Audit Safe
              </span>
            </h2>
            <p className="text-xs text-on-surface-variant mt-1 leading-relaxed max-w-4xl">
              ResilAI provides continuous technical readiness verification and telemetry mapping against regulatory and cybersecurity standards. Framework status is explicitly framed as <strong>&ldquo;Readiness evidence aligned to...&rdquo;</strong> and does not constitute formal certification, attestation, or third-party audit sign-off.
            </p>
          </div>
        </div>
        <div className="shrink-0 self-end sm:self-center">
          <span className="text-[11px] font-mono text-ready-emerald flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4" />
            <span>Cryptographically Bound</span>
          </span>
        </div>
      </aside>

      {/* Overview Alignment Banner */}
      <section className="bg-surface-container-low border border-outline-variant/60 rounded-2xl p-6 md:p-8 flex flex-col lg:flex-row gap-8 items-start lg:items-center justify-between shadow-sm relative overflow-hidden">
        <div className="flex-1 space-y-3 relative z-10">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-ready-emerald">
            <Sparkles className="w-4 h-4" />
            <span>Continuous Governance Health</span>
          </div>

          <h2 className="text-xl md:text-2xl font-bold text-on-surface leading-tight">
            Overall compliance posture is currently{' '}
            <span className={isPostureReady ? 'text-ready-emerald' : 'text-drift-amber'}>
              {isPostureReady ? 'Aligned & Monitored' : 'Review Required'}
            </span>
            .
          </h2>

          <p className="text-xs md:text-sm text-on-surface-variant leading-relaxed max-w-3xl">
            Readiness evidence shows core frameworks (NIST CSF 2.0, HIPAA, SOC 2) remain firmly within monitored operational tolerances. Continuous verification engines continuously check configuration drift against baseline telemetry harvested from active connectors.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-4 text-xs font-mono text-on-surface-variant">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-ready-emerald" /> 6 Frameworks Evaluated
            </span>
            <span className="flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-ready-emerald" /> Last Scan: Continuous Heartbeat
            </span>
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-ready-emerald" /> Zero Critical Breaches
            </span>
          </div>
        </div>

        <div className="shrink-0 flex flex-col items-center justify-center p-6 bg-surface-container rounded-2xl border border-outline-variant/60 min-w-[200px] text-center shadow-lg relative z-10">
          <span className="text-5xl font-bold tracking-tight text-ready-emerald font-mono">
            {overallAlignmentScore}%
          </span>
          <span className="text-xs font-mono uppercase tracking-widest text-on-surface-variant mt-2 font-semibold">
            Alignment Score
          </span>
          <span className="text-[10px] font-mono text-on-surface-variant mt-1">
            424 / 447 Controls Verified
          </span>
        </div>
      </section>

      {/* Target Frameworks Bento Grid */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
            <Gavel className="w-5 h-5 text-ready-emerald" />
            <span>Target Regulatory & Security Frameworks</span>
          </h2>
          <span className="text-xs font-mono text-on-surface-variant">
            {filteredFrameworks.length} frameworks active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredFrameworks.map((fw) => {
            const isAligned = fw.status === 'aligned';
            return (
              <div
                key={fw.id}
                onClick={() => setSelectedFramework(fw)}
                className="bg-surface-container-low border border-outline-variant/60 hover:border-ready-emerald/50 rounded-2xl p-6 flex flex-col justify-between hover:shadow-xl hover:shadow-black/25 hover:-translate-y-0.5 transition-all duration-300 group cursor-pointer relative overflow-hidden"
              >
                <div
                  className={`absolute right-0 top-0 w-28 h-28 rounded-full -mr-14 -mt-14 transition-transform group-hover:scale-150 duration-500 pointer-events-none ${
                    isAligned ? 'bg-ready-emerald/5' : 'bg-drift-amber/5'
                  }`}
                />

                <div className="space-y-4">
                  {/* Top Bar: Icon + Status Badge */}
                  <div className="flex justify-between items-start">
                    <div
                      className={`p-3 rounded-xl border ${
                        isAligned
                          ? 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/20'
                          : 'bg-drift-amber/10 text-drift-amber border-drift-amber/20'
                      }`}
                    >
                      {fw.icon === 'nist' && <ShieldCheck className="w-6 h-6" />}
                      {fw.icon === 'ai' && <Cpu className="w-6 h-6" />}
                      {fw.icon === 'cis' && <Shield className="w-6 h-6" />}
                      {fw.icon === 'soc2' && <Scale className="w-6 h-6" />}
                      {fw.icon === 'iso' && <FileText className="w-6 h-6" />}
                      {fw.icon === 'hipaa' && <Gavel className="w-6 h-6" />}
                    </div>

                    <span
                      className={`px-3 py-1 text-xs font-mono font-bold rounded-full border ${
                        isAligned
                          ? 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/30'
                          : 'bg-drift-amber/10 text-drift-amber border-drift-amber/30'
                      }`}
                    >
                      {fw.statusLabel}
                    </span>
                  </div>

                  {/* Title & Framing */}
                  <div>
                    <h3 className="text-base font-bold text-on-surface group-hover:text-ready-emerald transition-colors">
                      {fw.name}
                    </h3>
                    <p className="text-[11px] font-mono text-ready-emerald/90 mt-0.5 font-semibold">
                      {fw.alignmentFraming}
                    </p>
                    <p className="text-xs text-on-surface-variant leading-relaxed mt-2 line-clamp-2">
                      {fw.description}
                    </p>
                  </div>
                </div>

                {/* Bottom Metadata */}
                <div className="mt-6 pt-4 border-t border-outline-variant/60 flex items-center justify-between text-xs">
                  <div className="space-y-0.5">
                    <span className="font-mono text-[11px] text-on-surface-variant block">
                      Last Scan: {fw.lastScan}
                    </span>
                    <span className="font-mono text-[11px] text-on-surface-variant block">
                      {fw.coveredControls}/{fw.totalControls} Controls Verified
                    </span>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-bold font-mono text-ready-emerald block">
                      {fw.score}%
                    </span>
                    <button className="text-ready-emerald hover:underline text-[11px] font-semibold flex items-center gap-0.5 justify-end">
                      <span>Details</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Compliance Drift Tracking Table */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
            <Activity className="w-5 h-5 text-ready-emerald" />
            <span>Compliance Drift Tracking & Technical Telemetry</span>
          </h2>
          <span className="text-xs font-mono text-on-surface-variant">
            Continuous Baseline Comparison
          </span>
        </div>

        <div className="bg-surface-container-low border border-outline-variant/60 rounded-2xl overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-surface-container border-b border-outline-variant/60 text-xs font-mono uppercase text-on-surface-variant">
                  <th className="py-4 px-6">Policy Domain</th>
                  <th className="py-4 px-6">Required Baseline</th>
                  <th className="py-4 px-6">Current Telemetry State</th>
                  <th className="py-4 px-6">Variance</th>
                  <th className="py-4 px-6 text-right">Evidence Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-outline-variant/40">
                {driftRows.map((drift, i) => (
                  <tr key={i} className="hover:bg-surface-container/40 transition-colors group">
                    <td className="py-4 px-6 font-medium text-on-surface">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-surface-container border border-outline-variant/30 text-on-surface-variant group-hover:text-ready-emerald transition-colors">
                          {drift.icon === 'iam' && <Lock className="w-4 h-4" />}
                          {drift.icon === 'crypto' && <ShieldCheck className="w-4 h-4" />}
                          {drift.icon === 'logs' && <FileText className="w-4 h-4" />}
                          {drift.icon === 'endpoint' && <Server className="w-4 h-4" />}
                          {drift.icon === 'ai' && <Cpu className="w-4 h-4" />}
                          {drift.icon === 'backup' && <Activity className="w-4 h-4" />}
                        </div>
                        <div>
                          <span className="font-bold text-on-surface block">{drift.domain}</span>
                          <span className="text-[10px] font-mono text-on-surface-variant block">{drift.source}</span>
                        </div>
                      </div>
                    </td>

                    <td className="py-4 px-6 text-on-surface-variant font-mono text-xs">
                      {drift.baseline}
                    </td>

                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-bold ${
                          drift.status === 'aligned'
                            ? 'bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30'
                            : 'bg-drift-amber/10 text-drift-amber border border-drift-amber/30'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            drift.status === 'aligned' ? 'bg-ready-emerald' : 'bg-drift-amber'
                          }`}
                        />
                        {drift.currentState}
                      </span>
                    </td>

                    <td className="py-4 px-6 font-mono text-xs">
                      <span
                        className={drift.status === 'aligned' ? 'text-on-surface-variant' : 'text-drift-amber font-semibold'}
                      >
                        {drift.variance}
                      </span>
                    </td>

                    <td className="py-4 px-6 text-right">
                      <button
                        onClick={() => handleCopyEvidence(drift.evidenceHash, drift.domain)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-surface-container hover:bg-surface-container-high border border-outline-variant/40 text-ready-emerald hover:text-white transition-all text-xs font-semibold"
                        title="Copy SHA-256 evidence hash"
                      >
                        {copiedHash === drift.evidenceHash ? (
                          <>
                            <Check className="w-3.5 h-3.5 text-ready-emerald" />
                            <span>Copied</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-3.5 h-3.5" />
                            <span>Copy Evidence</span>
                          </>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Framework Detail Modal */}
      {selectedFramework && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in"
          onClick={() => setSelectedFramework(null)}
        >
          <div
            className="bg-surface-container-low border border-outline-variant/60 rounded-2xl max-w-3xl w-full p-6 md:p-8 space-y-6 shadow-2xl animate-in zoom-in-95 max-h-[90vh] overflow-y-auto"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-start justify-between border-b border-outline-variant/60 pb-5">
              <div className="flex items-center gap-3.5">
                <div className="p-3 bg-ready-emerald/10 text-ready-emerald rounded-xl border border-ready-emerald/30">
                  <Gavel className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-on-surface">{selectedFramework.name}</h3>
                  <p className="text-xs font-mono text-ready-emerald font-semibold mt-0.5">
                    {selectedFramework.alignmentFraming}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedFramework(null)}
                className="p-1.5 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="space-y-6 text-xs text-on-surface leading-relaxed">
              <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 space-y-2">
                <h4 className="font-bold text-on-surface text-xs uppercase tracking-wider">Framework Overview</h4>
                <p className="text-on-surface-variant">{selectedFramework.description}</p>
              </div>

              {/* Status and Metrics Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/50">
                  <span className="text-[10px] font-mono uppercase text-on-surface-variant block">Alignment Score</span>
                  <span className="text-2xl font-bold font-mono text-ready-emerald mt-1 block">
                    {selectedFramework.score}%
                  </span>
                </div>
                <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/50">
                  <span className="text-[10px] font-mono uppercase text-on-surface-variant block">Verified Controls</span>
                  <span className="text-xl font-bold text-on-surface mt-1 block">
                    {selectedFramework.coveredControls} / {selectedFramework.totalControls}
                  </span>
                </div>
                <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/50">
                  <span className="text-[10px] font-mono uppercase text-on-surface-variant block">Last Automated Scan</span>
                  <span className="text-xs font-mono font-semibold text-on-surface mt-2 block">
                    {selectedFramework.lastScan}
                  </span>
                </div>
              </div>

              {/* Telemetry Sources */}
              <div>
                <h4 className="text-xs font-mono uppercase text-on-surface-variant mb-2">
                  Connected Telemetry Probes
                </h4>
                <div className="flex flex-wrap gap-2">
                  {selectedFramework.telemetrySources.map((source, i) => (
                    <span
                      key={i}
                      className="px-3 py-1 bg-surface-container rounded-lg border border-outline-variant/40 text-on-surface text-xs font-medium flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5 text-ready-emerald" />
                      {source}
                    </span>
                  ))}
                </div>
              </div>

              {/* Sample Verified Controls */}
              <div className="space-y-3">
                <h4 className="text-xs font-mono uppercase text-on-surface-variant">
                  Sample Mapped Controls & Telemetry Proofs
                </h4>
                <div className="divide-y divide-outline-variant/40 border border-outline-variant/60 rounded-xl overflow-hidden bg-surface-container/50">
                  {selectedFramework.sampleControls.map((ctl) => (
                    <div key={ctl.id} className="p-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-2 hover:bg-surface-container transition-colors">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 bg-surface-container-high rounded text-[10px] font-mono font-bold text-on-surface border border-outline-variant/30">
                            {ctl.id}
                          </span>
                          <span className="text-xs font-bold text-on-surface">{ctl.label}</span>
                        </div>
                        <p className="text-[11px] text-on-surface-variant mt-1">{ctl.evidence}</p>
                      </div>
                      <span
                        className={`px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase self-start sm:self-auto ${
                          ctl.status === 'verified'
                            ? 'bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30'
                            : 'bg-drift-amber/10 text-drift-amber border border-drift-amber/30'
                        }`}
                      >
                        {ctl.status}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Non-Certification Reminder */}
              <div className="p-3.5 bg-blue-500/10 border border-blue-500/20 rounded-xl text-[11px] text-on-surface-variant leading-relaxed flex items-start gap-2.5">
                <Info className="w-4 h-4 text-blue-400 shrink-0 mt-0.5" />
                <span>
                  Reminder: This mapping reflects continuous operational readiness telemetry harvested by ResilAI and does not replace official accreditation, independent CPA audit reports, or regulatory filings.
                </span>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="pt-4 border-t border-outline-variant/60 flex items-center justify-between text-xs font-mono text-on-surface-variant">
              <span>All evidence verified by ResilAI Deterministic Moat</span>
              <button
                onClick={() => setSelectedFramework(null)}
                className="px-5 py-2 bg-ready-emerald text-slate-950 font-bold rounded-xl text-xs hover:brightness-110 shadow-sm"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Live view: a real organisation                                              */
/* -------------------------------------------------------------------------- */

interface LiveGovernance {
  ghi: GHIResponse | null;
  frameworks: ApplicableFramework[];
  coverage: FrameworkCoverageItem[];
  /** True when at least one of the three requests failed. */
  partial: boolean;
}

const EMPTY_LIVE_GOVERNANCE: LiveGovernance = { ghi: null, frameworks: [], coverage: [], partial: false };

const finiteNumber = (value: unknown): number | null =>
  typeof value === 'number' && Number.isFinite(value) ? value : null;

const normaliseFrameworkName = (name: string) => name.toLowerCase().replace(/[^a-z0-9]/g, '');

/** "NIST_AI_RMF" (coverage API) and "NIST AI RMF" (applicability API) are the same framework. */
function coverageFor(name: string, coverage: FrameworkCoverageItem[]): FrameworkCoverageItem | undefined {
  const key = normaliseFrameworkName(name);
  if (!key) return undefined;
  return coverage.find((item) => {
    const candidate = normaliseFrameworkName(item.framework);
    return candidate.length >= 4 && (candidate === key || key.startsWith(candidate));
  });
}

interface MeasuredGhi {
  value: number;
  grade: string | null;
  passed: boolean | null;
  /** What the backend says the index was calculated from. */
  inputs: string[];
  issues: string[];
}

/**
 * Read the governance health index out of `GET /api/governance/{org}/health-index`.
 * Returns null when the backend sent no index, or when its own breakdown says
 * nothing stands behind the number (no findings, no tracked components, no
 * service-level tier, no applicable framework): the formula then returns its
 * starting value, which is not a measurement of this organisation.
 */
function readGhi(ghi: GHIResponse | null): MeasuredGhi | null {
  const value = finiteNumber(ghi?.ghi);
  if (!ghi || value === null) return null;

  const openFindings = finiteNumber(ghi.audit_readiness?.total_open);
  const components = finiteNumber(ghi.lifecycle?.total_components);
  const frameworks = finiteNumber(ghi.compliance?.total_frameworks);
  const slaStatus = typeof ghi.sla?.status === 'string' ? ghi.sla.status : null;

  if (openFindings === 0 && components === 0 && frameworks === 0 && slaStatus === 'not_configured') {
    return null;
  }

  const inputs: string[] = [];
  if (openFindings !== null) inputs.push(`${openFindings} open finding${openFindings === 1 ? '' : 's'}`);
  if (components !== null) inputs.push(`${components} tracked technology component${components === 1 ? '' : 's'}`);
  if (slaStatus !== null) {
    inputs.push(slaStatus === 'not_configured' ? 'no service-level tier set' : `service-level status "${slaStatus.replace(/_/g, ' ')}"`);
  }
  if (frameworks !== null) inputs.push(`${frameworks} applicable framework${frameworks === 1 ? '' : 's'}`);

  return {
    value,
    grade: typeof ghi.grade === 'string' && ghi.grade.trim() ? ghi.grade.trim() : null,
    passed: typeof ghi.passed === 'boolean' ? ghi.passed : null,
    inputs,
    issues: Array.isArray(ghi.issues) ? ghi.issues.filter((issue) => typeof issue === 'string' && issue.trim()) : [],
  };
}

function GovernanceLiveView({ orgId }: { orgId: string }) {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [data, setData] = useState<LiveGovernance>(EMPTY_LIVE_GOVERNANCE);
  const [searchQuery, setSearchQuery] = useState('');
  const [reloadKey, setReloadKey] = useState(0);

  const reload = useCallback(() => setReloadKey((key) => key + 1), []);

  useEffect(() => {
    let active = true;

    if (!orgId) {
      setData(EMPTY_LIVE_GOVERNANCE);
      setStatus('ready');
      return;
    }

    setStatus('loading');
    (async () => {
      const [ghiResult, frameworksResult, coverageResult] = await Promise.allSettled([
        Promise.resolve().then(() => getGovernanceHealthIndex(orgId)),
        Promise.resolve().then(() => getApplicableFrameworks(orgId)),
        Promise.resolve().then(() => getFrameworkCoverage(orgId)),
      ]);
      if (!active) return;

      const failures = [ghiResult, frameworksResult, coverageResult].filter((r) => r.status === 'rejected').length;
      if (failures === 3) {
        setStatus('error');
        return;
      }

      const ghi = ghiResult.status === 'fulfilled' && ghiResult.value ? ghiResult.value : null;

      const rawFrameworks = frameworksResult.status === 'fulfilled' ? frameworksResult.value?.frameworks : null;
      const frameworks = Array.isArray(rawFrameworks)
        ? rawFrameworks.filter((f) => f && typeof f.framework === 'string' && f.framework.trim())
        : [];

      const rawCoverage = coverageResult.status === 'fulfilled' ? coverageResult.value : null;
      const coverage = Array.isArray(rawCoverage)
        ? rawCoverage.filter(
            (c) =>
              c &&
              typeof c.framework === 'string' &&
              c.framework.trim() &&
              finiteNumber(c.covered_controls) !== null &&
              finiteNumber(c.total_controls) !== null &&
              finiteNumber(c.coverage_percent) !== null
          )
        : [];

      setData({ ghi, frameworks, coverage, partial: failures > 0 });
      setStatus('ready');
    })();

    return () => {
      active = false;
    };
  }, [orgId, reloadKey]);

  const measured = useMemo(() => readGhi(data.ghi), [data.ghi]);

  // Frameworks the backend says apply, each with its coverage row if one exists.
  // Coverage rows for a framework that is not in the applicability list are
  // shown only when the backend tracked at least one control for it.
  const cards = useMemo(() => {
    const applicable = data.frameworks.map((fw) => ({
      key: `applicable-${fw.framework}`,
      name: fw.framework,
      reason: typeof fw.reason === 'string' ? fw.reason : '',
      mandatory: typeof fw.mandatory === 'boolean' ? fw.mandatory : null,
      referenceUrl:
        typeof fw.reference_url === 'string' && fw.reference_url.startsWith('https://') ? fw.reference_url : null,
      coverage: coverageFor(fw.framework, data.coverage) ?? null,
    }));
    const used = new Set(applicable.map((card) => card.coverage).filter(Boolean));
    const tracked = data.coverage
      .filter((item) => !used.has(item) && item.covered_controls > 0)
      .map((item) => ({
        key: `tracked-${item.framework}`,
        name: item.framework.replace(/_/g, ' '),
        reason: '',
        mandatory: null as boolean | null,
        referenceUrl: null as string | null,
        coverage: item as FrameworkCoverageItem | null,
      }));
    return [...applicable, ...tracked];
  }, [data.frameworks, data.coverage]);

  const filteredCards = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return cards;
    return cards.filter((card) => card.name.toLowerCase().includes(q) || card.reason.toLowerCase().includes(q));
  }, [cards, searchQuery]);

  if (status === 'loading') return <LoadingState message="Loading governance..." />;
  if (status === 'error') {
    return (
      <ErrorState
        error="We could not load governance data for your organisation. Please try again."
        onRetry={reload}
      />
    );
  }

  const scoreTone = measured?.passed === false ? 'text-drift-amber' : 'text-ready-emerald';
  const displayValue = measured ? (Number.isInteger(measured.value) ? String(measured.value) : measured.value.toFixed(1)) : null;

  return (
    <div className="space-y-8 animate-fade-up max-w-7xl mx-auto pb-16" data-testid="governance-live">
      {/* Page Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant/30 pb-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">
            Governance & Framework Alignment
          </h1>
          <p className="text-sm md:text-base text-on-surface-variant mt-1.5 max-w-3xl">
            Which frameworks apply to your organisation, and what ResilAI has measured for it so far.
          </p>
        </div>

        {cards.length > 0 && (
          <div className="flex items-center gap-3 shrink-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search frameworks..."
                className="bg-surface-container-low border border-outline-variant/40 rounded-xl pl-9 pr-3 py-2 text-xs text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-ready-emerald transition-all w-52 sm:w-64"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  aria-label="Clear search"
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>
        )}
      </header>

      {data.partial && (
        <div
          role="status"
          data-testid="governance-partial-notice"
          className="p-4 bg-surface-container-low border border-drift-amber/30 rounded-xl text-xs text-on-surface flex items-center justify-between gap-4"
        >
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-drift-amber shrink-0" />
            <span>Some governance data could not be loaded, so this page may be incomplete.</span>
          </div>
          <button
            onClick={reload}
            className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-lg border border-outline-variant/50 flex items-center gap-1.5 shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try again</span>
          </button>
        </div>
      )}

      {/* Non-Certification Disclaimer */}
      <aside
        aria-label="Framework Alignment Disclaimer"
        className="rounded-xl bg-surface-container-low border border-outline-variant/40 p-4 sm:p-5 flex items-start gap-3.5 shadow-sm"
      >
        <div className="p-2.5 rounded-xl bg-blue-500/10 border border-blue-500/20 text-blue-400 shrink-0 mt-0.5">
          <Info className="w-5 h-5" />
        </div>
        <div>
          <h2 className="text-xs font-bold font-mono uppercase tracking-wider text-on-surface">
            Readiness Evidence Mapping Disclaimer
          </h2>
          <p className="text-xs text-on-surface-variant mt-1 leading-relaxed max-w-4xl">
            Framework information on this page is readiness evidence. It does not constitute formal certification,
            attestation, or third-party audit sign-off.
          </p>
        </div>
      </aside>

      {/* Governance Health */}
      <section className="bg-surface-container-low border border-outline-variant/60 rounded-2xl p-6 md:p-8 flex flex-col lg:flex-row gap-8 items-start lg:items-center justify-between shadow-sm relative overflow-hidden">
        <div className="flex-1 space-y-3 relative z-10">
          <div className="flex items-center gap-2 text-xs font-mono font-bold uppercase text-on-surface-variant">
            <Activity className="w-4 h-4" />
            <span>Governance Health</span>
          </div>

          {measured ? (
            <>
              <h2 className="text-xl md:text-2xl font-bold text-on-surface leading-tight">
                Governance health index: <span className={scoreTone}>{displayValue} out of 100</span>
                {measured.grade ? `, grade ${measured.grade}` : ''}.
              </h2>
              {measured.inputs.length > 0 && (
                <p className="text-xs md:text-sm text-on-surface-variant leading-relaxed max-w-3xl">
                  Calculated by ResilAI from {measured.inputs.join(', ')}.
                </p>
              )}
              {measured.issues.length > 0 && (
                <ul className="pt-1 space-y-1.5 text-xs text-on-surface-variant max-w-3xl">
                  {measured.issues.map((issue, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <AlertTriangle className="w-3.5 h-3.5 text-drift-amber shrink-0 mt-0.5" />
                      <span>{issue}</span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          ) : (
            <>
              <h2 className="text-xl md:text-2xl font-bold text-on-surface leading-tight">
                Governance health has not been measured yet.
              </h2>
              <p className="text-xs md:text-sm text-on-surface-variant leading-relaxed max-w-3xl">
                ResilAI calculates this from your organisation profile, your assessment findings and the technology
                it can see. Complete the organisation profile and connect a system, and the index appears here.
              </p>
            </>
          )}
        </div>

        <div className="shrink-0 flex flex-col items-center justify-center p-6 bg-surface-container rounded-2xl border border-outline-variant/60 min-w-[200px] text-center shadow-lg relative z-10">
          {measured ? (
            <span className={`text-5xl font-bold tracking-tight font-mono ${scoreTone}`} data-testid="governance-ghi-value">
              {displayValue}
            </span>
          ) : (
            <span className="text-lg font-bold text-on-surface-variant" data-testid="governance-ghi-not-measured">
              Not measured yet
            </span>
          )}
          <span className="text-xs font-mono uppercase tracking-widest text-on-surface-variant mt-2 font-semibold">
            Governance Health Index
          </span>
          {measured?.grade && (
            <span className="text-[10px] font-mono text-on-surface-variant mt-1">Grade {measured.grade}</span>
          )}
        </div>
      </section>

      {/* Applicable Frameworks */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
            <Gavel className="w-5 h-5 text-ready-emerald" />
            <span>Frameworks That Apply to Your Organisation</span>
          </h2>
          {cards.length > 0 && (
            <span className="text-xs font-mono text-on-surface-variant">
              {filteredCards.length} of {cards.length} shown
            </span>
          )}
        </div>

        {cards.length === 0 ? (
          <div
            data-testid="governance-empty-state"
            className="p-8 rounded-xl bg-surface-container-low border border-dashed border-surface-bright flex flex-col items-center justify-center text-center"
          >
            <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
              <Gavel className="w-6 h-6" />
            </div>
            <h3 className="text-base font-semibold text-on-surface">No frameworks to show yet.</h3>
            <p className="text-xs text-on-surface-variant max-w-md mt-1 leading-relaxed">
              ResilAI works out which frameworks apply from your organisation profile: the kind of data you handle
              and the sector you work in. Complete the profile in Settings, then connect a system so there is
              evidence to measure against them.
            </p>
            <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
              <Link
                to="/settings"
                className="inline-flex items-center gap-2 px-6 py-3 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl transition-all active:scale-[0.98]"
              >
                <SettingsIcon className="w-4 h-4" />
                <span>Complete organisation profile</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/connectors"
                className="inline-flex items-center gap-2 px-5 py-3 bg-surface-container hover:bg-surface-container-high border border-outline-variant/60 text-on-surface text-sm font-semibold rounded-xl transition-all active:scale-[0.98]"
              >
                <Plug className="w-4 h-4" />
                <span>Connect a system</span>
              </Link>
            </div>
          </div>
        ) : filteredCards.length === 0 ? (
          <p className="text-xs text-on-surface-variant">No framework matches your search.</p>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredCards.map((card) => (
              <div
                key={card.key}
                data-testid="governance-framework-card"
                className="bg-surface-container-low border border-outline-variant/60 rounded-2xl p-6 flex flex-col justify-between"
              >
                <div className="space-y-4">
                  <div className="flex justify-between items-start gap-3">
                    <div className="p-3 rounded-xl border bg-surface-container text-on-surface-variant border-outline-variant/40">
                      <Gavel className="w-6 h-6" />
                    </div>
                    {card.mandatory !== null && (
                      <span
                        className={`px-3 py-1 text-xs font-mono font-bold rounded-full border ${
                          card.mandatory
                            ? 'bg-drift-amber/10 text-drift-amber border-drift-amber/30'
                            : 'bg-surface-container text-on-surface-variant border-outline-variant/40'
                        }`}
                      >
                        {card.mandatory ? 'Mandatory' : 'Recommended'}
                      </span>
                    )}
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-on-surface">{card.name}</h3>
                    {card.reason && (
                      <p className="text-xs text-on-surface-variant leading-relaxed mt-2">{card.reason}</p>
                    )}
                    {card.referenceUrl && (
                      <a
                        href={card.referenceUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-ready-emerald hover:underline"
                      >
                        <span>Official reference</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>

                <div className="mt-6 pt-4 border-t border-outline-variant/60 text-xs">
                  {card.coverage ? (
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-mono text-[11px] text-on-surface-variant">
                        {card.coverage.covered_controls} of {card.coverage.total_controls} controls tracked
                      </span>
                      <span className="text-sm font-bold font-mono text-on-surface">
                        {card.coverage.coverage_percent}% coverage
                      </span>
                    </div>
                  ) : (
                    <span className="font-mono text-[11px] text-on-surface-variant">Coverage not measured yet</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
