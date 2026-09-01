import type {
  StepMetadata,
  SecurityConnectorState,
  EvidenceLedgerItem,
  NeedsAttentionPreviewItem,
  RecoveryReadinessPreview,
  BoardStoryPreview,
  OnboardingOrgProfile,
} from '../../types/onboarding';

export const ONBOARDING_STEPS_METADATA: StepMetadata[] = [
  {
    step: 1,
    shortTitle: 'Readiness Profile',
    title: 'Start with Organization Readiness',
    subtitle: 'Define your operating baseline and clinical profile',
    description: 'ResilAI continuously verifies operational controls across your environment. Establish your organizational profile to align baseline verification thresholds.',
    badge: 'Step 1 of 6',
  },
  {
    step: 2,
    shortTitle: 'Connect Systems',
    title: 'Connect Security Systems',
    subtitle: 'Link Microsoft 365, Veeam, CrowdStrike, and SentinelOne',
    description: 'ResilAI ingests deterministic telemetry directly from your active identity, backup, and endpoint detection platforms without deploying custom kernel agents.',
    badge: 'Step 2 of 6',
  },
  {
    step: 3,
    shortTitle: 'Evidence Ledger',
    title: 'See What Can Be Verified',
    subtitle: 'Explore deterministic health checks & SHA-256 evidence',
    description: 'Every control is mathematically proven with fresh cryptographic evidence. If telemetry is missing or unverified, readiness score drops to 0% for that control.',
    badge: 'Step 3 of 6',
  },
  {
    step: 4,
    shortTitle: 'Needs Attention',
    title: 'Understand What Matters',
    subtitle: 'Triage active gaps by clinical risk and operational impact',
    description: 'Instead of drowning in hundreds of raw alerts, ResilAI translates technical gaps into plain-English business impacts and prioritized executive actions.',
    badge: 'Step 4 of 6',
  },
  {
    step: 5,
    shortTitle: 'Recovery Assurance',
    title: 'Prepare for an Incident',
    subtitle: 'Verify backup immutability, air-gaps, and recovery RTOs',
    description: 'Assure uninterrupted clinical operations. Verify immutable backup snapshots, air-gapped replication locks, and realistic Recovery Time Objectives before an incident occurs.',
    badge: 'Step 5 of 6',
  },
  {
    step: 6,
    shortTitle: 'Executive Report',
    title: 'Generate Executive Board Report',
    subtitle: 'Preview and download your Boardroom Security Posture Story',
    description: 'Transform verified control telemetry into an executive-ready PDF report designed for clinic managing partners, hospital boards, and cyber insurers.',
    badge: 'Step 6 of 6',
  },
];

export const INITIAL_DEMO_PROFILE: OnboardingOrgProfile = {
  name: 'Acme Health Systems',
  industry: 'Healthcare (Outpatient Clinics & Surgical Centers)',
  size: '51-200',
  country: 'United States',
  regionState: 'California',
  clinicalTier: 'Tier 1 Critical Care & EHR Operations',
  primarySystems: ['Epic EHR', 'Microsoft 365 / Entra ID', 'Veeam Backup', 'CrowdStrike Falcon'],
};

export const INITIAL_REAL_PROFILE: OnboardingOrgProfile = {
  name: '',
  industry: 'Healthcare',
  size: '1-50',
  country: 'US',
  regionState: '',
  clinicalTier: 'Standard Healthcare Operations',
  primarySystems: ['Microsoft 365', 'Veeam Backup'],
};

