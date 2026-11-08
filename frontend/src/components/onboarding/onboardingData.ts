import type {
  IndustryCardOption,
  OnboardingOrgProfile,
  OnboardingTeamSize,
} from '../../types/onboarding';

export const INDUSTRY_CARDS: IndustryCardOption[] = [
  {
    id: 'healthcare',
    title: 'Healthcare clinic',
    caption: 'Patient records, scheduling and billing systems. Checks are worded for practice managers.',
  },
  {
    id: 'legal',
    title: 'Legal practice',
    caption: 'Client files, matter documents and email. Checks are worded for managing partners.',
  },
];

export const TEAM_SIZE_OPTIONS: { value: OnboardingTeamSize; label: string }[] = [
  { value: '1-50', label: '1-50 people' },
  { value: '51-200', label: '51-200 people' },
  { value: '201-1000', label: '201-1000 people' },
  { value: '1000+', label: 'More than 1000 people' },
];

export const INITIAL_REAL_PROFILE: OnboardingOrgProfile = {
  name: '',
  industry: 'healthcare',
  size: '1-50',
};

/**
 * First-run checklist copy. These one-line captions replaced the old six-step
 * wizard: the product now explains itself next to the action instead of before it.
 */
export const FIRST_RUN_COPY = {
  connect: {
    title: 'Connect where your email and files live',
    caption:
      'Start with Microsoft 365, then your backup system. Those two answer the question most owners ask first: if something goes wrong tonight, do we still open tomorrow?',
    href: '/connectors',
  },
  verdict: {
    title: 'Get your first Monday verdict',
    caption:
      'Once a system is connected we check it around the clock and give you one plain answer each morning, with the proof behind it.',
    href: '/morning-brief',
  },
  report: {
    title: 'Download your 1-page boss report',
    caption:
      'A one-page summary for your board, partners or insurer. Same facts as the morning brief, written for someone who was not in the room.',
    href: '/reports',
  },
} as const;

/** Plain-English note for the IT person, copied to the clipboard from the checklist. */
export const IT_HANDOFF_NOTE = `Hi,

We are setting up ResilAI to check that our systems are protected and recoverable. Could you connect it for us?

What it needs:
- Read-only access to Microsoft 365 (an Entra app registration with these application permissions: Directory.Read.All, Policy.Read.All, AuditLog.Read.All, Reports.Read.All).
- Read-only access to our backup system (a reporting or viewer account, for example a Veeam Enterprise Manager user with the "Portal Viewer" role).

What it does not do:
- It does not install any software on our computers or servers.
- It does not change settings. It only reads status and settings to confirm protections are in place.
- Credentials are stored encrypted and can be revoked at any time.

Where to enter them: sign in to ResilAI and open Connected systems (the /connectors page).

Thank you.`;

// LocalStorage helpers (still read by the readiness header)
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

export const FIRST_RUN_DISMISSED_KEY = (orgId: string) => `resilai_first_run_dismissed_${orgId}`;
