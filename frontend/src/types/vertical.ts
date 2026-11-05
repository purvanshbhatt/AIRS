/**
 * Vertical Architecture Types
 * 
 * Supports host-aware and path-aware multi-vertical positioning (General, Healthcare, Legal)
 * while preserving a single, shared deterministic evidence and scoring platform.
 */

export type VerticalKey = 'general' | 'healthcare' | 'legal';

export type VerticalSource = 'subdomain' | 'path' | 'query' | 'default';

export interface VerticalConfig {
  key: VerticalKey;
  displayName: string;
  industryLabel: string;
  tagline: string;
  headline: string;
  coreQuestion: string;
  focusAreas: string[];
  demoOrgId: string;
  demoOrgName: string;
  demoPersonaName: string;
  demoPersonaRole: string;
  criticalSystems: string[];
}

export interface VerticalContextType {
  currentVertical: VerticalKey;
  config: VerticalConfig;
  setVertical: (vertical: VerticalKey) => void;
  isLoading: boolean;
  source: VerticalSource;
}

export interface PublicProductConfigResponse {
  vertical_key: string;
  display_name: string;
  industry_label: string;
  headline: string;
  core_question: string;
  focus_areas: string[];
  demo_org_id: string;
  demo_org_name: string;
}