export const DEFAULT_CONNECTORS: SecurityConnectorState[] = [
  {
    id: 'conn-m365',
    name: 'Microsoft 365 / Entra ID',
    type: 'microsoft365',
    category: 'Identity & Access Management',
    description: 'Verifies conditional access policies, admin MFA enforcement, and active user directory synchronization.',
    iconName: 'KeyRound',
    status: 'connected',
    lastSync: '4 minutes ago',
    verifiedControls: [
      'MFA Enforcement on Admin Accounts (IV-001)',
      'Legacy Protocol Blocking (IV-002)',
      'Privileged Role Assignment Sync (IV-003)',
    ],
    missingControls: [],
    configFields: [
      { key: 'tenant_id', label: 'Entra / Azure Tenant ID *', placeholder: '72f988bf-86f1-41af-91ab-2d7cd011db47', required: true },
      { key: 'client_id', label: 'Application (Client) ID *', placeholder: '00000000-0000-0000-0000-000000000000', required: true },
      { key: 'client_secret', label: 'Client Secret Value *', placeholder: '••••••••••••••••', type: 'password', required: true },
    ],
    simulatedTelemetry: {
      endpointCount: 142,
      lastHeartbeat: 'Just now (14:32:01 UTC)',
      evidenceHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
      latencyMs: 84,
      sampleMetric: '99.3% MFA Coverage across 142 active accounts',
    },
  },
  {
    id: 'conn-veeam',
    name: 'Veeam Backup & Replication',
    type: 'veeam',
    category: 'Backup & Recovery Assurance',
    description: 'Verifies immutable cloud backup snapshots, offsite air-gapped replication, and automated recovery SLAs.',
    iconName: 'HardDrive',
    status: 'connected',
    lastSync: '12 minutes ago',
    verifiedControls: [
      'Immutable Backup Snapshot Verification (BR-004)',
      'Air-gapped Storage Lock Validation (BR-005)',
      'EHR Database Recovery SLA Proof (BR-006)',
    ],
    missingControls: [],
    configFields: [
      { key: 'base_url', label: 'Veeam Enterprise Manager URL *', placeholder: 'https://veeam-em.clinic.local:9398', required: true },
      { key: 'api_key', label: 'API Token / Service Account Key *', placeholder: 'veeam_auth_token_...', type: 'password', required: true },
    ],
    simulatedTelemetry: {
      endpointCount: 28,
      lastHeartbeat: '12 mins ago (14:20:11 UTC)',
      evidenceHash: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      latencyMs: 142,
      sampleMetric: '30-Day Immutable Object Lock active on 28 daily volumes',
    },
  },
  {
    id: 'conn-crowdstrike',
    name: 'CrowdStrike Falcon',
    type: 'crowdstrike',
    category: 'Endpoint Detection & Response',
    description: 'Monitors clinical workstation and server agent health, real-time zero-trust posture, and threat containment.',
    iconName: 'ShieldCheck',
    status: 'connected',
    lastSync: '6 minutes ago',
    verifiedControls: [
      'EDR Agent Health on Clinical Terminals (ED-001)',
      'Zero-Trust Endpoint Hygiene Rating (ED-002)',
      'Ransomware Behavioral Isolation Active (ED-003)',
    ],
    missingControls: [],
    configFields: [
      { key: 'client_id', label: 'Falcon OAuth2 Client ID *', placeholder: 'cs_falcon_client_id_...', required: true },
      { key: 'client_secret', label: 'Falcon Client Secret *', placeholder: '••••••••••••••••', type: 'password', required: true },
      { key: 'cloud_region', label: 'Falcon Cloud Region', placeholder: 'us-1 / us-2 / eu-1', defaultValue: 'us-1' },
    ],
    simulatedTelemetry: {
      endpointCount: 218,
      lastHeartbeat: '6 mins ago (14:26:44 UTC)',
      evidenceHash: '9f83c68f7ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
      latencyMs: 62,
      sampleMetric: '218/218 active endpoints reporting healthy sensor status',
    },
  },
  {
    id: 'conn-sentinelone',
    name: 'SentinelOne Singularity',
    type: 'sentinelone',
    category: 'Autonomous Endpoint Security',
    description: 'Verifies autonomous behavioral AI detection, anti-tamper agent protection, and automated 1-click rollback readiness.',
    iconName: 'ShieldAlert',
    status: 'connected',
    lastSync: '8 minutes ago',
    verifiedControls: [
      'Behavioral AI Agent Anti-Tamper State (SO-001)',
      '1-Click Automated Rollback Capability (SO-002)',
      'Autonomous Offline Threat Containment (SO-003)',
    ],
    missingControls: [],
    configFields: [
      { key: 'management_url', label: 'SentinelOne Management Console URL *', placeholder: 'https://usea1-partners.sentinelone.net', required: true },
      { key: 'api_token', label: 'API User Token *', placeholder: 's1_api_token_••••••••', type: 'password', required: true },
    ],
    simulatedTelemetry: {
      endpointCount: 165,
      lastHeartbeat: '8 mins ago (14:24:19 UTC)',
      evidenceHash: 'c4ca4238a0b923820dcc509a6f75849b27ae41e4649b934ca495991b7852b855',
      latencyMs: 98,
      sampleMetric: '165 agents verified with Anti-Tamper & Rollback active',
    },
  },
];

