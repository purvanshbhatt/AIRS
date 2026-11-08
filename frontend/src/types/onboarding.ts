/**
 * Onboarding types.
 *
 * The product opens with one screen (name, industry, optional team size) and
 * then a three-item first-run checklist on the morning brief. The step number
 * type is kept only for the per-organisation localStorage helpers in
 * onboardingData.ts, which other parts of the app still read.
 */

export type OnboardingStepNumber = 1 | 2 | 3 | 4 | 5 | 6;

export type OnboardingMode = 'demo' | 'real';

/** Industry value sent to the API. "general" is what the small "Other" link maps to. */
export type OnboardingIndustry = 'healthcare' | 'legal' | 'general';

export type OnboardingTeamSize = '1-50' | '51-200' | '201-1000' | '1000+';

export interface OnboardingOrgProfile {
  name: string;
  industry: OnboardingIndustry;
  size: OnboardingTeamSize;
}

export interface IndustryCardOption {
  id: Exclude<OnboardingIndustry, 'general'>;
  title: string;
  caption: string;
}

export type FirstRunItemId = 'connect' | 'verdict' | 'report';

export interface FirstRunItem {
  id: FirstRunItemId;
  title: string;
  caption: string;
  href: string;
  done: boolean;
}
