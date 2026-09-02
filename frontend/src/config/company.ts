/**
 * ResilAI Company & Team Configuration
 * 
 * Centralized single source of truth for company metadata,
 * founding year, leadership, and public contact channels.
 */

export interface TeamMember {
  name: string;
  role: string;
  bio: string;
  email?: string;
  avatarUrl?: string;
  linkedin: string;
  github?: string;
  twitter?: string;
  isFounder?: boolean;
}

export interface CompanyInfo {
  name: string;
  tagline: string;
  description: string;
  foundedYear: number;
  location: string;
  contactEmail: string;
  securityEmail: string;
  founder: TeamMember;
  team: TeamMember[];
  socials: {
    github: string;
    linkedin: string;
    maidensail: string;
  };
}

export const COMPANY_INFO: CompanyInfo = {
  name: 'ResilAI',
  tagline: 'AI Incident Readiness Platform',
  description: 'Deterministic security evidence and AI-powered business impact intelligence for healthcare and enterprise organizations.',
  foundedYear: 2025,
  location: 'Toronto, ON & Remote',
  contactEmail: 'purvansh95b@gmail.com',
  securityEmail: 'purvansh95b@gmail.com',
  founder: {
    name: 'Purvansh Bhatt',
    role: 'Founder & Security Engineer',
    bio: 'Security engineer and systems architect specializing in continuous control verification, cryptographic audit trails, and deterministic incident resilience.',
    email: 'purvansh95b@gmail.com',
    linkedin: 'https://www.linkedin.com/in/purvanshbhatt',
    github: 'https://github.com/purvanshbhatt',
    isFounder: true,
  },
  team: [
    {
      name: 'Purvansh Bhatt',
      role: 'Founder & Security Engineer',
      bio: 'Security engineer and systems architect specializing in continuous control verification, cryptographic audit trails, and deterministic incident resilience.',
      email: 'purvansh95b@gmail.com',
      linkedin: 'https://www.linkedin.com/in/purvanshbhatt',
      github: 'https://github.com/purvanshbhatt',
      isFounder: true,
    }
  ],
  socials: {
    github: 'https://github.com/purvanshbhatt/AIRS',
    linkedin: 'https://www.linkedin.com/in/purvanshbhatt',
    maidensail: 'https://maidensail.com/startup/resilai',
  },
};