export const DEMO_EVIDENCE_ITEMS: EvidenceLedgerItem[] = [
  {
    id: 'ev-01',
    controlCode: 'IV-001',
    title: 'MFA Enforcement on Administrator Accounts',
    category: 'Identity & Access',
    status: 'verified',
    sourceConnector: 'Microsoft 365 / Entra ID',
    lastVerifiedAt: '4 minutes ago',
    evidenceHash: 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
    confidencePct: 100,
    plainEnglishExplanation: 'All 12 clinic administrator accounts have hardware-token or authenticator app MFA enforced with zero legacy exclusions.',
    technicalTelemetry: 'Tenant: 72f988bf-86f1 | Verified 12/12 Global Admins with CapId: conditional-access-mfa-all-admins',
  },
  {
    id: 'ev-02',
    controlCode: 'BR-004',
    title: 'Immutable Cloud Backup Snapshot Verification',
    category: 'Recovery Assurance',
    status: 'verified',
    sourceConnector: 'Veeam Backup & Replication',
    lastVerifiedAt: '12 minutes ago',
    evidenceHash: '7f83b1657ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    confidencePct: 100,
    plainEnglishExplanation: 'Primary clinical EHR database backups are locked with 30-day write-once-read-many (WORM) immutability, preventing ransomware deletion.',
    technicalTelemetry: 'Repo: s3-immutable-worm-vault | Retention: 30d | Hash: sha256:7f83... | Last Run: 2026-08-31 14:15:00 UTC',
  },
  {
    id: 'ev-03',
    controlCode: 'ED-001',
    title: 'EDR Sensor Health on Clinical Workstations',
    category: 'Endpoint Security',
    status: 'verified',
    sourceConnector: 'CrowdStrike Falcon',
    lastVerifiedAt: '6 minutes ago',
    evidenceHash: '9f83c68f7ff1fc53b92dc18148a1d65dfc2d4b1fa3d677284addd200126d9069',
    confidencePct: 100,
    plainEnglishExplanation: 'All 218 active exam room computers and radiology workstations are actively communicating with EDR with real-time prevention enabled.',
    technicalTelemetry: 'AID Count: 218/218 online | Sensor Version: 7.14.17904 | Policy: Strict Prevention | Zero Drift',
  },
  {
    id: 'ev-04',
    controlCode: 'SO-002',
    title: 'Autonomous 1-Click Rollback Readiness',
    category: 'Incident Response',
    status: 'verified',
    sourceConnector: 'SentinelOne Singularity',
    lastVerifiedAt: '8 minutes ago',
    evidenceHash: 'c4ca4238a0b923820dcc509a6f75849b27ae41e4649b934ca495991b7852b855',
    confidencePct: 100,
    plainEnglishExplanation: 'System volume shadow copies and local rollback manifests are protected against tampering for rapid single-click ransomware recovery.',
    technicalTelemetry: 'Anti-tamper: Active | VSS Lock: Verified | Rollback Journal Capacity: 40GB allocated per host',
  },
];

