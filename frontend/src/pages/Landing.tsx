import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Shield,
  ChevronRight,
  BarChart3,
  FileText,
  Zap,
  CheckCircle,
  Github,
  Mail,
  ArrowRight,
  Clock,
  Target,
  TrendingUp,
  ShieldCheck,
  Calendar,
  Cpu,
  Terminal as TerminalIcon,
  Copy,
  Check,
  Lock,
  Layers,
} from 'lucide-react';
import ThemeToggle from '../components/ui/ThemeToggle';

const features = [
  {
    icon: Target,
    title: 'Comprehensive Assessment',
    description:
      'Evaluate your security posture across 5 critical domains with 30+ targeted questions designed by incident response experts.',
  },
  {
    icon: ShieldCheck,
    title: 'Compliance Intelligence',
    description:
      'Auto-detect applicable frameworks — SOC 2, HIPAA, PCI-DSS, CMMC, GDPR — based on your organization profile. Know what\'s mandatory vs. recommended.',
  },
  {
    icon: BarChart3,
    title: 'Instant Scoring & Insights',
    description:
      'Get immediate visibility into your readiness level with weighted scores, maturity ratings, and prioritized findings.',
  },
  {
    icon: Calendar,
    title: 'Audit Calendar & Forecasts',
    description:
      'Schedule upcoming audits, get countdown alerts, and run pre-audit risk forecasts that cross-reference your live findings.',
  },
  {
    icon: FileText,
    title: 'Executive-Ready Reports',
    description:
      'Generate professional PDF reports with AI-powered narratives, actionable recommendations, and benchmark comparisons.',
  },
  {
    icon: Cpu,
    title: 'Tech Stack Lifecycle',
    description:
      'Track component versions and LTS status. Get deterministic risk classification for EOL, deprecated, and outdated dependencies.',
  },
];

const stats = [
  { value: '9+', label: 'Compliance Frameworks' },
  { value: '5', label: 'Security Domains' },
  { value: '30+', label: 'Assessment Questions' },
  { value: '<5min', label: 'Time to Complete' },
];

