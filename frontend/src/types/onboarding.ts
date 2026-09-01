export type OnboardingStepNumber = 1 | 2 | 3 | 4 | 5 | 6;

export type OnboardingMode = 'demo' | 'real';

export interface OnboardingOrgProfile {
  name: string;
  industry: string;
  size: string;
  country: string;
  regionState: string;
  clinicalTier?: string;
  primarySystems?: string[];
}

export interface SecurityConnectorState {
  id: string;
  name: string;
  type: 'microsoft365' | 'veeam' | 'crowdstrike' | 'sentinelone' | 'splunk' | 'wazuh' | 'aws';
  category: string;
  description: string;
  iconName: string;
  status: 'connected' | 'not_configured' | 'testing' | 'error';
  lastSync?: string;
  verifiedControls: string[];
  missingControls?: string[];
  configFields: {
    key: string;
    label: string;
    placeholder: string;
    type?: string;
    required?: boolean;
    defaultValue?: string;
    value?: string;
  }[];
  simulatedTelemetry?: {
    endpointCount: number;
    lastHeartbeat: string;
    evidenceHash: string;
    latencyMs: number;
    sampleMetric: string;
  };
}

export interface EvidenceLedgerItem {
  id: string;
  controlCode: string;
  title: string;
  category: string;
  status: 'verified' | 'unverified' | 'action_needed';
  sourceConnector: string;
  lastVerifiedAt: string;
  evidenceHash: string;
  confidencePct: number;
  plainEnglishExplanation: string;
  technicalTelemetry: string;
}

export interface NeedsAttentionPreviewItem {
  id: string;
  title: string;
  severity: 'critical' | 'high' | 'medium';
  clinicalRiskScore: number; // 0-100
  clinicalImpactSummary: string;
  executiveSummary: string;
  technicalFinding: string;
  recommendedAction: string;
  system: string;
  evidenceHash: string;
}

export interface RecoveryReadinessPreview {
  immutabilityStatus: 'locked' | 'unlocked' | 'warning';
  immutabilityDays: number;
  rtoMinutes: number;
  rpoMinutes: number;
  backupSource: string;
  lastSuccessfulSnapshot: string;
  airgapVerified: boolean;
  recoveryAssuranceScore: number;
  readinessNarrative: string;
}

export interface BoardStoryPreview {
  orgName: string;
  generatedDate: string;
  readinessScore: number;
  readinessStatus: 'safe_to_open' | 'action_needed' | 'critical_risk';
  executiveSummaryHeadline: string;
  keyHighlights: string[];
  verifiedControlsCount: number;
  unverifiedGapsCount: number;
  immutabilityGuarantee: boolean;
  pdfDownloadUrl?: string;
}

export interface OnboardingState {
  currentStep: OnboardingStepNumber;
  completedSteps: OnboardingStepNumber[];
  mode: OnboardingMode;
  isDismissed: boolean;
  isCompleted: boolean;
  orgProfile: OnboardingOrgProfile;
  connectors: SecurityConnectorState[];
  selectedConnectorId?: string;
}

export interface StepMetadata {
  step: OnboardingStepNumber;
  shortTitle: string;
  title: string;
  subtitle: string;
  description: string;
  badge: string;
}