export const DEMO_NEEDS_ATTENTION_ITEMS: NeedsAttentionPreviewItem[] = [
  {
    id: 'na-01',
    title: 'Radiology PACS Archive Backup Delayed (>24h)',
    severity: 'critical',
    clinicalRiskScore: 92,
    clinicalImpactSummary: 'High patient care disruption risk: If PACS storage fails today, today’s diagnostic MRIs and CT scans would require re-imaging.',
    executiveSummary: 'The secondary imaging server missed its scheduled midnight backup window due to a transient network timeout.',
    technicalFinding: 'Veeam job "PACS_Daily_Image_Archive" failed at 02:14:00 UTC with Error: SocketTimeout. Last valid snapshot is 26 hours old.',
    recommendedAction: 'Trigger immediate incremental sync on Veeam PACS repository and re-verify network route.',
    system: 'Veeam Backup (PACS Server 02)',
    evidenceHash: 'a1b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0',
  },
  {
    id: 'na-02',
    title: '3 Newly Provisioned Nurse Laptops Missing EDR Agent',
    severity: 'high',
    clinicalRiskScore: 78,
    clinicalImpactSummary: 'Moderate endpoint vulnerability: Laptops in the West Wing triage station are connected to the clinical VLAN without active telemetry.',
    executiveSummary: 'Three replacement laptops deployed this morning are not yet reporting sensor heartbeat to CrowdStrike.',
    technicalFinding: 'Entra ID shows 3 active device registrations without matching CrowdStrike AID entries in CID: 018293-healthcare.',
    recommendedAction: 'Push CrowdStrike Falcon sensor package via Intune device policy and verify heartbeat.',
    system: 'CrowdStrike Falcon (Intune)',
    evidenceHash: 'b2c3d4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef01a',
  },
];

export const DEMO_RECOVERY_PREVIEW: RecoveryReadinessPreview = {
  immutabilityStatus: 'locked',
  immutabilityDays: 30,
  rtoMinutes: 42,
  rpoMinutes: 15,
  backupSource: 'Veeam Cloud Vault & Air-Gapped S3 Object Lock',
  lastSuccessfulSnapshot: '14 minutes ago',
  airgapVerified: true,
  recoveryAssuranceScore: 94,
  readinessNarrative: 'If a catastrophic ransomware event occurs right now, your core Electronic Health Records (EHR) and patient scheduling databases can be fully restored in 42 minutes with zero data loss beyond 15 minutes of transactions.',
};

export const DEMO_BOARD_STORY_PREVIEW: BoardStoryPreview = {
  orgName: 'Acme Health Systems',
  generatedDate: 'August 31, 2026',
  readinessScore: 94,
  readinessStatus: 'safe_to_open',
  executiveSummaryHeadline: 'All critical clinical systems operating within verified incident recovery thresholds.',
  keyHighlights: [
    '100% of Administrative & Clinical accounts verified with hardware-enforced Multi-Factor Authentication.',
    '30-Day Immutable Cloud Backup lock mathematically verified across all EHR and financial databases.',
    '218 endpoint sensors actively streaming telemetry with zero unmonitored critical clinical hosts.',
    'Zero unverified controls or blind assumptions across all 4 integrated security platforms.',
  ],
  verifiedControlsCount: 24,
  unverifiedGapsCount: 0,
  immutabilityGuarantee: true,
  pdfDownloadUrl: '/api/v1/reports/board-story.pdf?org_id=demo-health-org',
};

// LocalStorage helpers
export const getOnboardingCompleted = (orgId?: string): boolean => {
  if (typeof window === 'undefined') return false;
  if (!orgId) {
    return localStorage.getItem('resilai_onboarding_completed_global') === 'true';
  }
  return (
    localStorage.getItem(`resilai_onboarding_completed_${orgId}`) === 'true' ||
    localStorage.getItem('resilai_onboarding_completed_global') === 'true'
  );
};

export const setOnboardingCompleted = (orgId: string, completed: boolean = true): void => {
  if (typeof window === 'undefined') return;
  if (orgId) {
    localStorage.setItem(`resilai_onboarding_completed_${orgId}`, completed ? 'true' : 'false');
  }
  localStorage.setItem('resilai_onboarding_completed_global', completed ? 'true' : 'false');
};

export const getOnboardingStep = (orgId?: string): number => {
  if (typeof window === 'undefined') return 1;
  const key = orgId ? `resilai_onboarding_step_${orgId}` : 'resilai_onboarding_step_global';
  const val = localStorage.getItem(key);
  const num = parseInt(val || '1', 10);
  return isNaN(num) || num < 1 || num > 6 ? 1 : num;
};

export const setOnboardingStep = (orgId: string, step: number): void => {
  if (typeof window === 'undefined') return;
  const key = orgId ? `resilai_onboarding_step_${orgId}` : 'resilai_onboarding_step_global';
  localStorage.setItem(key, String(step));
};