export default function Landing() {
  const [terminalTab, setTerminalTab] = useState<'telemetry' | 'request' | 'response'>('telemetry');
  const [copied, setCopied] = useState(false);
  const logContainerRef = useRef<HTMLDivElement>(null);

  const [telemetryLogs, setTelemetryLogs] = useState<string[]>([
    `[2026-05-23T21:15:23Z] INITIALIZING TELEMETRY STREAM...`,
    `[2026-05-23T21:15:24Z] CONNECTED TO DAEMON // HOST: api.resilai.io`,
    `[2026-05-23T21:15:25Z] SYNCHRONIZING NIST CSF 2.0 CONTROL SETS...`
  ]);

  useEffect(() => {
    const events = [
      () => `[${new Date().toISOString()}] [INFO] Checked /health/system - 200 OK`,
      () => `[${new Date().toISOString()}] [SYNC] Synced MITRE ATT&CK Control ID T1548`,
      () => `[${new Date().toISOString()}] [POLL] Fetched latest GHI domain metrics: Score=82.0%`,
      () => `[${new Date().toISOString()}] [INFO] Active audit ledger sync completed successfully`,
      () => `[${new Date().toISOString()}] [WARN] Endpoint latency drift warning: min 14d, current 3.0d`,
      () => `[${new Date().toISOString()}] [SYNC] Telemetry logs matched OWASP AI Top 10 guidelines`,
      () => `[${new Date().toISOString()}] [INFO] Re-validating FastAPI core runtime status...`,
      () => `[${new Date().toISOString()}] [SUCCESS] All 340 engineering log loops validated`
    ];

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
  }, []);

  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [telemetryLogs]);

  const requestText = `curl -X GET "https://api.resilai.io/api/assessments/latest/summary" \\
  -H "Accept: application/json" \\
  -H "Authorization: Bearer resil_live_83fa9b12a819cd6f"`;

  const responseText = `{
  "status": "ready",
  "overall_readiness_score": 84.5,
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

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-blue-500/20 transition-colors duration-300">
      {/* Navigation */}
      <nav 
        className="fixed left-0 right-0 z-50 bg-white/85 dark:bg-slate-950/85 backdrop-blur-md border-b border-slate-200/80 dark:border-slate-800/80 transition-colors duration-300"
        style={{ top: 'var(--banner-height, 0px)' }}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <img src="/logo_header.svg" alt="ResilAI Logo" className="h-11 w-auto dark:brightness-0 dark:invert transition-all duration-300" />
            </div>
            
            <div className="flex items-center gap-4">
              <div className="hidden md:flex items-center gap-5">
                <Link
                  to="/about"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  About
                </Link>
                <Link
                  to="/security"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  Security
                </Link>
                <Link
                  to="/status"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  Status
                </Link>
                <Link
                  to="/pilot"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  Request Pilot
                </Link>
                <Link
                  to="/dashboard"
                  className="text-sm font-medium text-slate-600 dark:text-slate-300 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                >
                  Dashboard
                </Link>
              </div>

              <div className="h-6 w-px bg-slate-200 dark:bg-slate-800 hidden md:block" />

              <ThemeToggle />

              <Link
                to="/assessment/quick"
                className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-950 text-sm font-semibold rounded-xl hover:bg-slate-800 dark:hover:bg-slate-200 transition-all shadow-sm"
              >
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 overflow-hidden px-4 sm:px-6 lg:px-8">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-blue-500/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute top-1/3 left-1/4 w-[300px] h-[300px] bg-cyan-500/10 rounded-full blur-[80px] pointer-events-none" />

        <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 space-y-6 text-left">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 rounded-full text-xs font-semibold tracking-wide border border-blue-100 dark:border-blue-900/50"
            >
              <Zap className="w-3.5 h-3.5" />
              Continuous Readiness & AI Security Lifecycle
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] text-slate-900 dark:text-slate-50"
            >
              Neutralizing Subjectivity <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 to-cyan-500 dark:from-blue-400 dark:to-cyan-300">
                in Compliance Audits
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed"
            >
              ResilAI continuously validates your system perimeters against active framework targets. Turn subjective readiness checks into deterministic, auditable compliance telemetry.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap items-center gap-4 pt-4"
            >
              <Link
                to="/pilot"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-gradient-to-br from-blue-600 to-cyan-500 text-white font-semibold rounded-2xl hover:shadow-lg hover:shadow-blue-500/25 transition-all duration-300 active:scale-[0.98]"
              >
                Request Enterprise Pilot
                <ChevronRight className="w-5 h-5" />
              </Link>
              <Link
                to="/dashboard"
                className="inline-flex items-center gap-2 px-6 py-3.5 text-slate-700 dark:text-slate-300 font-semibold rounded-2xl border border-slate-300 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/60 transition-all active:scale-[0.98]"
              >
                Launch Sandbox Demo
                <ArrowRight className="w-4 h-4 text-slate-400" />
              </Link>
            </motion.div>
          </div>

          {/* Interactive Mock Terminal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-5 relative"
          >
            <div className="absolute -inset-2 bg-gradient-to-r from-blue-500 to-cyan-400 rounded-[28px] blur-xl opacity-20 dark:opacity-30" />
            <div className="relative rounded-[24px] bg-slate-950 border border-slate-800 shadow-2xl overflow-hidden font-mono text-left">
              {/* Header */}
              <div className="flex items-center justify-between px-5 py-3 border-b border-slate-900 bg-slate-900/40">
                <div className="flex gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-500" />
                  <div className="w-3 h-3 rounded-full bg-amber-500" />
                  <div className="w-3 h-3 rounded-full bg-emerald-500" />
                </div>
                <div className="text-xs text-slate-400 font-semibold flex items-center gap-1.5 select-none">
                  <TerminalIcon className="w-3.5 h-3.5 text-blue-400" />
                  api.resilai.io
                </div>
                <button
                  onClick={handleCopy}
                  className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                  title="Copy to clipboard"
                >
                  {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>

              {/* Tabs */}
              <div className="flex bg-slate-900/10 border-b border-slate-900 text-xs text-slate-400">
                <button
                  onClick={() => setTerminalTab('telemetry')}
                  className={`px-4 py-2 border-r border-slate-900 hover:text-slate-100 transition-colors ${
                    terminalTab === 'telemetry' ? 'bg-slate-950 text-blue-400 font-semibold border-b border-b-blue-500' : ''
                  }`}
                >
                  Live Telemetry
                </button>
                <button
                  onClick={() => setTerminalTab('request')}
                  className={`px-4 py-2 border-r border-slate-900 hover:text-slate-100 transition-colors ${
                    terminalTab === 'request' ? 'bg-slate-950 text-blue-400 font-semibold border-b border-b-blue-500' : ''
                  }`}
                >
                  cURL Request
                </button>
                <button
                  onClick={() => setTerminalTab('response')}
                  className={`px-4 py-2 hover:text-slate-100 transition-colors ${
                    terminalTab === 'response' ? 'bg-slate-950 text-blue-400 font-semibold border-b border-b-blue-500' : ''
                  }`}
                >
                  JSON Response
                </button>
              </div>

              {/* Console Body */}
              <div ref={logContainerRef} className="p-5 h-[230px] overflow-auto text-xs leading-relaxed text-slate-300 select-text scrollbar-thin">
                <AnimatePresence mode="wait">
                  {terminalTab === 'telemetry' ? (
                    <motion.div
                      key="telemetry"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="space-y-1 font-mono text-[11px]"
                    >
                      {telemetryLogs.map((log, index) => {
                        let color = 'text-slate-300';
                        if (log.includes('[WARN]')) color = 'text-amber-400 font-semibold';
                        if (log.includes('[SUCCESS]') || log.includes('Score=')) color = 'text-emerald-400';
                        if (log.includes('[SYNC]')) color = 'text-blue-400';
                        return (
                          <div key={index} className={color}>
                            <span className="text-slate-500 select-none">&gt;</span> {log}
                          </div>
                        );
                      })}
                    </motion.div>
                  ) : terminalTab === 'request' ? (
                    <motion.pre
                      key="req"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-pre-wrap text-blue-300 font-mono text-[11px]"
                    >
                      <span className="text-slate-500">$</span> {requestText}
                    </motion.pre>
                  ) : (
                    <motion.pre
                      key="res"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-pre text-emerald-400 font-mono text-[11px]"
                    >
                      {responseText}
                    </motion.pre>
                  )}
                </AnimatePresence>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 bg-slate-50 dark:bg-slate-900/60 border-y border-slate-200/60 dark:border-slate-800/80 transition-colors duration-300">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, i) => (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="text-center"
              >
                <p className="text-3xl sm:text-4xl font-extrabold text-blue-600 dark:text-blue-400 tracking-tight">
                  {stat.value}
                </p>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mt-1">
                  {stat.label}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Pillars */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              Readiness, Compliance & Risk — Unified
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
              Built by GRC professionals for modern engineering teams. Deterministic scoring you can verify, with AI summaries where they matter most.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                className="group p-8 bg-slate-50 dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/80 rounded-[24px] hover:border-blue-450 hover:bg-white dark:hover:bg-slate-900/80 hover:shadow-xl hover:shadow-blue-500/5 transition-all duration-300"
              >
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-950/40 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-blue-600 group-hover:scale-105 transition-all duration-300">
                  <feature.icon className="w-6 h-6 text-blue-600 dark:text-blue-400 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50 mb-3">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Report Preview Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-slate-50/50 dark:bg-slate-900/30 border-t border-slate-200/50 dark:border-slate-800/40">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="space-y-6 text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 rounded-full text-xs font-semibold border border-emerald-100 dark:border-emerald-900/50">
                <TrendingUp className="w-3.5 h-3.5" />
                AI-Powered Executive Summaries
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
                Executive-Ready Audits
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                Generate comprehensive PDF reports that executives and auditors trust. Includes compliance thermal maps, score charts, and real-time posture indicators.
              </p>
              <ul className="space-y-3.5">
                {[
                  'Executive summary with compliance rating',
                  'Security domain heatmaps',
                  'Priority remediation ledger checks',
                  'Actionable upgrade recommendations',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-500 flex-shrink-0" />
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Interactive Report View */}
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-[32px] blur-2xl opacity-15 dark:opacity-25" />
              <div className="relative bg-white dark:bg-slate-900 rounded-[24px] shadow-2xl border border-slate-200/80 dark:border-slate-800/80 overflow-hidden text-left">
                {/* Banner header */}
                <div className="bg-gradient-to-r from-blue-600 to-cyan-600 px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-white font-bold text-sm tracking-wide">ResilAI Assessment Report</p>
                      <p className="text-white/80 text-xs">AI Incident Readiness Score (GHI)</p>
                    </div>
                  </div>
                </div>

                <div className="p-6 space-y-6">
                  {/* Score Ring */}
                  <div className="flex items-center gap-6">
                    <div className="w-20 h-20 rounded-full border-[6px] border-emerald-500 flex items-center justify-center shadow-inner">
                      <span className="text-2xl font-bold text-slate-800 dark:text-slate-100">84%</span>
                    </div>
                    <div>
                      <p className="font-bold text-slate-900 dark:text-slate-50">Maturity Level: Managed</p>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Recalculated 2 minutes ago</p>
                    </div>
                  </div>

                  {/* Domain bars */}
                  <div className="space-y-3.5">
                    {[
                      { name: 'Telemetry & Logging', score: 92 },
                      { name: 'Identity & Access Visibility', score: 88 },
                      { name: 'Detection Coverage', score: 81 },
                    ].map((d) => (
                      <div key={d.name}>
                        <div className="flex justify-between text-xs font-semibold mb-1 text-slate-700 dark:text-slate-300">
                          <span>{d.name}</span>
                          <span className="font-bold">{d.score}%</span>
                        </div>
                        <div className="h-2 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-blue-500 rounded-full"
                            style={{ width: `${d.score}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Sample Alert Card */}
                  <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/20 border border-amber-250/50 dark:border-amber-900/50">
                    <div className="flex gap-3">
                      <div className="w-5 h-5 bg-amber-500 rounded-lg text-white flex items-center justify-center text-xs font-bold shrink-0">
                        !
                      </div>
                      <div>
                        <p className="text-xs font-bold text-amber-950 dark:text-amber-300">Identity Provider Idle Timeouts</p>
                        <p className="text-[11px] text-amber-700 dark:text-amber-400 mt-0.5">
                          Idle sessions exceed 15-minute SLA limits inside Okta configurations.
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 border-t border-slate-200/50 dark:border-slate-800/40">
        <div className="max-w-4xl mx-auto text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-50 dark:bg-blue-950/40 text-blue-700 dark:text-blue-300 rounded-full text-xs font-semibold border border-blue-100 dark:border-blue-900/50">
            <Clock className="w-3.5 h-3.5" />
            Full audit ready in under 5 minutes
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
            Assess Your Cybersecurity Posture
          </h2>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Run a sandbox audit using our synthetic templates, or register your organization to link real-time integrations and track compliance drift.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/assessment/quick"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-slate-900 dark:bg-slate-50 text-white dark:text-slate-900 text-base font-semibold rounded-2xl hover:bg-slate-800 dark:hover:bg-slate-100 shadow-lg transition-all active:scale-[0.98]"
            >
              Start Free Assessment
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/org/new"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-base font-semibold rounded-2xl border border-slate-300 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/60 transition-all active:scale-[0.98]"
            >
              Create Organization
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-50 dark:bg-slate-900 border-t border-slate-200 dark:border-slate-800/80 py-12 transition-colors duration-300 text-xs text-slate-500 dark:text-slate-400">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex flex-col items-center md:items-start gap-3">
              <img src="/logo_footer_and github.svg" alt="ResilAI Logo" className="h-20 w-auto dark:brightness-0 dark:invert transition-all duration-300" />
              <span className="font-medium text-slate-500 dark:text-slate-400">Continuous Readiness Intelligence</span>
            </div>

            <div className="flex items-center gap-6">
              <a
                href="https://www.github.com/purvanshbhatt/AIRS"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
              >
                <Github className="w-4.5 h-4.5" />
                <span>GitHub</span>
              </a>
              <a
                href="mailto:purvansh95b@gmail.com"
                className="flex items-center gap-2 hover:text-slate-900 dark:hover:text-slate-100 transition-colors"
              >
                <Mail className="w-4.5 h-4.5" />
                <span>Contact</span>
              </a>
            </div>

            <p className="text-slate-400 dark:text-slate-500">
              &copy; {new Date().getFullYear()} ResilAI. Open source under GNU AGPL-3.0 license.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
