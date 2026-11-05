/**
 * Static Vertical Configuration Registry
 * 
 * Provides typed synchronous fallback configurations for all supported verticals:
 * - General Platform (Universal incident readiness, cloud & SaaS)
 * - Healthcare Vertical (Clinical continuity, ransomware defense, EHR)
 * - Legal Vertical (Client data protection, partner access, ABA compliance)
 */

import type { VerticalConfig, VerticalKey } from '../types/vertical';

export const DEFAULT_VERTICAL: VerticalKey = 'general';

export const VERTICAL_CONFIGS: Record<VerticalKey, VerticalConfig> = {
  general: {
    key: 'general',
    displayName: 'ResilAI',
    industryLabel: 'Enterprise & Cloud',
    tagline: 'Continuous Incident Readiness & Mathematical Verification',
    headline: 'ResilAI — AI Incident Readiness Platform',
    coreQuestion: 'If a security or AI incident happens tomorrow, are you actually ready?',
    focusAreas: [
      'Universal incident readiness',
      'Deterministic scoring & evidence pipeline',
      'SaaS & cloud reliability',
      'Identity & access control',
      'Executive impact translation',
      'Automated control verification',
    ],
    demoOrgId: 'demo-acme-technologies',
    demoOrgName: 'Acme Technologies',
    demoPersonaName: 'Alex Chen',
    demoPersonaRole: 'VP Engineering',
    criticalSystems: [
      'AWS Multi-Region Infrastructure',
      'Okta Identity Cloud',
      'GitHub Enterprise & CI/CD',
      'Kubernetes Production Clusters',
      'Cloudflare Edge Network',
    ],
  },
  healthcare: {
    key: 'healthcare',
    displayName: 'ResilAI Healthcare',
    industryLabel: 'Healthcare & Clinics',
    tagline: 'Continuous Clinical Continuity & Ransomware Defense',
    headline: 'Incident readiness for healthcare organizations',
    coreQuestion: "If ransomware hits your clinic tomorrow morning, can you keep operating and prove you're ready?",
    focusAreas: [
      'Ransomware resilience',
      'EHR clinical operations continuity',
      'Microsoft 365 & Entra ID protection',
      'Veeam immutable backup integrity',
      'Recovery readiness SLAs',
      'Executive board visibility',
    ],
    demoOrgId: 'demo-northstar-health',
    demoOrgName: 'Northstar Family Health',
    demoPersonaName: 'Dr. Evelyn Reed',
    demoPersonaRole: 'Chief Medical Officer',
    criticalSystems: [
      'Epic EHR Clinical System',
      'Veeam Cloud Connect Immutable Backups',
      'Microsoft 365 / Entra ID',
      'PACS Imaging Archive',
      'Clinical Workstation Network',
    ],
  },
  legal: {
    key: 'legal',
    displayName: 'ResilAI Legal',
    industryLabel: 'Law Firms & Legal',
    tagline: 'Client Data Protection & Practice Continuity',
    headline: 'Incident readiness for law firms',
    coreQuestion: 'If ransomware hits your firm tomorrow morning, can you keep operating and protect client data?',
    focusAreas: [
      'Client data protection',
      'Privileged access & confidentiality',
      'Document vault & repository security',
      'Endpoint & partner laptop protection',
      'ABA & regulatory compliance',
      'MSP & vendor visibility',
    ],
    demoOrgId: 'demo-northstar-cole',
    demoOrgName: 'Northstar & Cole LLP',
    demoPersonaName: 'Marcus Cole',
    demoPersonaRole: 'Managing Partner',
    criticalSystems: [
      'NetDocuments Vault',
      'Elite 3E Practice Management',
      'iManage Document System',
      'Azure Active Directory',
      'Partner Secure Laptops',
    ],
  },
};

/**
 * Type guard to check if a value is a valid VerticalKey.
 */
export function isVerticalKey(value: unknown): value is VerticalKey {
  return typeof value === 'string' && (value === 'general' || value === 'healthcare' || value === 'legal');
}

/**
 * Get configuration for a given vertical key, defaulting to general.
 */
export function getVerticalConfig(key: VerticalKey): VerticalConfig {
  return VERTICAL_CONFIGS[key] || VERTICAL_CONFIGS[DEFAULT_VERTICAL];
}
