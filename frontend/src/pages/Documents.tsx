import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Download,
  Share2,
  Search,
  Upload,
  ShieldCheck,
  ShieldAlert,
  Folder,
  FolderCheck,
  Server,
  HardDriveDownload,
  History,
  FileSpreadsheet,
  FileCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  X,
  Copy,
  Check,
  Filter,
  Sparkles,
  RefreshCw,
  Lock,
  ChevronRight,
  Info,
  MoreVertical,
  ExternalLink,
  FileCode,
  Plug,
} from 'lucide-react';
import {
  downloadBoardStoryPdf,
  getEvidencePackages,
  getEvidenceLedger,
  getReports,
  downloadReportById,
  EvidenceLedgerItem,
} from '../api';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { LoadingState, ErrorState } from '../components/readiness/ReadinessStates';
import type { BackendReport } from '../types/reports';
import { ContextualDemoBanner } from '../components/common/ContextualDemoBanner';

interface AuditFolder {
  id: string;
  name: string;
  category: string;
  status: 'verified' | 'current' | 'review_needed';
  statusLabel: string;
  fileCount: number;
  icon: 'hipaa' | 'policy' | 'config' | 'recovery';
  description: string;
  files: Array<{
    id: string;
    name: string;
    type: 'pdf' | 'json' | 'csv';
    size: string;
    hash: string;
    verifiedAt: string;
    status: 'verified' | 'review_needed';
  }>;
}

interface RecentReport {
  id: string;
  title: string;
  category: 'board' | 'soc2' | 'audit' | 'operations' | 'recovery';
  format: 'pdf' | 'csv' | 'json';
  generatedAt: string;
  size: string;
  status: 'verified' | 'generating' | 'ready';
  description: string;
  downloadHandler?: () => void;
}

interface ExecutiveSummaryItem {
  id: string;
  period: string;
  status: 'stable' | 'updated' | 'verified';
  headline: string;
  narrative: string;
  impact: string;
  safeguardsPassed: number;
  totalSafeguards: number;
  lastVerified: string;
}

const AUDIT_FOLDERS: AuditFolder[] = [
  {
    id: 'folder-hipaa',
    name: 'HIPAA Safeguards Package',
    category: 'Regulatory Safeguards',
    status: 'verified',
    statusLabel: 'Verified',
    fileCount: 42,
    icon: 'hipaa',
    description: 'Technical, administrative, and physical safeguard evidence logs for ePHI protection.',
    files: [
      {
        id: 'f-hipaa-1',
        name: 'ePHI_Access_Audit_Log_Q3.csv',
        type: 'csv',
        size: '1.4 MB',
        hash: 'sha256:7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
        verifiedAt: '2 hours ago',
        status: 'verified',
      },
      {
        id: 'f-hipaa-2',
        name: 'BAA_Registry_Vendor_Signoffs.pdf',
        type: 'pdf',
        size: '840 KB',
        hash: 'sha256:3a4b9c812d4e5f67a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1',
        verifiedAt: '1 day ago',
        status: 'verified',
      },
      {
        id: 'f-hipaa-3',
        name: 'Database_Encryption_At_Rest_Audit.json',
        type: 'json',
        size: '420 KB',
        hash: 'sha256:9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72',
        verifiedAt: '4 hours ago',
        status: 'verified',
      },
    ],
  },
  {
    id: 'folder-policy',
    name: 'Policy Guidelines',
    category: 'Governance Documentation',
    status: 'current',
    statusLabel: 'Current',
    fileCount: 18,
    icon: 'policy',
    description: 'Active disaster recovery runbooks, access control policies, and incident response matrices.',
    files: [
      {
        id: 'f-pol-1',
        name: 'Incident_Response_Plan_v4.2.pdf',
        type: 'pdf',
        size: '2.1 MB',
        hash: 'sha256:88e2a149c719854746f332912448375e1a3d3c457193238a2e58494191d84bcf',
        verifiedAt: '3 days ago',
        status: 'verified',
      },
      {
        id: 'f-pol-2',
        name: 'Clinical_Staff_Access_Control_Matrix.pdf',
        type: 'pdf',
        size: '1.2 MB',
        hash: 'sha256:4d1a3b89ef72635489a1c2d3e4f5b6a7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3',
        verifiedAt: '5 days ago',
        status: 'verified',
      },
    ],
  },
  {
    id: 'folder-config',
    name: 'System Configs',
    category: 'Technical Infrastructure',
    status: 'review_needed',
    statusLabel: 'Review Needed',
    fileCount: 7,
    icon: 'config',
    description: 'Firewall snapshots, MFA enforcement configurations, and staging cluster drift logs.',
    files: [
      {
        id: 'f-cfg-1',
        name: 'Firewall_Rule_Drift_Snapshot.json',
        type: 'json',
        size: '640 KB',
        hash: 'sha256:1234a567b890c123d456e789f012a345b678c901d234e567f890a123b456c789',
        verifiedAt: '30 mins ago',
        status: 'review_needed',
      },
      {
        id: 'f-cfg-2',
        name: 'M365_Conditional_Access_Baseline.json',
        type: 'json',
        size: '310 KB',
        hash: 'sha256:abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890',
        verifiedAt: '1 hour ago',
        status: 'verified',
      },
    ],
  },
  {
    id: 'folder-recovery',
    name: 'Recovery Playbooks',
    category: 'Disaster Recovery',
    status: 'verified',
    statusLabel: 'Verified',
    fileCount: 12,
    icon: 'recovery',
    description: 'Automated failover guides, air-gapped backup attestation, and recovery time SLA logs.',
    files: [
      {
        id: 'f-rec-1',
        name: 'EHR_Epic_Failover_Validation_Report.pdf',
        type: 'pdf',
        size: '1.9 MB',
        hash: 'sha256:5678c901d234e567f890a123b456c789abcdef1234567890abcdef1234567890',
        verifiedAt: '6 hours ago',
        status: 'verified',
      },
      {
        id: 'f-rec-2',
        name: 'Veeam_Immutable_Storage_Lock_Audit.json',
        type: 'json',
        size: '520 KB',
        hash: 'sha256:fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321',
        verifiedAt: '3 hours ago',
        status: 'verified',
      },
    ],
  },
];

