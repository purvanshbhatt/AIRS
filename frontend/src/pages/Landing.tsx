import { useState, useEffect, useRef, useMemo } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { motion, AnimatePresence, useScroll, useTransform, MotionValue } from 'framer-motion';
import {
  Shield,
  ChevronRight,
  BarChart3,
  Zap,
  CheckCircle,
  ArrowRight,
  Clock,
  Target,
  TrendingUp,
  ShieldCheck,
  Terminal as TerminalIcon,
  Copy,
  Check,
  Lock,
  Layers,
  Sparkles,
  Activity,
  Scale,
  BookOpen,
  Server,
  HardDrive,
  AlertTriangle,
  ChevronDown,
  Database,
  Network,
  Eye,
  RefreshCw,
  FileText,
  Plug,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import { SEOHead } from '../components/common/SEOHead';
import { useVertical, detectVerticalFromLocation } from '../contexts/VerticalContext';
import { DEFAULT_VERTICAL, getVerticalConfig, isVerticalKey } from '../config/verticals';
import type { VerticalKey, VerticalConfig } from '../types/vertical';

export interface LandingProps {
  defaultVertical?: VerticalKey;
}

const getPersonasForVertical = (vertical: VerticalKey) => {
  if (vertical === 'healthcare') {
    return [
      {
        icon: Shield,
        role: 'Executive (L1)',
        question: 'Can we treat patients and stay open?',
        description:
          'Get a deterministic, board ready answer on clinical continuity and ransomware resilience without interpreting complex technical logs.',
      },
      {
        icon: Target,
        role: 'Clinic Manager (L2)',
        question: 'What EHR or backup controls drifted?',
        description:
          'Understand how clinical workstation, Veeam backup, and Entra ID configurations drifted, with concrete remediation paths.',
      },
      {
        icon: TerminalIcon,
        role: 'Clinical IT / MSP (L3)',
        question: 'What telemetry proves our readiness?',
        description:
          'Trace findings directly to immutable backup verification, EHR uptime telemetry, and Active Directory audit logs.',
      },
    ];
  }
  if (vertical === 'legal') {
    return [
      {
        icon: Shield,
        role: 'Managing Partner (L1)',
        question: 'Is client confidentiality protected?',
        description:
          'Obtain verifiable confirmation that client matters, financial records, and firm operations withstand ransomware without breach.',
      },
      {
        icon: Target,
        role: 'Practice Director (L2)',
        question: 'What document vault risks need action?',
        description:
          'Pinpoint privileged access drift, document management system policy violations, and unencrypted attorney endpoints.',
      },
      {
        icon: TerminalIcon,
        role: 'Legal IT / MSP (L3)',
        question: 'What evidence proves ABA compliance?',
        description:
          'Cryptographic evidence connecting NetDocuments access logs, MFA enforcement, and secure repository retention.',
      },
    ];
  }
  return [
    {
      icon: Shield,
      role: 'Executive (L1)',
      question: 'Are we ready for an incident?',
      description:
        'Get a deterministic, board ready answer to your most critical question without navigating complex technical dashboards or interpreting raw logs.',
    },
    {
      icon: Target,
      role: 'Operations Lead (L2)',
      question: 'What drifted and what needs action?',
      description:
        'Understand exactly how your readiness posture drifted, why it matters to the business, and the clear remediation steps required to fix it.',
    },
    {
      icon: TerminalIcon,
      role: 'IT & Security (L3)',
      question: 'What evidence proves our posture?',
      description:
        'Trace every finding down to the raw evidence block, timestamp, and connector source. No guesswork, just cryptographic proof of your operational state.',
    },
  ];
};

const loopSteps = [
  {
    number: '01',
    title: 'Connect in 15 minutes',
    subtitle: 'Zero agents installed',
    description: 'Connect read only APIs for Microsoft 365, Veeam Backup, Wazuh, and Splunk without installing workstation drivers.',
    icon: Plug,
  },
  {
    number: '02',
    title: 'Verify deterministically',
    subtitle: 'Mathematical engine',
    description: 'Evaluate raw telemetry against HIPAA, NIST CSF 2.0, and ABA 477R controls with immutable SHA-256 evidence hashing.',
    icon: ShieldCheck,
  },
  {
    number: '03',
    title: 'Understand impact',
    subtitle: 'Plain English translation',
    description: 'Translate verified control gaps into operational recovery exposure, projected downtime SLAs, and financial risk.',
    icon: BarChart3,
  },
  {
    number: '04',
    title: 'Prove readiness',
    subtitle: 'One click boss reports',
    description: 'Export consultant grade executive PDFs and insurance binders pre mapped to Coalition, Chubb, and Travelers.',
    icon: FileText,
  },
];

const faqs = [
  {
    q: 'Do we need to install software agents on our servers or endpoints?',
    a: 'No. ResilAI is completely agentless. It connects exclusively through read only cloud APIs and established log forwarders including Microsoft Graph, Veeam Cloud Connect, Wazuh SIEM, and Splunk HEC. There are zero kernel drivers, background daemons, or workstation agents to deploy or patch.',
  },
  {
    q: 'Why deterministic mathematical scoring instead of an AI model?',
    a: 'Cyber insurance underwriters, regulators, and healthcare boards demand reproducible, auditable proof. Large language models can hallucinate risks or invent false reassurances. ResilAI calculates all readiness scores with deterministic mathematical formulas derived from raw telemetry, using Gemini strictly to synthesize the plain English narrative explanation constrained by the math.',
  },
  {
    q: 'How long does initial setup and telemetry ingestion take?',
    a: 'Most clinics and law practices complete initial API authorization in under 15 minutes. Once authorized, initial control verification and baseline readiness scoring populate within the first scan cycle.',
  },
  {
    q: 'Does sensitive patient health data (PHI) or confidential legal material leave our network?',
    a: 'Never. ResilAI ingests only security posture metadata, configuration attributes, and audit event heartbeats such as backup completion status, MFA enforcement flags, and disk encryption states. Raw patient charts and confidential legal documents are never accessed or transmitted.',
  },
  {
    q: 'Which infrastructure connectors are supported today?',
    a: 'Out of the box connectors include Microsoft 365 and Entra ID, Veeam Backup and Replication, Wazuh EDR and SIEM, Splunk SIEM, and AWS SSM. Custom webhook endpoints are also available for proprietary SIEM feeds.',
  },
  {
    q: 'Can our Managed Service Provider (MSP) manage ResilAI on our behalf?',
    a: 'Yes. ResilAI includes multi tenant workspace support and role based access controls, allowing MSPs and clinical IT partners to monitor readiness and export Monday morning boss reports across all their client practices from a single console.',
  },
];

function WordReveal({
  word,
  progress,
  range,
  isHighlight,
}: {
  word: string;
  progress: MotionValue<number>;
  range: [number, number];
  isHighlight?: boolean;
}) {
  const opacity = useTransform(progress, range, [0.25, 1]);
  return (
    <motion.span
      style={{ opacity }}
      className={`transition-colors duration-200 ${
        isHighlight ? 'text-ready-emerald font-bold' : 'text-on-surface'
      }`}
    >
      {word}
    </motion.span>
  );
}

function TaglineReveal() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ['start 85%', 'end 45%'],
  });

  const words = [
    'Questionnaires',
    'lie.',
    'Raw',
    'infrastructure',
    'evidence',
    'does',
    'not.',
    'ResilAI',
    'replaces',
    'subjective',
    'annual',
    'checklists',
    'with',
    'continuous,',
    'mathematical',
    'readiness',
    'scoring.',
  ];

  return (
    <section
      ref={containerRef}
      className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-y border-outline-variant/40 bg-surface-container-low/40"
    >
      <div className="max-w-4xl mx-auto text-center space-y-4">
        <p className="text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald">
          The Ground Truth Invariant
        </p>
        <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight leading-snug flex flex-wrap justify-center gap-x-2.5 sm:gap-x-3 gap-y-1.5 sm:gap-y-2 [text-wrap:balance]">
          {words.map((word, i) => {
            const start = i / words.length;
            const end = start + 1 / words.length;
            const isHighlight =
              word.includes('mathematical') ||
              word.includes('evidence') ||
              word.includes('not.');
            return (
              <WordReveal
                key={i}
                word={word}
                progress={scrollYProgress}
                range={[start, end]}
                isHighlight={isHighlight}
              />
            );
          })}
        </h2>
        <p className="text-sm sm:text-base text-on-surface-variant max-w-2xl mx-auto pt-4 leading-relaxed [text-wrap:pretty]">
          Security teams spend months filling static spreadsheets. Threat actors target real systems. We verify your operational infrastructure continuously so you know your recovery capability before an incident happens.
        </p>
      </div>
    </section>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border border-outline-variant/60 rounded-2xl bg-surface-container-low overflow-hidden transition-all">
      <button
        onClick={() => setOpen(!open)}
        className="w-full p-5 sm:p-6 text-left flex items-center justify-between gap-4 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald"
        aria-expanded={open}
      >
        <span className="text-sm sm:text-base font-semibold text-on-surface [text-wrap:balance]">
          {q}
        </span>
        <ChevronDown
          className={`w-5 h-5 text-on-surface-variant shrink-0 transition-transform duration-300 ${
            open ? 'rotate-180 text-ready-emerald' : ''
          }`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="px-5 sm:px-6 pb-5 sm:pb-6 text-xs sm:text-sm text-on-surface-variant leading-relaxed border-t border-outline-variant/40 pt-4 [text-wrap:pretty]">
              {a}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function Landing({ defaultVertical }: LandingProps = {}) {
  let navigate: ReturnType<typeof useNavigate> | undefined;
  try {
    navigate = useNavigate();
  } catch {
    // Graceful fallback if outside router
  }

  let locationSearch = '';
  let locationPathname = '';
  try {
    const loc = useLocation();
    locationSearch = loc.search;
    locationPathname = loc.pathname;
  } catch {
    // Outside Router
  }

  const { signInAsDemo, clearError } = useAuth();

  const detectedFromRoute = useMemo(() => {
    return detectVerticalFromLocation({
      search: locationSearch,
      pathname: locationPathname,
    });
  }, [locationSearch, locationPathname]);

  let vContext: ReturnType<typeof useVertical> | undefined;
  try {
    vContext = useVertical();
  } catch {
    // Graceful fallback when rendered outside VerticalProvider
  }

  const effectiveVertical: VerticalKey = useMemo(() => {
    if (detectedFromRoute.source === 'query') {
      return detectedFromRoute.vertical;
    }
    if (defaultVertical && isVerticalKey(defaultVertical)) {
      return defaultVertical;
    }
    if (detectedFromRoute.source === 'path') {
      return detectedFromRoute.vertical;
    }
    if (vContext?.currentVertical) {
      return vContext.currentVertical;
    }
    return DEFAULT_VERTICAL;
  }, [detectedFromRoute, defaultVertical, vContext?.currentVertical]);

  const effectiveConfig: VerticalConfig = useMemo(() => {
    if (vContext && vContext.currentVertical === effectiveVertical) {
      return vContext.config;
    }
    return getVerticalConfig(effectiveVertical);
  }, [vContext, effectiveVertical]);

  const currentVertical = effectiveVertical;
  const config = effectiveConfig;

  useEffect(() => {
    if (vContext?.setVertical && vContext.currentVertical !== effectiveVertical) {
      vContext.setVertical(effectiveVertical);
    }
  }, [effectiveVertical, vContext]);

  const handleEnterSandbox = async () => {
    clearError();
    try {
      await signInAsDemo();
    } catch {
      // ignore
    } finally {
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', config.demoOrgId);
      if (navigate) {
        navigate(`/morning-brief?vertical=${currentVertical}`, { replace: true });
      } else if (typeof window !== 'undefined') {
        window.location.href = `/morning-brief?vertical=${currentVertical}`;
      }
    }
  };

  // Interactive Product Canvas State
  type ProductTab = 'posture' | 'connectors' | 'ledger' | 'telemetry';
  const [productTab, setProductTab] = useState<ProductTab>('posture');

  // Terminal Subtabs State
  const [terminalTab, setTerminalTab] = useState<'telemetry' | 'request' | 'response'>('telemetry');
  const [copied, setCopied] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const initialLogs =
    currentVertical === 'healthcare'
      ? [
          `[2026-05-23T21:15:23Z] INITIALIZING HEALTHCARE TELEMETRY STREAM...`,
          `[2026-05-23T21:15:24Z] CONNECTED TO CLINICAL DAEMON // HOST: api.resilai.io`,
          `[2026-05-23T21:15:25Z] SYNCHRONIZING HIPAA & NIST CSF 2.0 CONTROL SETS...`,
        ]
      : currentVertical === 'legal'
      ? [
          `[2026-05-23T21:15:23Z] INITIALIZING LEGAL PRACTICE TELEMETRY STREAM...`,
          `[2026-05-23T21:15:24Z] CONNECTED TO DOCUMENT VAULT DAEMON // HOST: api.resilai.io`,
          `[2026-05-23T21:15:25Z] SYNCHRONIZING ABA 477R & SOC 2 CONTROL SETS...`,
        ]
      : [
          `[2026-05-23T21:15:23Z] INITIALIZING TELEMETRY STREAM...`,
          `[2026-05-23T21:15:24Z] CONNECTED TO DAEMON // HOST: api.resilai.io`,
          `[2026-05-23T21:15:25Z] SYNCHRONIZING NIST CSF 2.0 CONTROL SETS...`,
        ];

  const [telemetryLogs, setTelemetryLogs] = useState<string[]>(initialLogs);

  useEffect(() => {
    setTelemetryLogs(initialLogs);
  }, [currentVertical]);

  useEffect(() => {
    const healthcareEvents = [
      () => `[${new Date().toISOString()}] [INFO] Checked Epic EHR Clinical API - 200 OK`,
      () => `[${new Date().toISOString()}] [SYNC] Synced Veeam Cloud Connect Immutable Snapshot ID v-9481`,
      () => `[${new Date().toISOString()}] [POLL] Fetched clinical workstation posture: Score=86.5%`,
      () => `[${new Date().toISOString()}] [INFO] HIPAA Security Rule §164.312(a)(2)(iv) verified`,
      () => `[${new Date().toISOString()}] [WARN] Endpoint latency drift: Clinic Workstation 04 (3.2d since scan)`,
      () => `[${new Date().toISOString()}] [SYNC] Microsoft 365 Entra ID conditional access policy matched`,
      () => `[${new Date().toISOString()}] [INFO] Re-validating PACS imaging recovery SLA...`,
      () => `[${new Date().toISOString()}] [SUCCESS] All 340 clinical telemetry loops validated`,
    ];

    const legalEvents = [
      () => `[${new Date().toISOString()}] [INFO] Checked NetDocuments Vault API - 200 OK`,
      () => `[${new Date().toISOString()}] [SYNC] Synced ABA Formal Opinion 477R Control ID L-204`,
      () => `[${new Date().toISOString()}] [POLL] Fetched partner laptop disk encryption posture: Score=89.0%`,
      () => `[${new Date().toISOString()}] [INFO] Elite 3E practice management ledger sync completed`,
      () => `[${new Date().toISOString()}] [WARN] Privileged share link expiration warning: 24h remaining`,
      () => `[${new Date().toISOString()}] [SYNC] Azure AD MFA enforcement matched for litigation team`,
      () => `[${new Date().toISOString()}] [INFO] Re-validating client document vault backup snapshot...`,
      () => `[${new Date().toISOString()}] [SUCCESS] All 340 firm telemetry loops validated`,
    ];

    const generalEvents = [
      () => `[${new Date().toISOString()}] [INFO] Checked /health/system - 200 OK`,
      () => `[${new Date().toISOString()}] [SYNC] Synced MITRE ATT&CK Control ID T1548`,
      () => `[${new Date().toISOString()}] [POLL] Fetched latest GHI domain metrics: Score=82.0%`,
      () => `[${new Date().toISOString()}] [INFO] Active audit ledger sync completed successfully`,
      () => `[${new Date().toISOString()}] [WARN] Endpoint latency drift warning: min 14d, current 3.0d`,
      () => `[${new Date().toISOString()}] [SYNC] Telemetry logs matched OWASP AI Top 10 guidelines`,
      () => `[${new Date().toISOString()}] [INFO] Re-validating FastAPI core runtime status...`,
      () => `[${new Date().toISOString()}] [SUCCESS] All 340 engineering log loops validated`,
    ];

    const events =
      currentVertical === 'healthcare'
        ? healthcareEvents
        : currentVertical === 'legal'
        ? legalEvents
        : generalEvents;

    const interval = setInterval(() => {
      setTelemetryLogs(prev => {
        const next = [...prev, events[Math.floor(Math.random() * events.length)]()];
        if (next.length > 20) {
          next.shift();
        }
        return next;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, [currentVertical]);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [telemetryLogs]);

  const requestText = `curl -X GET "https://api.resilai.io/api/verification/latest/summary" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer resil_live_83fa9b12a819cd6f"`;

  const responseText = `{
  "status": "ready",
  "readiness_score": 84.5,
  "compliance_rating": "managed",
  "frameworks": ["SOC 2 Type II", "NIST CSF 2.0", "GDPR"],
  "dimensions": {
    "telemetry_logging": 92.0,
    "identity_visibility": 88.5,
    "detection_coverage": 81.0,
    "incident_response": 78.0,
    "upgrade_governance": 83.5
  },
  "last_updated": "2026-05-20T04:00:00Z"
}`;

  const handleCopy = async () => {
    const textToCopy =
      terminalTab === 'request'
        ? requestText
        : terminalTab === 'response'
        ? responseText
        : telemetryLogs.join('\n');
    await navigator.clipboard.writeText(textToCopy);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const seoConfig = useMemo(() => {
    if (currentVertical === 'healthcare') {
      return {
        title: 'Incident Readiness for Healthcare Organizations | ResilAI',
        description: 'Deterministic incident readiness and ransomware defense for healthcare clinics. Protect clinical EHR systems, guarantee 4-hour RTO, and verify continuous HIPAA compliance.',
        keywords: 'how to stop attacks on healthcare businesses, healthcare ransomware protection, clinical continuity, protect clinic EHR, HIPAA Security Rule, ResilAI',
        canonicalUrl: 'https://resilai.org/healthcare',
        schema: {
          '@context': 'https://schema.org',
          '@type': 'SoftwareApplication',
          name: 'ResilAI Healthcare Incident Readiness Platform',
          applicationCategory: 'SecurityApplication',
          operatingSystem: 'Cloud, Web',
          description: 'Deterministic continuous incident readiness and ransomware defense for healthcare clinics.',
          offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
        }
      };
    }
    if (currentVertical === 'legal') {
      return {
        title: 'Incident Readiness for Legal Firms & Law Practices | ResilAI',
        description: 'Deterministic incident readiness and client confidentiality verification for law practices. Protect document vaults, prevent ransomware, and comply with ABA Formal Opinion 477R.',
        keywords: 'how to stop attacks on legal firms, law firm cybersecurity, protect client confidentiality, law firm ransomware, ABA Formal Opinion 477R, ResilAI',
        canonicalUrl: 'https://resilai.org/legal',
        schema: {
          '@context': 'https://schema.org',
          '@type': 'SoftwareApplication',
          name: 'ResilAI Legal Incident Readiness Platform',
          applicationCategory: 'SecurityApplication',
          operatingSystem: 'Cloud, Web',
          description: 'Deterministic continuous incident readiness and client confidentiality verification for law practices.',
          offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
        }
      };
    }
    return {
      title: 'ResilAI — Continuous Incident Readiness & Cybersecurity Verification Platform',
      description: 'Transform fragmented security telemetry into deterministic readiness scoring, continuous compliance verification, and plain-English executive impact translation.',
      keywords: 'how to stop attacks on legal firms, how to stop attacks on healthcare businesses, AI incident readiness, cybersecurity verification, continuous security audit, NIST CSF 2.0, ResilAI',
      canonicalUrl: 'https://resilai.org/',
      schema: {
        '@context': 'https://schema.org',
        '@type': 'SoftwareApplication',
        name: 'ResilAI Incident Readiness Platform',
        applicationCategory: 'SecurityApplication',
        operatingSystem: 'Cloud, Web',
        description: 'Continuous incident readiness and deterministic cybersecurity verification platform.',
        offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' }
      }
    };
  }, [currentVertical]);

  return (
    <div className="min-h-screen bg-background text-on-surface selection:bg-ready-emerald/20 transition-colors duration-300 flex flex-col font-sans">
      <SEOHead {...seoConfig} />
      
      {/* Navigation Header */}
      <PublicNavbar transparent currentVertical={effectiveVertical} />

      {/* ========================================================================= */}
      {/* 1. HERO SECTION (Outcome + Audience, Single Offer, Startup Canvas)        */}
      {/* ========================================================================= */}
      <section className="relative pt-12 sm:pt-16 pb-20 overflow-hidden px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-12">
          
          {/* Header Copy Stack */}
          <div className="max-w-3xl mx-auto text-center space-y-6">
            
            {/* Industry Selector Switcher */}
            <div className="flex flex-wrap items-center justify-center gap-2 sm:gap-2.5">
              <button
                type="button"
                onClick={() => {
                  if (vContext?.setVertical) vContext.setVertical('healthcare');
                  if (navigate) navigate('/healthcare');
                }}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs sm:text-sm font-semibold border transition-all cursor-pointer shadow-xs ${
                  currentVertical === 'healthcare'
                    ? 'bg-ready-emerald/15 text-emerald-950 dark:text-ready-emerald border-ready-emerald/60 shadow-sm font-bold ring-1 ring-ready-emerald/40'
                    : 'bg-surface-container-low text-on-surface-variant border-outline-variant/60 hover:bg-surface-container-high hover:text-on-surface'
                }`}
              >
                <Activity className="w-3.5 h-3.5 text-ready-emerald shrink-0" />
                <span>Healthcare Clinics</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  if (vContext?.setVertical) vContext.setVertical('legal');
                  if (navigate) navigate('/legal');
                }}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs sm:text-sm font-semibold border transition-all cursor-pointer shadow-xs ${
                  currentVertical === 'legal'
                    ? 'bg-blue-500/15 text-blue-950 dark:text-blue-400 border-blue-500/60 shadow-sm font-bold ring-1 ring-blue-500/40'
                    : 'bg-surface-container-low text-on-surface-variant border-outline-variant/60 hover:bg-surface-container-high hover:text-on-surface'
                }`}
              >
                <Scale className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400 shrink-0" />
                <span>Law Practices</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  if (vContext?.setVertical) vContext.setVertical('general');
                  if (navigate) navigate('/');
                }}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-xs sm:text-sm font-semibold border transition-all cursor-pointer shadow-xs ${
                  currentVertical === 'general'
                    ? 'bg-surface-container text-on-surface border-outline font-bold shadow-sm'
                    : 'bg-surface-container-low text-on-surface-variant border-outline-variant/60 hover:bg-surface-container-high hover:text-on-surface'
                }`}
              >
                <Server className="w-3.5 h-3.5 text-on-surface-variant shrink-0" />
                <span>Enterprise Cloud</span>
              </button>
            </div>

            {/* Sub-badge Indicator */}
            <div
              className="inline-flex items-center gap-2 px-3.5 py-1 bg-surface-container-high text-on-surface-variant rounded-full text-xs font-mono font-medium border border-outline-variant/60"
              data-testid="hero-badge"
            >
              <span className="w-2 h-2 rounded-full bg-ready-emerald animate-pulse" />
              <span>
                {currentVertical === 'healthcare'
                  ? 'Continuous Clinical Continuity · HIPAA Verified'
                  : currentVertical === 'legal'
                  ? 'Document Vault Protection · ABA 477R Verified'
                  : 'Deterministic Engine · Non-LLM Readiness Scoring'}
              </span>
            </div>

            {/* Primary Headline */}
            <h1
              className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-on-surface [text-wrap:balance] leading-[1.1]"
              data-testid="landing-headline"
            >
              {currentVertical === 'healthcare' ? (
                <>
                  Know your clinic&apos;s ransomware readiness with{' '}
                  <span className="text-ready-emerald font-bold">mathematical proof</span>
                </>
              ) : currentVertical === 'legal' ? (
                <>
                  Know your firm&apos;s ransomware resilience with{' '}
                  <span className="text-blue-500 dark:text-blue-400 font-bold">verifiable proof</span>
                </>
              ) : (
                <>
                  Know and prove your ransomware readiness with{' '}
                  <span className="text-ready-emerald font-bold">deterministic evidence</span>
                </>
              )}
            </h1>

            {/* Core Question Subheadline */}
            <p
              className="text-lg sm:text-xl font-medium text-on-surface-variant max-w-2xl mx-auto leading-relaxed [text-wrap:pretty]"
              data-testid="landing-core-question"
            >
              {config.coreQuestion}
            </p>

            {/* Specific Value Description */}
            <p className="text-sm sm:text-base text-on-surface-variant/90 max-w-2xl mx-auto leading-relaxed [text-wrap:pretty]">
              {currentVertical === 'healthcare'
                ? "Connect Microsoft 365, Veeam Backup, Wazuh, and your EHR in under 15 minutes. Verify whether clinical workstations and immutable backups actually withstand attack before patient care is disrupted."
                : currentVertical === 'legal'
                ? "Connect Microsoft 365, NetDocuments, Veeam, and partner laptops in under 15 minutes. Verify whether privileged client files and matter repositories remain protected before an extortion attempt occurs."
                : "Connect Microsoft 365, Veeam Backup, Wazuh EDR, and Splunk in under 15 minutes. Transform raw telemetry into continuous mathematical readiness scoring without generative model hallucinations."}
            </p>

            {/* Primary Call to Action Stack */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
              <Link
                to={currentVertical === 'general' ? '/login' : `/login?vertical=${currentVertical}`}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 font-bold rounded-xl shadow-sm transition-all duration-200 active:scale-[0.98] min-h-[48px] text-sm text-center"
              >
                <span>Start Free Readiness Scan</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
              
              <button
                onClick={handleEnterSandbox}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-on-surface font-semibold rounded-xl border border-outline-variant/60 bg-surface-container-low hover:bg-surface-container-high transition-all active:scale-[0.98] min-h-[48px] text-sm text-center cursor-pointer"
                data-testid="hero-demo-cta"
              >
                <Sparkles className="w-4 h-4 text-ready-emerald shrink-0" />
                <span>Explore Live Sandbox Demo</span>
              </button>
            </div>

            {/* Risk Reversals */}
            <p className="text-xs text-on-surface-variant/80 font-medium">
              15 minute setup · 100% agentless · No credit card required · Instant posture report
            </p>

            {/* Proof Signals Strip */}
            <div className="pt-6 border-t border-outline-variant/40 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto text-left">
              <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/40">
                <span className="text-[11px] font-mono text-on-surface-variant uppercase block">Scoring Engine</span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block">100% Deterministic</span>
                <span className="text-[11px] text-on-surface-variant/80">No LLM guessing risk</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/40">
                <span className="text-[11px] font-mono text-on-surface-variant uppercase block">Deployment</span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block">&lt; 15 Minutes</span>
                <span className="text-[11px] text-on-surface-variant/80">Zero workstation agents</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/40">
                <span className="text-[11px] font-mono text-on-surface-variant uppercase block">Evidence Integrity</span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block">SHA-256 Ledger</span>
                <span className="text-[11px] text-on-surface-variant/80">Immutable audit chain</span>
              </div>
              <div className="p-3.5 rounded-xl bg-surface-container-low border border-outline-variant/40">
                <span className="text-[11px] font-mono text-on-surface-variant uppercase block">Recovery SLA</span>
                <span className="text-sm font-bold text-on-surface mt-0.5 block">4-Hour RTO Proof</span>
                <span className="text-[11px] text-on-surface-variant/80">Verified WORM storage</span>
              </div>
            </div>

          </div>

          {/* ========================================================================= */}
          {/* Hero Interactive Startup Product Canvas                                   */}
          {/* ========================================================================= */}
          <div className="max-w-5xl mx-auto rounded-2xl bg-surface-container-low border border-outline-variant/60 shadow-xl overflow-hidden text-left">
            
            {/* Canvas App Title Bar */}
            <div className="px-4 py-3 bg-surface-container border-b border-outline-variant/60 flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1.5">
                  <span className="w-3 h-3 rounded-full bg-rose-500/80 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block" />
                  <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block" />
                </div>
                <div className="flex items-center gap-2 pl-2 border-l border-outline-variant/60 text-xs font-semibold text-on-surface">
                  <span className="w-2 h-2 rounded-full bg-ready-emerald" />
                  <span>{config.demoOrgName}</span>
                  <span className="text-[10px] uppercase font-mono px-1.5 py-0.2 rounded bg-ready-emerald/10 text-ready-emerald border border-ready-emerald/20">
                    Active Workspace
                  </span>
                </div>
              </div>

              {/* View Switcher Tabs */}
              <div className="flex items-center gap-1 bg-surface-container-low p-1 rounded-xl border border-outline-variant/60 text-xs">
                <button
                  onClick={() => setProductTab('posture')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                    productTab === 'posture'
                      ? 'bg-surface-container-high text-on-surface shadow-xs'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Readiness Posture
                </button>
                <button
                  onClick={() => setProductTab('connectors')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                    productTab === 'connectors'
                      ? 'bg-surface-container-high text-on-surface shadow-xs'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Connector Fleet
                </button>
                <button
                  onClick={() => setProductTab('ledger')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                    productTab === 'ledger'
                      ? 'bg-surface-container-high text-on-surface shadow-xs'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Evidence Ledger
                </button>
                <button
                  onClick={() => setProductTab('telemetry')}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition-all cursor-pointer ${
                    productTab === 'telemetry'
                      ? 'bg-surface-container-high text-on-surface shadow-xs'
                      : 'text-on-surface-variant hover:text-on-surface'
                  }`}
                >
                  Live Stream
                </button>
              </div>
            </div>

            {/* Canvas App Body Area */}
            <div className="p-5 sm:p-7">
              {/* TAB 1: READINESS POSTURE */}
              {productTab === 'posture' && (
                <div className="space-y-6">
                  <div className="grid sm:grid-cols-12 gap-6 items-center">
                    
                    {/* Score Gauge */}
                    <div className="sm:col-span-5 p-5 rounded-2xl bg-surface-container border border-outline-variant/60 flex items-center gap-5">
                      <div className="relative w-24 h-24 rounded-full border-8 border-ready-emerald flex items-center justify-center shrink-0">
                        <div className="text-center">
                          <span className="text-2xl font-extrabold text-on-surface leading-none block">86</span>
                          <span className="text-[10px] font-mono text-on-surface-variant uppercase">out of 100</span>
                        </div>
                      </div>
                      <div className="space-y-1 text-left">
                        <span className="text-[10px] uppercase font-bold tracking-wider font-mono text-ready-emerald">
                          Managed Resilience
                        </span>
                        <h4 className="text-sm font-bold text-on-surface">Verified Incident Readiness</h4>
                        <p className="text-xs text-on-surface-variant leading-relaxed">
                          Deterministic mathematical score based on raw telemetry evidence. Zero model hallucinations.
                        </p>
                      </div>
                    </div>

                    {/* Operational SLAs & KPIs */}
                    <div className="sm:col-span-7 grid grid-cols-2 gap-3">
                      <div className="p-3.5 rounded-xl bg-surface-container border border-outline-variant/60">
                        <span className="text-[10px] uppercase font-mono text-on-surface-variant block mb-1">
                          Recovery SLA (RTO)
                        </span>
                        <span className="text-base font-bold text-ready-emerald">4.0 Hours</span>
                        <span className="text-[11px] text-on-surface-variant block mt-0.5">Verified WORM backup target</span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-surface-container border border-outline-variant/60">
                        <span className="text-[10px] uppercase font-mono text-on-surface-variant block mb-1">
                          Immutable Backups
                        </span>
                        <span className="text-base font-bold text-on-surface">100% Air Gapped</span>
                        <span className="text-[11px] text-on-surface-variant block mt-0.5">Veeam Cloud Connect active</span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-surface-container border border-outline-variant/60">
                        <span className="text-[10px] uppercase font-mono text-on-surface-variant block mb-1">
                          Active Endpoints
                        </span>
                        <span className="text-base font-bold text-on-surface">142 Monitored</span>
                        <span className="text-[11px] text-on-surface-variant block mt-0.5">Wazuh SIEM agents healthy</span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-surface-container border border-outline-variant/60">
                        <span className="text-[10px] uppercase font-mono text-on-surface-variant block mb-1">
                          Regulatory Scope
                        </span>
                        <span className="text-base font-bold text-ready-emerald">
                          {currentVertical === 'healthcare' ? 'HIPAA Verified' : currentVertical === 'legal' ? 'ABA 477R Verified' : 'NIST CSF 2.0'}
                        </span>
                        <span className="text-[11px] text-on-surface-variant block mt-0.5">Continuous audit alignment</span>
                      </div>
                    </div>

                  </div>

                  {/* Domain Bars */}
                  <div className="space-y-3 pt-2">
                    <span className="text-xs font-mono uppercase font-bold text-on-surface-variant block">
                      Critical System Posture Breakdown ({config.displayName})
                    </span>
                    <div className="grid sm:grid-cols-2 gap-3 text-xs">
                      {config.criticalSystems.slice(0, 4).map((sys, idx) => {
                        const score = 94 - idx * 4;
                        return (
                          <div key={sys} className="p-3 rounded-xl bg-surface-container border border-outline-variant/40">
                            <div className="flex justify-between items-center mb-1.5 font-medium">
                              <span className="text-on-surface truncate">{sys}</span>
                              <span className="font-mono font-bold text-ready-emerald">{score}%</span>
                            </div>
                            <div className="h-2 rounded-full bg-surface-container-high overflow-hidden">
                              <div
                                className="h-full bg-ready-emerald rounded-full transition-all duration-500"
                                style={{ width: `${score}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: CONNECTORS FLEET */}
              {productTab === 'connectors' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-outline-variant/40">
                    <span className="text-xs font-mono uppercase font-bold text-on-surface-variant">
                      Connected Infrastructure Fleet (Agentless Read Only APIs)
                    </span>
                    <span className="text-xs font-mono font-semibold text-ready-emerald">
                      4 / 4 Connectors Ingesting
                    </span>
                  </div>

                  <div className="grid sm:grid-cols-2 gap-3.5">
                    <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/60 flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h5 className="text-xs font-bold text-on-surface">Microsoft 365 & Entra ID</h5>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-ready-emerald/10 text-ready-emerald font-bold">
                            LIVE SYNC
                          </span>
                        </div>
                        <p className="text-xs text-on-surface-variant">
                          MFA enforcement, privileged account access, and tenant security baseline.
                        </p>
                        <span className="text-[10px] font-mono text-on-surface-variant/70 block pt-1">
                          Last heartbeat: 42 seconds ago via Graph API
                        </span>
                      </div>
                      <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                    </div>

                    <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/60 flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h5 className="text-xs font-bold text-on-surface">Veeam Backup & Replication</h5>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-ready-emerald/10 text-ready-emerald font-bold">
                            WORM LOCKED
                          </span>
                        </div>
                        <p className="text-xs text-on-surface-variant">
                          Backup job status, air gap retention validation, and immutable repository verification.
                        </p>
                        <span className="text-[10px] font-mono text-on-surface-variant/70 block pt-1">
                          Last snapshot: 12 minutes ago · 0 corrupted blocks
                        </span>
                      </div>
                      <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                    </div>

                    <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/60 flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h5 className="text-xs font-bold text-on-surface">Wazuh SIEM & EDR Fleet</h5>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-ready-emerald/10 text-ready-emerald font-bold">
                            142 NODES
                          </span>
                        </div>
                        <p className="text-xs text-on-surface-variant">
                          Endpoint vulnerability scans, integrity monitoring, and privilege escalation alerts.
                        </p>
                        <span className="text-[10px] font-mono text-on-surface-variant/70 block pt-1">
                          Endpoint agent status: 100% active
                        </span>
                      </div>
                      <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                    </div>

                    <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/60 flex items-start justify-between">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h5 className="text-xs font-bold text-on-surface">Splunk SIEM Forwarder</h5>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-ready-emerald/10 text-ready-emerald font-bold">
                            HEC ACTIVE
                          </span>
                        </div>
                        <p className="text-xs text-on-surface-variant">
                          Centralized security event streams and lateral breach detection rule matching.
                        </p>
                        <span className="text-[10px] font-mono text-on-surface-variant/70 block pt-1">
                          Ingestion latency: 110ms average
                        </span>
                      </div>
                      <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: EVIDENCE LEDGER */}
              {productTab === 'ledger' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between pb-2 border-b border-outline-variant/40">
                    <span className="text-xs font-mono uppercase font-bold text-on-surface-variant">
                      Cryptographic Evidence Ledger (Immutable Proof Chain)
                    </span>
                    <span className="text-xs font-mono text-ready-emerald font-bold">
                      SHA-256 HASH CHAIN VALIDATED
                    </span>
                  </div>

                  <div className="p-4 rounded-xl bg-surface-container border border-outline-variant/60 font-mono text-xs space-y-3">
                    <div className="flex items-center justify-between text-on-surface-variant pb-2 border-b border-outline-variant/40">
                      <span>Ledger Block #84920</span>
                      <span className="text-ready-emerald font-bold">SOC 2 / HIPAA CONTROL PASS</span>
                    </div>

                    <div className="grid sm:grid-cols-2 gap-3 text-[11px]">
                      <div>
                        <span className="text-on-surface-variant block mb-0.5">Control Dimension</span>
                        <span className="text-on-surface font-semibold">
                          {currentVertical === 'healthcare'
                            ? 'HIPAA §164.312(a)(2)(iv) Data Encryption at Rest'
                            : currentVertical === 'legal'
                            ? 'ABA Formal Opinion 477R Privileged File Retention'
                            : 'NIST CSF 2.0 PR.DS-01 Data Security Baseline'}
                        </span>
                      </div>
                      <div>
                        <span className="text-on-surface-variant block mb-0.5">Connector Provenance</span>
                        <span className="text-on-surface font-semibold">Veeam Cloud Connect API (Air Gap Target)</span>
                      </div>
                    </div>

                    <div className="p-3 bg-surface-container-low rounded-lg border border-outline-variant/40 text-[11px] space-y-1">
                      <div className="flex justify-between">
                        <span className="text-on-surface-variant">Payload SHA-256:</span>
                        <span className="text-ready-emerald font-mono truncate max-w-[280px]">
                          4f89d3a7e2b109c48e89f71b2d01e4a3b891c78...
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-on-surface-variant">Verification Result:</span>
                        <span className="text-on-surface">Immutable WORM retention lock confirmed for 30 days.</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: LIVE TELEMETRY STREAM */}
              {productTab === 'telemetry' && (
                <div className="rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs overflow-hidden">
                  <div className="flex items-center justify-between px-3 py-2 border-b border-slate-800 bg-slate-900/80">
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={() => setTerminalTab('telemetry')}
                        className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                          terminalTab === 'telemetry' ? 'bg-slate-800 text-ready-emerald' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Live Stream
                      </button>
                      <button
                        onClick={() => setTerminalTab('request')}
                        className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                          terminalTab === 'request' ? 'bg-slate-800 text-primary-400' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        cURL API
                      </button>
                      <button
                        onClick={() => setTerminalTab('response')}
                        className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                          terminalTab === 'response' ? 'bg-slate-800 text-ready-emerald' : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        JSON Schema
                      </button>
                    </div>

                    <button
                      onClick={handleCopy}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] cursor-pointer"
                    >
                      {copied ? <Check className="w-3 h-3 text-ready-emerald" /> : <Copy className="w-3 h-3" />}
                      <span>{copied ? 'Copied' : 'Copy'}</span>
                    </button>
                  </div>

                  <div ref={logContainerRef} className="p-3.5 h-[220px] overflow-auto text-[11px] text-slate-300 select-text leading-relaxed">
                    <AnimatePresence mode="wait">
                      {terminalTab === 'telemetry' ? (
                        <div className="space-y-1">
                          {telemetryLogs.map((log, index) => {
                            let color = 'text-slate-300';
                            if (log.includes('[WARN]')) color = 'text-amber-400 font-semibold';
                            if (log.includes('[SUCCESS]') || log.includes('Score=')) color = 'text-ready-emerald';
                            if (log.includes('[SYNC]')) color = 'text-primary-400';
                            return (
                              <div key={index} className={color}>
                                <span className="text-slate-600 select-none">&gt;</span> {log}
                              </div>
                            );
                          })}
                        </div>
                      ) : terminalTab === 'request' ? (
                        <pre className="whitespace-pre-wrap text-primary-300">{requestText}</pre>
                      ) : (
                        <pre className="whitespace-pre text-ready-emerald">{responseText}</pre>
                      )}
                    </AnimatePresence>
                  </div>
                </div>
              )}
            </div>

            {/* Canvas App Footer Banner */}
            <div className="px-5 py-3 bg-surface-container border-t border-outline-variant/60 flex flex-wrap items-center justify-between text-xs text-on-surface-variant">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-ready-emerald" />
                <span>Deterministic Mathematical Scoring Active</span>
              </span>
              <span className="font-mono text-ready-emerald font-semibold">100% Non-LLM Calculation</span>
            </div>

          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* 2. MANDATORY TAGLINE REVEAL (Section B11 from Skill)                      */}
      {/* ========================================================================= */}
      <TaglineReveal />

      {/* ========================================================================= */}
      {/* 3. PROBLEM TO SOLUTION (Manual GRC vs Deterministic Engine)               */}
      {/* ========================================================================= */}
      <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40">
        <div className="max-w-7xl mx-auto space-y-12">
          
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <p className="text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald">
              The Reality Gap
            </p>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
              Annual security spreadsheets lie. Your infrastructure cannot.
            </h2>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed [text-wrap:pretty]">
              Traditional GRC asks teams to self attest to security policies once a year. When ransomware hits, self attestation offers zero recovery capability.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
            
            {/* The Old Way */}
            <div className="p-6 sm:p-8 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-6">
              <div className="space-y-1.5">
                <span className="text-xs font-mono uppercase font-bold text-rose-500">The Status Quo</span>
                <h3 className="text-xl font-bold text-on-surface">Annual GRC &amp; AI Questionnaires</h3>
                <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
                  Static yes/no checklists and AI chatbots that guess risk posture without looking at actual configurations.
                </p>
              </div>

              <ul className="space-y-3 text-xs sm:text-sm text-on-surface-variant">
                <li className="flex items-start gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">✕</span>
                  <span>Self reported questionnaires filled out once every 12 months</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">✕</span>
                  <span>LLMs hallucinating risk scores based on subjective text inputs</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">✕</span>
                  <span>Unverified backup air gaps that fail during real ransomware incidents</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <span className="w-4 h-4 rounded-full bg-rose-500/10 text-rose-500 flex items-center justify-center font-bold text-xs shrink-0 mt-0.5">✕</span>
                  <span>Cyber insurance underwriters rejecting vague self assessments</span>
                </li>
              </ul>
            </div>

            {/* The ResilAI Way */}
            <div className="p-6 sm:p-8 rounded-2xl bg-surface-container-low border-2 border-ready-emerald/50 space-y-6 shadow-sm ring-1 ring-ready-emerald/20">
              <div className="space-y-1.5">
                <span className="text-xs font-mono uppercase font-bold text-ready-emerald">The ResilAI Standard</span>
                <h3 className="text-xl font-bold text-on-surface">Deterministic Mathematical Verification</h3>
                <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
                  Continuous ingestion from Microsoft 365, Veeam, and Wazuh calculating real readiness without model hallucinations.
                </p>
              </div>

              <ul className="space-y-3 text-xs sm:text-sm text-on-surface">
                <li className="flex items-start gap-2.5">
                  <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                  <span>Continuous 24/7 telemetry sync from real infrastructure APIs</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                  <span>100% deterministic mathematical scoring with zero AI hallucination</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                  <span>Cryptographic proof of immutable WORM storage and 4-hour RTO</span>
                </li>
                <li className="flex items-start gap-2.5">
                  <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0 mt-0.5" />
                  <span>Pre mapped insurance binders accepted by Coalition, Chubb, and Travelers</span>
                </li>
              </ul>
            </div>

          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* 4. THREE-STEP OPERATIONAL ENGINE (How It Works)                           */}
      {/* ========================================================================= */}
      <section id="how-it-works" className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40 bg-surface-container-low/40">
        <div className="max-w-7xl mx-auto space-y-12">
          
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <p className="text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald">
              The 4-Step Operational Engine
            </p>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
              How ResilAI verifies and proves your readiness
            </h2>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed [text-wrap:pretty]">
              A complete pipeline taking raw infrastructure telemetry to executive board reports in four deterministic steps.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {loopSteps.map((step) => {
              const Icon = step.icon;
              return (
                <div
                  key={step.title}
                  className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-ready-emerald bg-ready-emerald/10 border border-ready-emerald/20 px-2 py-0.5 rounded">
                        Step {step.number}
                      </span>
                      <Icon className="w-5 h-5 text-ready-emerald" />
                    </div>

                    <div>
                      <h4 className="text-base font-bold text-on-surface">{step.title}</h4>
                      <span className="text-xs font-mono text-on-surface-variant/80">{step.subtitle}</span>
                    </div>

                    <p className="text-xs text-on-surface-variant leading-relaxed">
                      {step.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* 5. MULTI-STAKEHOLDER TRANSLATION                                          */}
      {/* ========================================================================= */}
      <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40">
        <div className="max-w-7xl mx-auto space-y-12">
          
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <p className="text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald">
              Unified Language
            </p>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
              One source of truth, translated for every leader
            </h2>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed [text-wrap:pretty]">
              Technical telemetry is translated into the exact metrics that executives, practice leads, and sysadmins need.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {getPersonasForVertical(currentVertical).map((p) => {
              const Icon = p.icon;
              return (
                <div
                  key={p.role}
                  className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-4 text-left flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/20 flex items-center justify-center text-ready-emerald">
                      <Icon className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="text-xs font-mono font-bold text-ready-emerald uppercase">{p.role}</span>
                      <h4 className="text-sm sm:text-base font-bold text-on-surface mt-0.5 [text-wrap:balance]">
                        &quot;{p.question}&quot;
                      </h4>
                    </div>
                    <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed [text-wrap:pretty]">
                      {p.description}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* 6. CYBER DEFENSE PLAYBOOKS & GUIDES                                       */}
      {/* ========================================================================= */}
      <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40 bg-surface-container-low/40">
        <div className="max-w-7xl mx-auto space-y-12">
          
          <div className="max-w-3xl mx-auto text-center space-y-4">
            <p className="text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald">
              Operational Defense Playbooks
            </p>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
              How to stop attacks on high risk organizations
            </h2>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed [text-wrap:pretty]">
              Tested playbooks designed specifically for clinics and law practices facing targeted extortion.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-6 max-w-5xl mx-auto">
            
            {/* Legal Card */}
            <div className="p-6 sm:p-8 rounded-2xl bg-surface-container-low border border-outline-variant/60 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-blue-500 uppercase">Legal Sector Playbook</span>
                  <Scale className="w-5 h-5 text-blue-500" />
                </div>
                <h3 className="text-xl font-bold text-on-surface">How to Stop Attacks on Legal Firms</h3>
                <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
                  Protect confidential client matters, satisfy ABA Formal Opinion 477R, enforce hardware MFA, and secure NetDocuments document vaults against extortion.
                </p>
                <ul className="space-y-2 text-xs text-on-surface pt-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0" />
                    <span>Ethical wall and matter level Zero Trust access segregation</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0" />
                    <span>Immutable air gapped backups (WORM storage) for case archives</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0" />
                    <span>Continuous automated telemetry verification vs annual checklists</span>
                  </li>
                </ul>
              </div>

              <div>
                <Link
                  to="/solutions/legal-firm-cyber-attacks"
                  className="inline-flex items-center gap-2 text-xs sm:text-sm font-bold text-primary-600 dark:text-primary-400 hover:underline"
                >
                  <span>Read Complete Legal Defense Guide</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

            {/* Healthcare Card */}
            <div className="p-6 sm:p-8 rounded-2xl bg-surface-container-low border border-outline-variant/60 flex flex-col justify-between space-y-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-ready-emerald uppercase">Healthcare Playbook</span>
                  <Activity className="w-5 h-5 text-ready-emerald" />
                </div>
                <h3 className="text-xl font-bold text-on-surface">How to Stop Attacks on Healthcare Businesses</h3>
                <p className="text-xs sm:text-sm text-on-surface-variant leading-relaxed">
                  Prevent clinical EHR shutdowns, isolate diagnostic imaging systems, guarantee 4-hour RTO, and enforce continuous HIPAA Security Rule compliance.
                </p>
                <ul className="space-y-2 text-xs text-on-surface pt-2">
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0" />
                    <span>Clinical EHR micro segmentation and network isolation</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0" />
                    <span>3-2-1-1-0 Veeam and S3 immutable backups ransomware cannot delete</span>
                  </li>
                  <li className="flex items-center gap-2">
                    <CheckCircle className="w-4 h-4 text-ready-emerald shrink-0" />
                    <span>Daily executive Morning Brief answering: &quot;Can we safely treat patients?&quot;</span>
                  </li>
                </ul>
              </div>

              <div>
                <Link
                  to="/solutions/healthcare-cyber-attacks"
                  className="inline-flex items-center gap-2 text-xs sm:text-sm font-bold text-ready-emerald hover:underline"
                >
                  <span>Read Complete Healthcare Defense Guide</span>
                  <ArrowRight className="w-4 h-4" />
                </Link>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* 7. FREQUENTLY ASKED QUESTIONS (Objection Handling Accordion)              */}
      {/* ========================================================================= */}
      <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40">
        <div className="max-w-4xl mx-auto space-y-10">
          
          <div className="text-center space-y-4">
            <p className="text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald">
              Common Questions
            </p>
            <h2 className="text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
              Frequently asked questions
            </h2>
            <p className="text-sm sm:text-base text-on-surface-variant leading-relaxed [text-wrap:pretty]">
              Everything you need to know about our agentless ingestion and deterministic scoring model.
            </p>
          </div>

          <div className="space-y-3">
            {faqs.map((faq) => (
              <FAQItem key={faq.q} q={faq.q} a={faq.a} />
            ))}
          </div>

        </div>
      </section>

      {/* ========================================================================= */}
      {/* 8. FINAL HIGH-CONVERSION CTA                                              */}
      {/* ========================================================================= */}
      <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 bg-surface-container-low/40">
        <div className="max-w-3xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-surface-container-high text-on-surface-variant rounded-full text-xs font-mono font-medium border border-outline-variant/60">
            <Clock className="w-3.5 h-3.5 text-ready-emerald" />
            <span>Deterministic verification in 15 minutes</span>
          </div>

          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
            Know your ransomware readiness before an incident proves otherwise
          </h2>

          <p className="text-sm sm:text-base text-on-surface-variant max-w-xl mx-auto leading-relaxed [text-wrap:pretty]">
            Connect your infrastructure read only APIs in 15 minutes. Generate your first deterministic readiness report and Monday morning boss brief today.
          </p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
            <Link
              to={currentVertical === 'general' ? '/login' : `/login?vertical=${currentVertical}`}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 font-bold rounded-xl shadow-sm transition-all duration-200 active:scale-[0.98] min-h-[48px] text-sm text-center"
            >
              <span>Start Free Readiness Scan</span>
              <ArrowRight className="w-4 h-4" />
            </Link>

            <button
              onClick={handleEnterSandbox}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-on-surface font-semibold rounded-xl border border-outline-variant/60 bg-surface-container-low hover:bg-surface-container-high transition-all active:scale-[0.98] min-h-[48px] text-sm text-center cursor-pointer"
              data-testid="bottom-demo-cta"
            >
              <Sparkles className="w-4 h-4 text-ready-emerald shrink-0" />
              <span>Explore Demo Sandbox ({config.demoOrgName})</span>
            </button>
          </div>

          <p className="text-xs text-on-surface-variant/80 font-medium pt-2">
            No credit card required · 14-day evaluation access · Instant executive PDF export
          </p>
        </div>
      </section>

      {/* Footer */}
      <Footer />
    </div>
  );
}
