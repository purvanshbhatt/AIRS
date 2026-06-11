import { useState, useEffect } from 'react';

export interface TrustEvent {
  id: string;
  timestamp: string;
  controlId: string;
  controlName: string;
  connector: string;
  oldState: 'Self-Attested' | 'Not Verified' | 'Partially Verified';
  newState: 'Verified' | 'Partially Verified' | 'Self-Attested';
  status: 'success' | 'warning' | 'info';
  details: string;
  evidenceHash: string;
}

export interface TrustTrendPoint {
  date: string;
  verified: number;
  attested: number;
  unverified: number;
}

export interface MockTrustData {
  overallScore: number;
  verifiedTelemetryPct: number;
  selfAttestedPct: number;
  verificationSummary: {
    verified: number;
    partiallyVerified: number;
    selfAttested: number;
    notVerified: number;
  };
  trendData: TrustTrendPoint[];
  events: TrustEvent[];
}

const mockData: MockTrustData = {
  overallScore: 84,
  verifiedTelemetryPct: 65,
  selfAttestedPct: 35,
  verificationSummary: {
    verified: 22,
    partiallyVerified: 14,
    selfAttested: 12,
    notVerified: 8,
  },
  trendData: [
    { date: 'Apr 17', verified: 8, attested: 32, unverified: 16 },
    { date: 'Apr 24', verified: 11, attested: 29, unverified: 16 },
    { date: 'May 01', verified: 14, attested: 27, unverified: 15 },
    { date: 'May 08', verified: 17, attested: 24, unverified: 15 },
    { date: 'May 15', verified: 19, attested: 21, unverified: 16 },
    { date: 'May 22', verified: 20, attested: 18, unverified: 18 },
    { date: 'May 29', verified: 22, attested: 12, unverified: 22 },
  ],
  events: [
    {
      id: 'evt-001',
      timestamp: '2026-05-29T21:40:00Z',
      controlId: 'NIST PR.DS-1',
      controlName: 'Data-at-rest encryption',
      connector: 'Microsoft Intune',
      oldState: 'Self-Attested',
      newState: 'Verified',
      status: 'success',
      details: 'Microsoft Intune API verified BitLocker disk encryption is active on 98.4% of corporate laptop fleet.',
      evidenceHash: 'sha256:7f83b27b9492167c132890ef9892c90f230da1d02c918efca21074e2d30fa982',
    },
    {
      id: 'evt-002',
      timestamp: '2026-05-29T18:15:32Z',
      controlId: 'CIS Control 6.1',
      controlName: 'Access control visibility',
      connector: 'Okta Identity Cloud',
      oldState: 'Not Verified',
      newState: 'Verified',
      status: 'success',
      details: 'Okta configuration audit verified MFA rules are enforced for 100% of administrative accounts.',
      evidenceHash: 'sha256:3a9d18efca21074e2d30fa9827f83b27b9492167c132890ef9892c90f230da1d0',
    },
    {
      id: 'evt-003',
      timestamp: '2026-05-28T14:22:05Z',
      controlId: 'NIST DE.AE-1',
      controlName: 'Security continuous monitoring',
      connector: 'Splunk Ingestion HEC',
      oldState: 'Self-Attested',
      newState: 'Partially Verified',
      status: 'warning',
      details: 'Splunk HEC endpoint validated active log forwarding for 42/45 staging virtual machines. 3 hosts pending sync.',
      evidenceHash: 'sha256:f230da1d02c918efca21074e2d30fa9827f83b27b9492167c132890ef9892c90',
    },
    {
      id: 'evt-004',
      timestamp: '2026-05-27T09:05:11Z',
      controlId: 'OWASP A06:2021',
      controlName: 'Vulnerable components scanner',
      connector: 'Wazuh SIEM Manager',
      oldState: 'Self-Attested',
      newState: 'Verified',
      status: 'success',
      details: 'Wazuh Agent API vulnerability scan verified zero active CVEs of CRITICAL severity outstanding in staging docker hosts.',
      evidenceHash: 'sha256:d30fa9827f83b27b9492167c132890ef9892c90f230da1d02c918efca21074e2',
    },
    {
      id: 'evt-005',
      timestamp: '2026-05-26T11:58:43Z',
      controlId: 'CIS Control 8.1',
      controlName: 'Establish audit logs',
      connector: 'AWS GuardDuty',
      oldState: 'Not Verified',
      newState: 'Partially Verified',
      status: 'info',
      details: 'AWS API verified GuardDuty threat logs are enabled in us-east-1 and us-west-2 regions. Global configuration pending.',
      evidenceHash: 'sha256:1a82c3d4e5f67074e2d30fa9827f83b27b9492167c132890ef9892c90f230da1d',
    },
  ],
};

export function useMockTrustData(assessmentId?: string) {
  const [data, setData] = useState<MockTrustData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    // Simulate API fetch delay
    const timer = setTimeout(() => {
      setData(mockData);
      setLoading(false);
    }, 450);

    return () => clearTimeout(timer);
  }, [assessmentId]);

  return { data, loading };
}