const EXECUTIVE_SUMMARIES: ExecutiveSummaryItem[] = [
  {
    id: 'sum-hipaa',
    period: 'Current Review Cycle',
    status: 'stable',
    headline: 'HIPAA Compliance Stance remains stable.',
    narrative:
      'All automated technical safeguards passed verification. Identity provider configurations are secure, and MFA enforcement is active for 100% of clinical and administrative accounts. No unencrypted ePHI storage volumes detected in primary clusters.',
    impact:
      'Zero regulatory exposure detected for patient records or clinical messaging systems. Continuous audit logs satisfy HHS OCR documentation requirements.',
    safeguardsPassed: 42,
    totalSafeguards: 42,
    lastVerified: 'Today at 08:30 UTC',
  },
  {
    id: 'sum-vendor',
    period: 'Active Drift Review',
    status: 'updated',
    headline: 'Vendor Risk Assessment updated.',
    narrative:
      'Updated security telemetry applied to third-party API connectors. Note: 2 legacy webhook endpoints in auxiliary clinic billing require deprecation planning before next audit cycle to maintain fully compliant posture.',
    impact:
      'Auxiliary billing service flagged for scheduled certificate rollover. Core clinical workflows remain protected and unaffected.',
    safeguardsPassed: 17,
    totalSafeguards: 19,
    lastVerified: 'Yesterday at 16:45 UTC',
  },
  {
    id: 'sum-recovery',
    period: 'Disaster Recovery SLA',
    status: 'verified',
    headline: 'Immutable Backup SLA verified.',
    narrative:
      'Synthetic recovery test executed successfully with a 42-minute Recovery Time Objective (RTO). Air-gapped AWS S3 Object Lock and Veeam write-once retention validated for 30-day minimum immutability.',
    impact:
      'Ransomware resiliency validated against primary EHR database snapshots with zero data corruption.',
    safeguardsPassed: 12,
    totalSafeguards: 12,
    lastVerified: 'Today at 04:00 UTC',
  },
];

/**
 * Documents page ("Customer Evidence").
 *
 * The demo workspace shows the bundled sample vault (`DocumentsDemoView`),
 * tagged "Sample data". A real organisation only ever sees the reports that
 * were generated for it and the evidence ledger recorded for it
 * (`DocumentsLiveView`), or a plain statement that there is nothing yet.
 */
export default function DocumentsPage() {
  const { orgId, isDemo, loading } = useActiveOrg();
  if (isDemo) return <DocumentsDemoView orgId={orgId} />;
  if (loading) return <LoadingState message="Loading documents..." />;
  return <DocumentsLiveView orgId={orgId} />;
}

/** Sample vault. Demo workspace only: every folder, file, hash and summary below is illustrative. */
function DocumentsDemoView({ orgId }: { orgId: string }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<'all' | 'pdf' | 'csv' | 'packages'>('all');
  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);
  const [selectedFolder, setSelectedFolder] = useState<AuditFolder | null>(null);
  const [selectedSummary, setSelectedSummary] = useState<ExecutiveSummaryItem | null>(null);

  const [activeTab, setActiveTab] = useState<'vault' | 'ledger'>('vault');
  const [ledger, setLedger] = useState<EvidenceLedgerItem[]>([]);
  const [loadingLedger, setLoadingLedger] = useState(false);
  const [uploadToast, setUploadToast] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (activeTab === 'ledger') {
      setLoadingLedger(true);
      getEvidenceLedger(orgId, 50)
        .then((data) => {
          if (active) setLedger(data);
        })
        .catch((err) => {
          console.error('Failed to load evidence ledger:', err);
        })
        .finally(() => {
          if (active) setLoadingLedger(false);
        });
    }
    return () => {
      active = false;
    };
  }, [activeTab, orgId]);

  const handleDownloadBoardStory = async () => {
    setDownloadingId('board-story-pdf');
    try {
      await downloadBoardStoryPdf(orgId);
    } catch (err) {
      console.error('Board story download error:', err);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleDownloadItem = (id: string, name: string) => {
    setDownloadingId(id);
    setTimeout(() => {
      // Simulate client trigger or blob download
      const element = document.createElement('a');
      const file = new Blob([`ResilAI Verified Document: ${name}\nOrganization: ${orgId}\nGenerated: ${new Date().toISOString()}`], {
        type: 'text/plain',
      });
      element.href = URL.createObjectURL(file);
      element.download = `${name.replace(/\.[^/.]+$/, '')}_export.txt`;
      document.body.appendChild(element);
      element.click();
      document.body.removeChild(element);
      setDownloadingId(null);
    }, 600);
  };

  const handleCopyHash = (hash: string) => {
    try {
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(hash);
      }
    } catch {
      // ignore in test env
    }
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleUploadSimulate = () => {
    setUploadToast('Evidence ingestion active. Select connectors in Connectors Fleet or upload manual policy attestation.');
    setTimeout(() => setUploadToast(null), 4000);
  };

  const reportsList: RecentReport[] = useMemo(
    () => [
      {
        id: 'rep-board',
        title: 'Boardroom Security Posture Story',
        category: 'board',
        format: 'pdf',
        generatedAt: 'Today, 09:00 UTC',
        size: '1.8 MB',
        status: 'verified',
        description: 'Deterministic executive health narrative and prioritized risk roadmap for healthcare leadership.',
        downloadHandler: handleDownloadBoardStory,
      },
      {
        id: 'rep-soc2',
        title: 'Q3 SOC 2 Readiness Assessment Package',
        category: 'soc2',
        format: 'pdf',
        generatedAt: 'Oct 12, 2023',
        size: '2.4 MB',
        status: 'verified',
        description: 'Readiness evidence mapped across Trust Services Criteria (Security, Availability, Processing Integrity).',
      },
      {
        id: 'rep-access',
        title: 'Access Control & MFA Telemetry Log',
        category: 'audit',
        format: 'csv',
        generatedAt: 'Oct 10, 2023',
        size: '1.1 MB',
        status: 'verified',
        description: 'Complete user authentication audit log with conditional access verification flags.',
      },
      {
        id: 'rep-ops',
        title: 'Monthly IT Operations & Drift Summary',
        category: 'operations',
        format: 'pdf',
        generatedAt: 'Current Month',
        size: '3.2 MB',
        status: 'verified',
        description: 'Aggregated endpoint uptime, patch velocity, and connector telemetry health metrics.',
      },
      {
        id: 'rep-recovery',
        title: 'EHR Disaster Recovery SLA & Immutability Attestation',
        category: 'recovery',
        format: 'pdf',
        generatedAt: 'Oct 08, 2023',
        size: '1.5 MB',
        status: 'verified',
        description: 'Cryptographically verified snapshot logs and automated failover benchmark results.',
      },
    ],
    [orgId]
  );

  // Filter folders and reports based on search & category
  const filteredFolders = AUDIT_FOLDERS.filter((f) => {
    const matchesSearch =
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.description.toLowerCase().includes(searchQuery.toLowerCase());
    if (categoryFilter === 'packages') return matchesSearch;
    return matchesSearch;
  });

  const filteredReports = reportsList.filter((r) => {
    const matchesSearch =
      r.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.description.toLowerCase().includes(searchQuery.toLowerCase());
    if (categoryFilter === 'all') return matchesSearch;
    if (categoryFilter === 'pdf') return matchesSearch && r.format === 'pdf';
    if (categoryFilter === 'csv') return matchesSearch && r.format === 'csv';
    return matchesSearch;
  });

  return (
    <div className="space-y-8 animate-fade-up max-w-7xl mx-auto pb-16">
      {/* Contextual Demo Mode Amber Guidance Banner */}
      <ContextualDemoBanner section="documents" />

      {/* Page Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant/30 pb-6">
        <div>
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">Documents & Evidence Vault</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20 flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-ready-emerald animate-pulse" />
              Audit-Ready
            </span>
            <span
              data-testid="sample-data-tag"
              className="px-2 py-0.5 rounded text-[10px] uppercase font-mono font-bold tracking-wider bg-drift-amber/10 text-drift-amber border border-drift-amber/30"
            >
              Sample data
            </span>
          </div>
          <p className="text-sm md:text-base text-on-surface-variant mt-1.5 max-w-3xl">
            Centralized repository for verified compliance evidence, server-generated executive board reports, and disaster recovery playbooks.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={handleUploadSimulate}
            className="flex items-center gap-2 bg-ready-emerald text-slate-950 px-4 py-2.5 rounded-xl font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all shadow-md shadow-ready-emerald/20"
          >
            <Upload className="w-4 h-4" />
            <span>Upload Evidence</span>
          </button>
        </div>
      </header>

      {/* Upload simulated toast */}
      {uploadToast && (
        <div className="p-4 bg-surface-container-high border border-ready-emerald/40 rounded-xl text-on-surface text-xs flex items-center justify-between animate-in fade-in">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-ready-emerald" />
            <span>{uploadToast}</span>
          </div>
          <button onClick={() => setUploadToast(null)} className="text-on-surface-variant hover:text-on-surface">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-surface-container-low border border-outline-variant/30 rounded-xl p-3">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search documents, policies, SHA-256 logs..."
            className="w-full bg-surface-container border border-outline-variant/40 rounded-lg pl-10 pr-4 py-2 text-xs text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-ready-emerald transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setActiveTab('vault')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === 'vault'
                ? 'bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <FolderCheck className="w-3.5 h-3.5" />
            <span>Evidence Vault</span>
          </button>
          <button
            onClick={() => setActiveTab('ledger')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === 'ledger'
                ? 'bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Sync Ledger</span>
          </button>
        </div>
      </div>

      {activeTab === 'vault' ? (
        /* Main Bento Grid Layout */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Folders + Recent Reports (Span 8) */}
          <div className="lg:col-span-8 space-y-8">
            {/* Section 1: Audit-Ready Folders */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
                  <Folder className="w-5 h-5 text-ready-emerald" />
                  <span>Audit-Ready Folders</span>
                </h2>
                <span className="text-xs font-mono text-on-surface-variant">
                  {filteredFolders.length} categories active
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {filteredFolders.map((folder) => {
                  const isVerified = folder.status === 'verified' || folder.status === 'current';
                  return (
                    <div
                      key={folder.id}
                      onClick={() => setSelectedFolder(folder)}
                      className="group bg-surface-container-low border border-outline-variant/60 hover:border-ready-emerald/50 rounded-xl p-5 cursor-pointer transition-all duration-300 hover:shadow-xl hover:shadow-black/25 hover:-translate-y-0.5 relative overflow-hidden"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div
                          className={`p-2.5 rounded-lg ${
                            isVerified ? 'bg-ready-emerald/10 text-ready-emerald' : 'bg-drift-amber/10 text-drift-amber'
                          }`}
                        >
                          {folder.icon === 'hipaa' && <ShieldCheck className="w-5 h-5" />}
                          {folder.icon === 'policy' && <FileCheck className="w-5 h-5" />}
                          {folder.icon === 'config' && <Server className="w-5 h-5" />}
                          {folder.icon === 'recovery' && <HardDriveDownload className="w-5 h-5" />}
                        </div>
                        <span className="text-on-surface-variant group-hover:text-on-surface transition-colors p-1">
                          <MoreVertical className="w-4 h-4" />
                        </span>
                      </div>

                      <h3 className="text-sm font-bold text-on-surface mb-1 group-hover:text-ready-emerald transition-colors">
                        {folder.name}
                      </h3>
                      <span className="text-[10px] font-mono uppercase text-ready-emerald/90 block mb-1">
                        {folder.id === 'folder-hipaa' ? 'HIPAA Evidence' : folder.category}
                      </span>
                      <p className="text-[11px] font-mono text-on-surface-variant flex items-center gap-1.5 mb-2">
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            isVerified ? 'bg-ready-emerald' : 'bg-drift-amber'
                          }`}
                        />
                        <span className={isVerified ? 'text-on-surface-variant' : 'text-drift-amber font-semibold'}>
                          {folder.statusLabel}
                        </span>
                        <span>· {folder.fileCount} files</span>
                      </p>
                      <p className="text-xs text-on-surface-variant line-clamp-2 leading-relaxed">
                        {folder.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </section>

            {/* Section 2: Recent Reports & Artifacts */}
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
                  <History className="w-5 h-5 text-ready-emerald" />
                  <span>Recent Reports & Verification Exports</span>
                </h2>
                <div className="flex items-center gap-1.5 text-xs text-on-surface-variant">
                  <span className="w-2 h-2 rounded-full bg-ready-emerald" />
                  <span>Server-Generated</span>
                </div>
              </div>

              <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl overflow-hidden shadow-sm">
                {/* Table Header */}
                <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-outline-variant/60 text-xs font-mono uppercase text-on-surface-variant bg-surface-container/60">
                  <div className="col-span-8 md:col-span-6">Document Name</div>
                  <div className="hidden md:block col-span-3">Generated</div>
                  <div className="hidden md:block col-span-1">Size</div>
                  <div className="col-span-4 md:col-span-2 text-right">Actions</div>
                </div>

                {/* Table Rows */}
                <div className="divide-y divide-outline-variant/40">
                  {filteredReports.map((report) => (
                    <div
                      key={report.id}
                      className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-surface-container-high/40 transition-colors group"
                    >
                      <div className="col-span-8 md:col-span-6 flex items-center gap-3.5">
                        <div
                          className={`w-9 h-9 rounded-lg flex items-center justify-center shrink-0 ${
                            report.format === 'pdf'
                              ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                              : report.format === 'csv'
                              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                              : 'bg-blue-500/10 text-blue-400 border border-blue-500/20'
                          }`}
                        >
                          {report.format === 'pdf' && <FileText className="w-4 h-4" />}
                          {report.format === 'csv' && <FileSpreadsheet className="w-4 h-4" />}
                          {report.format === 'json' && <FileCode className="w-4 h-4" />}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-on-surface truncate group-hover:text-ready-emerald transition-colors">
                            {report.title}
                          </p>
                          <p className="text-[11px] text-on-surface-variant truncate max-w-sm">
                            {report.description}
                          </p>
                          <p className="text-[10px] font-mono text-on-surface-variant md:hidden mt-0.5">
                            {report.generatedAt} · {report.size}
                          </p>
                        </div>
                      </div>

                      <div className="hidden md:block col-span-3 text-xs font-mono text-on-surface-variant">
                        {report.generatedAt}
                      </div>

                      <div className="hidden md:block col-span-1 text-xs font-mono text-on-surface-variant">
                        {report.size}
                      </div>

                      <div className="col-span-4 md:col-span-2 flex items-center justify-end gap-2">
                        <button
                          onClick={() => {
                            if (report.downloadHandler) {
                              report.downloadHandler();
                            } else {
                              handleDownloadItem(report.id, report.title);
                            }
                          }}
                          disabled={downloadingId === report.id || downloadingId === 'board-story-pdf'}
                          className="px-2.5 py-1.5 bg-ready-emerald/10 text-ready-emerald hover:bg-ready-emerald hover:text-slate-950 border border-ready-emerald/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
                          title={`Download ${report.title}`}
                        >
                          {downloadingId === report.id || (report.id === 'rep-board' && downloadingId === 'board-story-pdf') ? (
                            <>
                              <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              <span className="hidden sm:inline">Preparing</span>
                            </>
                          ) : (
                            <>
                              <Download className="w-3.5 h-3.5" />
                              <span className="hidden sm:inline">Download</span>
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => handleCopyHash(`https://resilai.health/reports/${report.id}?org=${orgId}`)}
                          className="p-1.5 text-on-surface-variant hover:text-on-surface hover:bg-surface-container rounded-lg transition-colors"
                          title="Share report URL"
                        >
                          <Share2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </section>
          </div>

          {/* Right Column: Executive Summaries (Span 4) */}
          <div className="lg:col-span-4 space-y-8">
            <section className="h-full">
              <div className="sticky top-28 space-y-6">
                <div className="flex items-center justify-between">
                  <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
                    <FileText className="w-5 h-5 text-ready-emerald" />
                    <span>Executive Summaries</span>
                  </h2>
                  <span className="text-xs font-mono text-ready-emerald">Leadership View</span>
                </div>

                <div className="space-y-4">
                  {EXECUTIVE_SUMMARIES.map((summary) => {
                    const isEmerald = summary.status === 'stable' || summary.status === 'verified';
                    return (
                      <div
                        key={summary.id}
                        className={`bg-surface-container-low border border-outline-variant/60 rounded-xl p-5 relative overflow-hidden group border-l-4 ${
                          isEmerald ? 'border-l-ready-emerald' : 'border-l-drift-amber'
                        }`}
                      >
                        <div
                          className={`absolute right-0 top-0 w-24 h-24 rounded-full -mr-12 -mt-12 transition-transform group-hover:scale-150 duration-500 pointer-events-none ${
                            isEmerald ? 'bg-ready-emerald/5' : 'bg-drift-amber/5'
                          }`}
                        />

                        <div className="flex items-center justify-between gap-2 mb-3">
                          <div className="flex items-center gap-1.5">
                            {isEmerald ? (
                              <CheckCircle2 className="w-4 h-4 text-ready-emerald" />
                            ) : (
                              <AlertCircle className="w-4 h-4 text-drift-amber" />
                            )}
                            <span
                              className={`text-[11px] font-mono font-bold uppercase tracking-wider ${
                                isEmerald ? 'text-ready-emerald' : 'text-drift-amber'
                              }`}
                            >
                              {summary.period}
                            </span>
                          </div>
                          <span className="text-[10px] font-mono text-on-surface-variant">
                            {summary.safeguardsPassed}/{summary.totalSafeguards} Verified
                          </span>
                        </div>

                        <h3 className="text-sm font-bold text-on-surface leading-snug mb-2">
                          {summary.headline}
                        </h3>

                        <p className="text-xs text-on-surface-variant leading-relaxed mb-4">
                          {summary.narrative}
                        </p>

                        <div className="pt-3 border-t border-outline-variant/60 flex items-center justify-between">
                          <span className="text-[10px] font-mono text-on-surface-variant">
                            {summary.lastVerified}
                          </span>
                          <button
                            onClick={() => setSelectedSummary(summary)}
                            className="text-xs font-semibold text-ready-emerald hover:brightness-125 flex items-center gap-1 transition-colors"
                          >
                            <span>Read Full Summary</span>
                            <ArrowRight className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Cryptographic Ledger Callout Card */}
                <div className="bg-gradient-to-br from-surface-container to-surface-container-high border border-outline-variant/30 rounded-xl p-5 space-y-3">
                  <div className="flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-ready-emerald" />
                    <h4 className="text-xs font-bold text-on-surface uppercase tracking-wider">
                      Cryptographic Evidence Ledger
                    </h4>
                  </div>
                  <p className="text-xs text-on-surface-variant leading-relaxed">
                    All document summaries are mathematically bound to SHA-256 connector telemetry hashes harvested from your environment.
                  </p>
                  <button
                    onClick={() => setActiveTab('ledger')}
                    className="text-xs font-semibold text-ready-emerald hover:underline flex items-center gap-1"
                  >
                    <span>View Real-Time Sync Logs</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            </section>
          </div>
        </div>
      ) : (
        /* Tab 2: Cryptographic Audit Ledger & Sync Logs */
        <div className="space-y-6">
          <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-outline-variant/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-container/60">
              <div>
                <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
                  <History className="w-4 h-4 text-ready-emerald" />
                  <span>Connector Synchronization & Verification Logs</span>
                </h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Immutable audit ledger verifying continuous operational health across external integrations.
                </p>
              </div>
              <button
                onClick={() => {
                  setLoadingLedger(true);
                  getEvidenceLedger(orgId, 50).then(setLedger).finally(() => setLoadingLedger(false));
                }}
                className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-lg border border-outline-variant/50 flex items-center gap-1.5 self-start sm:self-auto"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingLedger ? 'animate-spin' : ''}`} />
                <span>Refresh Ledger</span>
              </button>
            </div>

            {loadingLedger ? (
              <div className="p-12 flex justify-center">
                <LoadingState />
              </div>
            ) : ledger && ledger.length > 0 ? (
              <LedgerTable ledger={ledger} copiedHash={copiedHash} onCopy={handleCopyHash} />
            ) : (
              <div className="p-12 text-center text-on-surface-variant space-y-2">
                <ShieldCheck className="w-8 h-8 text-ready-emerald mx-auto" />
                <p className="text-sm font-semibold text-on-surface">No verification ledger events recorded yet.</p>
                <p className="text-xs max-w-md mx-auto">
                  Connect external security telemetry sources to populate continuous cryptographic audit logs.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Folder Details Modal */}
      {selectedFolder && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in"
          onClick={() => setSelectedFolder(null)}
        >
          <div
            className="bg-surface-container-low border border-outline-variant/60 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl animate-in zoom-in-95"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-ready-emerald/10 text-ready-emerald rounded-xl border border-ready-emerald/30">
                  <FolderCheck className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-on-surface">{selectedFolder.name}</h3>
                  <p className="text-xs text-on-surface-variant">{selectedFolder.description}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedFolder(null)}
                className="p-1.5 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              <h4 className="text-xs font-mono uppercase text-on-surface-variant">Verified Files in Category</h4>
              <div className="divide-y divide-outline-variant/40 border border-outline-variant/60 rounded-xl overflow-hidden bg-surface-container/50">
                {selectedFolder.files.map((file) => (
                  <div key={file.id} className="p-4 flex items-center justify-between gap-4 hover:bg-surface-container transition-colors">
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-on-surface truncate">{file.name}</p>
                      <p className="text-[11px] font-mono text-on-surface-variant mt-0.5">
                        {file.size} · Verified {file.verifiedAt}
                      </p>
                      <p className="text-[10px] font-mono text-ready-emerald truncate mt-1">
                        {file.hash}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDownloadItem(file.id, file.name)}
                      className="px-3 py-1.5 bg-ready-emerald/10 hover:bg-ready-emerald hover:text-slate-950 text-ready-emerald border border-ready-emerald/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all shrink-0"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-outline-variant/60 flex items-center justify-between text-xs font-mono text-on-surface-variant">
              <span>All artifacts verified by ResilAI Cryptographic Ledger</span>
              <button
                onClick={() => setSelectedFolder(null)}
                className="px-4 py-2 bg-surface-container hover:bg-surface-container-high text-on-surface font-semibold rounded-lg"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Executive Summary Detail Modal */}
      {selectedSummary && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-in fade-in"
          onClick={() => setSelectedSummary(null)}
        >
          <div
            className="bg-surface-container-low border border-outline-variant/60 rounded-2xl max-w-2xl w-full p-6 space-y-6 shadow-2xl animate-in zoom-in-95"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="p-3 bg-ready-emerald/10 text-ready-emerald rounded-xl border border-ready-emerald/30">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <span className="text-[10px] font-mono font-bold uppercase text-ready-emerald">
                    {selectedSummary.period}
                  </span>
                  <h3 className="text-lg font-bold text-on-surface">{selectedSummary.headline}</h3>
                </div>
              </div>
              <button
                onClick={() => setSelectedSummary(null)}
                className="p-1.5 text-on-surface-variant hover:text-on-surface rounded-lg hover:bg-surface-container"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-4 text-xs text-on-surface leading-relaxed">
              <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 space-y-2">
                <h4 className="font-bold text-on-surface text-xs uppercase tracking-wider">Executive Overview</h4>
                <p className="text-on-surface-variant">{selectedSummary.narrative}</p>
              </div>

              <div className="p-4 bg-surface-container rounded-xl border border-outline-variant/60 space-y-2">
                <h4 className="font-bold text-on-surface text-xs uppercase tracking-wider">Clinical & Business Impact</h4>
                <p className="text-on-surface-variant">{selectedSummary.impact}</p>
              </div>

              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/50">
                  <span className="text-[10px] font-mono text-on-surface-variant uppercase block">Safeguards Passed</span>
                  <span className="text-lg font-bold text-ready-emerald">
                    {selectedSummary.safeguardsPassed} / {selectedSummary.totalSafeguards}
                  </span>
                </div>
                <div className="p-3 bg-surface-container rounded-lg border border-outline-variant/50">
                  <span className="text-[10px] font-mono text-on-surface-variant uppercase block">Verification Timestamp</span>
                  <span className="text-xs font-mono font-semibold text-on-surface mt-1 block">
                    {selectedSummary.lastVerified}
                  </span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-outline-variant/60 flex items-center justify-between">
              <span className="text-[11px] font-mono text-on-surface-variant">
                100% Deterministic Engine Evidence
              </span>
              <button
                onClick={() => setSelectedSummary(null)}
                className="px-4 py-2 bg-ready-emerald text-slate-950 font-bold rounded-lg text-xs hover:brightness-110"
              >
                Close Summary
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Shared: evidence ledger table                                               */
/* -------------------------------------------------------------------------- */

/** Backend timestamps without a zone are UTC. Falls back to the raw text when it cannot be parsed. */
function formatWhen(value: string | null | undefined): string {
  if (!value) return 'Not recorded';
  const text = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2}(\.\d+)?)?$/.test(value) ? `${value}Z` : value;
  const date = new Date(text);
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString();
}

function LedgerTable({
  ledger,
  copiedHash,
  onCopy,
  live = false,
}: {
  ledger: EvidenceLedgerItem[];
  copiedHash: string | null;
  onCopy: (hash: string) => void;
  /** Real organisation: neutral column names, and every cell is exactly what the backend recorded. */
  live?: boolean;
}) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-xs whitespace-nowrap">
        <thead className="bg-surface-container text-xs font-mono uppercase text-on-surface-variant border-b border-outline-variant/50">
          <tr>
            <th className="px-6 py-3">{live ? 'Recorded' : 'Timestamp (UTC)'}</th>
            <th className="px-6 py-3">{live ? 'Source' : 'Source Integration'}</th>
            <th className="px-6 py-3">{live ? 'Event' : 'Verification Event'}</th>
            <th className="px-6 py-3">Status</th>
            <th className="px-6 py-3">{live ? 'Evidence Hash' : 'SHA-256 Evidence Hash'}</th>
            <th className="px-6 py-3 text-right">Action</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-outline-variant/40">
          {ledger.map((item, index) => {
            const hash = item.evidence_hash || '';
            const verified = item.verification_status === 'verified';
            return (
              <tr key={item.id || index} className="hover:bg-surface-container/40 transition-colors">
                <td className="px-6 py-3.5 font-mono text-on-surface-variant">
                  {live ? formatWhen(item.timestamp) : new Date(item.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-3.5 font-semibold text-on-surface">{item.source_name}</td>
                <td className="px-6 py-3.5 text-on-surface-variant">{item.event_type}</td>
                <td className="px-6 py-3.5">
                  <span
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase ${
                      verified
                        ? 'bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/30'
                        : 'bg-drift-amber/10 text-drift-amber border border-drift-amber/30'
                    }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${verified ? 'bg-ready-emerald' : 'bg-drift-amber'}`} />
                    {item.verification_status || 'not recorded'}
                  </span>
                </td>
                <td className="px-6 py-3.5 font-mono text-on-surface-variant">
                  {hash ? (
                    <span className="bg-surface-container px-2 py-1 rounded text-[11px] border border-outline-variant/30">
                      {hash.length > 28 ? `${hash.substring(0, 16)}...${hash.substring(hash.length - 8)}` : hash}
                    </span>
                  ) : (
                    <span>Not recorded</span>
                  )}
                </td>
                <td className="px-6 py-3.5 text-right">
                  {hash && (
                    <button
                      onClick={() => onCopy(hash)}
                      className="inline-flex items-center gap-1 text-ready-emerald hover:underline text-xs font-semibold"
                    >
                      {copiedHash === hash ? (
                        <>
                          <Check className="w-3.5 h-3.5" />
                          <span>Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5" />
                          <span>Copy Hash</span>
                        </>
                      )}
                    </button>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/* Live view: a real organisation                                              */
/* -------------------------------------------------------------------------- */

type LoadStatus = 'idle' | 'loading' | 'ready' | 'error';

const DOWNLOADABLE_STATUSES = new Set(['completed', 'ready']);

function DocumentsLiveView({ orgId }: { orgId: string }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [activeTab, setActiveTab] = useState<'vault' | 'ledger'>('vault');

  const [reports, setReports] = useState<BackendReport[]>([]);
  const [reportsStatus, setReportsStatus] = useState<LoadStatus>('loading');
  const [reportsReloadKey, setReportsReloadKey] = useState(0);

  const [ledger, setLedger] = useState<EvidenceLedgerItem[]>([]);
  const [ledgerStatus, setLedgerStatus] = useState<LoadStatus>('idle');
  const [ledgerReloadKey, setLedgerReloadKey] = useState(0);

  const [downloadingId, setDownloadingId] = useState<string | null>(null);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  const reloadReports = useCallback(() => setReportsReloadKey((key) => key + 1), []);
  const reloadLedger = useCallback(() => setLedgerReloadKey((key) => key + 1), []);

  // Reports generated for this organisation (GET /api/reports?organization_id=...).
  useEffect(() => {
    let active = true;
    if (!orgId) {
      setReports([]);
      setReportsStatus('ready');
      return;
    }
    setReportsStatus('loading');
    (async () => {
      try {
        const response = await getReports({ organization_id: orgId, limit: 50 });
        if (!active) return;
        const rows = Array.isArray(response?.reports) ? response.reports : [];
        setReports(
          rows.filter(
            (report) =>
              report &&
              typeof report.id === 'string' &&
              typeof report.title === 'string' &&
              // Never list another organisation's report, whatever the server returned.
              (!report.organization_id || report.organization_id === orgId)
          )
        );
        setReportsStatus('ready');
      } catch (err) {
        console.error('Failed to load reports:', err);
        if (active) setReportsStatus('error');
      }
    })();
    return () => {
      active = false;
    };
  }, [orgId, reportsReloadKey]);

  // Evidence ledger recorded for this organisation (GET /api/v1/evidence/ledger).
  useEffect(() => {
    let active = true;
    if (activeTab !== 'ledger') return;
    if (!orgId) {
      setLedger([]);
      setLedgerStatus('ready');
      return;
    }
    setLedgerStatus('loading');
    (async () => {
      try {
        const rows = await getEvidenceLedger(orgId, 50);
        if (!active) return;
        setLedger(Array.isArray(rows) ? rows : []);
        setLedgerStatus('ready');
      } catch (err) {
        console.error('Failed to load evidence ledger:', err);
        if (active) setLedgerStatus('error');
      }
    })();
    return () => {
      active = false;
    };
  }, [activeTab, orgId, ledgerReloadKey]);

  const handleDownload = async (report: BackendReport) => {
    setDownloadingId(report.id);
    setDownloadError(null);
    try {
      const blob = report.download_url
        ? await downloadReportById(report.id, report.download_url)
        : await downloadReportById(report.id);
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      const safeTitle = report.title.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '') || 'report';
      const created = new Date(report.created_at);
      const stamp = Number.isNaN(created.getTime()) ? '' : `_${created.toISOString().split('T')[0]}`;
      anchor.download = `ResilAI_Report_${safeTitle}${stamp}.${report.format || 'pdf'}`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Report download failed:', err);
      setDownloadError(`"${report.title}" could not be downloaded. Please try again.`);
    } finally {
      setDownloadingId(null);
    }
  };

  const handleCopyHash = (hash: string) => {
    try {
      if (navigator?.clipboard?.writeText) {
        navigator.clipboard.writeText(hash);
      }
    } catch {
      // ignore in test env
    }
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const filteredReports = useMemo(() => {
    const q = searchQuery.trim().toLowerCase();
    if (!q) return reports;
    return reports.filter(
      (report) =>
        report.title.toLowerCase().includes(q) || String(report.report_type || '').toLowerCase().includes(q)
    );
  }, [reports, searchQuery]);

  return (
    <div className="space-y-8 animate-fade-up max-w-7xl mx-auto pb-16" data-testid="documents-live">
      {/* Page Header */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-outline-variant/30 pb-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold text-on-surface tracking-tight">Documents & Evidence Vault</h1>
          <p className="text-sm md:text-base text-on-surface-variant mt-1.5 max-w-3xl">
            The reports generated for your organisation, and the evidence ledger recorded from your connected systems.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <Link
            to="/reports"
            className="flex items-center gap-2 bg-ready-emerald text-slate-950 px-4 py-2.5 rounded-xl font-semibold text-xs hover:brightness-110 active:scale-[0.98] transition-all shadow-md shadow-ready-emerald/20"
          >
            <FileText className="w-4 h-4" />
            <span>Generate a report</span>
          </Link>
        </div>
      </header>

      {/* Search & Tabs */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-surface-container-low border border-outline-variant/30 rounded-xl p-3">
        <div className="relative w-full sm:max-w-md">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search your reports..."
            className="w-full bg-surface-container border border-outline-variant/40 rounded-lg pl-10 pr-4 py-2 text-xs text-on-surface placeholder:text-on-surface-variant focus:outline-none focus:ring-2 focus:ring-ready-emerald transition-all"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              aria-label="Clear search"
              className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-on-surface"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
          <button
            onClick={() => setActiveTab('vault')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === 'vault'
                ? 'bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <FolderCheck className="w-3.5 h-3.5" />
            <span>Evidence Vault</span>
          </button>
          <button
            onClick={() => setActiveTab('ledger')}
            className={`px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-colors flex items-center gap-1.5 ${
              activeTab === 'ledger'
                ? 'bg-ready-emerald/15 text-ready-emerald border border-ready-emerald/30'
                : 'bg-surface-container text-on-surface-variant hover:text-on-surface'
            }`}
          >
            <History className="w-3.5 h-3.5" />
            <span>Audit Sync Ledger</span>
          </button>
        </div>
      </div>

      {activeTab === 'vault' ? (
        <section className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-on-surface flex items-center gap-2">
              <History className="w-5 h-5 text-ready-emerald" />
              <span>Your Generated Reports</span>
            </h2>
            {reportsStatus === 'ready' && reports.length > 0 && (
              <span className="text-xs font-mono text-on-surface-variant">
                {filteredReports.length} of {reports.length} shown
              </span>
            )}
          </div>

          {downloadError && (
            <div
              role="alert"
              className="p-4 bg-surface-container-low border border-critical-red/30 rounded-xl text-xs text-on-surface flex items-center justify-between gap-4"
            >
              <div className="flex items-center gap-2">
                <AlertCircle className="w-4 h-4 text-critical-red shrink-0" />
                <span>{downloadError}</span>
              </div>
              <button
                onClick={() => setDownloadError(null)}
                aria-label="Dismiss"
                className="text-on-surface-variant hover:text-on-surface"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {reportsStatus === 'loading' || reportsStatus === 'idle' ? (
            <LoadingState message="Loading your documents..." />
          ) : reportsStatus === 'error' ? (
            <ErrorState error="We could not load your documents. Please try again." onRetry={reloadReports} />
          ) : reports.length === 0 ? (
            <div
              data-testid="documents-empty-state"
              className="p-8 rounded-xl bg-surface-container-low border border-dashed border-surface-bright flex flex-col items-center justify-center text-center"
            >
              <div className="w-12 h-12 rounded-2xl bg-drift-amber/10 border border-drift-amber/30 flex items-center justify-center text-drift-amber mb-3">
                <FileText className="w-6 h-6" />
              </div>
              <h3 className="text-base font-semibold text-on-surface">No documents yet.</h3>
              <p className="text-xs text-on-surface-variant max-w-md mt-1 leading-relaxed">
                Reports generated for your organisation appear here. Generate one on the Reports page, or connect a
                system first so there is evidence to report on.
              </p>
              <div className="mt-4 flex flex-wrap items-center justify-center gap-3">
                <Link
                  to="/reports"
                  className="inline-flex items-center gap-2 px-6 py-3 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl transition-all active:scale-[0.98]"
                >
                  <FileText className="w-4 h-4" />
                  <span>Go to Reports</span>
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
          ) : filteredReports.length === 0 ? (
            <p className="text-xs text-on-surface-variant">No report matches your search.</p>
          ) : (
            <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl overflow-hidden shadow-sm">
              <div className="grid grid-cols-12 gap-4 px-6 py-3 border-b border-outline-variant/60 text-xs font-mono uppercase text-on-surface-variant bg-surface-container/60">
                <div className="col-span-8 md:col-span-6">Document Name</div>
                <div className="hidden md:block col-span-3">Generated</div>
                <div className="hidden md:block col-span-1">Format</div>
                <div className="col-span-4 md:col-span-2 text-right">Actions</div>
              </div>

              <div className="divide-y divide-outline-variant/40">
                {filteredReports.map((report) => {
                  const format = String(report.format || 'pdf').toLowerCase();
                  const reportStatus = String(report.status || 'completed').toLowerCase();
                  const downloadable = DOWNLOADABLE_STATUSES.has(reportStatus);
                  const typeLabel = String(report.report_type || '').replace(/_/g, ' ');
                  return (
                    <div
                      key={report.id}
                      data-testid="documents-report-row"
                      className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-surface-container-high/40 transition-colors group"
                    >
                      <div className="col-span-8 md:col-span-6 flex items-center gap-3.5">
                        <div className="w-9 h-9 rounded-lg flex items-center justify-center shrink-0 bg-surface-container text-on-surface-variant border border-outline-variant/40">
                          {format === 'csv' ? (
                            <FileSpreadsheet className="w-4 h-4" />
                          ) : format === 'json' ? (
                            <FileCode className="w-4 h-4" />
                          ) : (
                            <FileText className="w-4 h-4" />
                          )}
                        </div>
                        <div className="min-w-0">
                          <p className="text-xs font-bold text-on-surface truncate">{report.title}</p>
                          {typeLabel && (
                            <p className="text-[11px] text-on-surface-variant truncate max-w-sm capitalize">{typeLabel}</p>
                          )}
                          <p className="text-[10px] font-mono text-on-surface-variant md:hidden mt-0.5">
                            {formatWhen(report.created_at)} · {format.toUpperCase()}
                          </p>
                        </div>
                      </div>

                      <div className="hidden md:block col-span-3 text-xs font-mono text-on-surface-variant">
                        {formatWhen(report.created_at)}
                      </div>

                      <div className="hidden md:block col-span-1 text-xs font-mono text-on-surface-variant">
                        {format.toUpperCase()}
                      </div>

                      <div className="col-span-4 md:col-span-2 flex items-center justify-end gap-2">
                        {downloadable ? (
                          <button
                            onClick={() => handleDownload(report)}
                            disabled={downloadingId !== null}
                            className="px-2.5 py-1.5 bg-ready-emerald/10 text-ready-emerald hover:bg-ready-emerald hover:text-slate-950 border border-ready-emerald/30 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all disabled:opacity-50"
                            title={`Download ${report.title}`}
                            aria-label={`Download ${report.title}`}
                          >
                            {downloadingId === report.id ? (
                              <>
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                                <span className="hidden sm:inline">Preparing</span>
                              </>
                            ) : (
                              <>
                                <Download className="w-3.5 h-3.5" />
                                <span className="hidden sm:inline">Download</span>
                              </>
                            )}
                          </button>
                        ) : (
                          <span className="text-[11px] font-mono uppercase text-on-surface-variant">{reportStatus}</span>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </section>
      ) : (
        <div className="space-y-6">
          <div className="bg-surface-container-low border border-outline-variant/60 rounded-xl overflow-hidden">
            <div className="px-6 py-4 border-b border-outline-variant/60 flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-surface-container/60">
              <div>
                <h3 className="text-base font-bold text-on-surface flex items-center gap-2">
                  <History className="w-4 h-4 text-ready-emerald" />
                  <span>Connector Synchronization & Verification Logs</span>
                </h3>
                <p className="text-xs text-on-surface-variant mt-0.5">
                  Evidence events ResilAI has recorded from the systems connected to your organisation.
                </p>
              </div>
              <button
                onClick={reloadLedger}
                disabled={ledgerStatus === 'loading'}
                className="px-3 py-1.5 bg-surface-container hover:bg-surface-container-high text-on-surface text-xs font-semibold rounded-lg border border-outline-variant/50 flex items-center gap-1.5 self-start sm:self-auto disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${ledgerStatus === 'loading' ? 'animate-spin' : ''}`} />
                <span>Refresh Ledger</span>
              </button>
            </div>

            {ledgerStatus === 'loading' || ledgerStatus === 'idle' ? (
              <div className="p-12 flex justify-center">
                <LoadingState message="Loading evidence ledger..." />
              </div>
            ) : ledgerStatus === 'error' ? (
              <div className="p-8">
                <ErrorState error="We could not load the evidence ledger. Please try again." onRetry={reloadLedger} />
              </div>
            ) : ledger.length > 0 ? (
              <LedgerTable ledger={ledger} copiedHash={copiedHash} onCopy={handleCopyHash} live />
            ) : (
              <div className="p-12 text-center text-on-surface-variant space-y-2" data-testid="documents-ledger-empty-state">
                <ShieldCheck className="w-8 h-8 text-on-surface-variant mx-auto" />
                <p className="text-sm font-semibold text-on-surface">No evidence events recorded yet.</p>
                <p className="text-xs max-w-md mx-auto">
                  Once a connected system has been checked, each evidence event is listed here.
                </p>
                <Link
                  to="/connectors"
                  className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-ready-emerald hover:underline"
                >
                  <Plug className="w-3.5 h-3.5" />
                  <span>Connect a system</span>
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
