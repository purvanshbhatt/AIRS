import { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
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
  Sparkles,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';

const personas = [
  {
    icon: Shield,
    title: 'Executive (L1) — "Are we ready?"',
    description: 'Get a deterministic, board-ready answer to your most critical question without navigating complex technical dashboards or interpreting raw logs.',
  },
  {
    icon: Target,
    title: 'Manager (L2) — "What changed and what needs action?"',
    description: 'Understand exactly how your readiness posture drifted, why it matters to the business, and the clear remediation steps required to fix it.',
  },
  {
    icon: TerminalIcon,
    title: 'IT & Security (L3) — "What evidence proves it?"',
    description: 'Trace every finding down to the raw evidence block, timestamp, and connector source. No more guesswork — just cryptographic proof of your operational state.',
  },
];

const loopSteps = [
  { title: 'CONNECT', description: 'Connect the security and operational systems your organization already uses.', icon: Layers },
  { title: 'VERIFY', description: 'ResilAI deterministically verifies operational evidence against readiness requirements.', icon: ShieldCheck },
  { title: 'UNDERSTAND', description: 'Translate verified technical gaps into clear business impact.', icon: BarChart3 },
  { title: 'ACT', description: 'Remediate the problem and verify that the remediation actually worked.', icon: CheckCircle },
];


export default function Landing() {
  const navigate = useNavigate();
  const { signInAsDemo, clearError } = useAuth();

  const handleEnterSandbox = async () => {
    clearError();
    try {
      await signInAsDemo();
      navigate("/morning-brief", { replace: true });
    } catch {
      navigate("/morning-brief", { replace: true });
    }
  };

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

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 selection:bg-primary-500/20 transition-colors duration-300 flex flex-col">
      {/* Unified Public Navigation */}
      <PublicNavbar transparent />

      {/* Hero Section */}
      <section className="relative pt-16 sm:pt-20 pb-24 overflow-hidden px-4 sm:px-6 lg:px-8">
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-primary-500/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute top-1/3 left-1/4 w-[300px] h-[300px] bg-emerald-500/10 rounded-full blur-[80px] pointer-events-none" />

        <div className="max-w-7xl mx-auto grid lg:grid-cols-12 gap-12 items-center relative z-10">
          <div className="lg:col-span-7 space-y-6 text-left">
            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 dark:bg-primary-950/40 text-primary-700 dark:text-primary-300 rounded-full text-xs font-semibold tracking-wide border border-primary-100 dark:border-primary-900/50"
            >
              <Zap className="w-3.5 h-3.5" />
              Deterministic Verification for Healthcare
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-[1.1] text-slate-900 dark:text-slate-50"
            >
              Know if your healthcare organization is ready <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-emerald-500 dark:from-primary-400 dark:to-emerald-300">
                before an incident happens.
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="text-lg sm:text-xl text-slate-600 dark:text-slate-400 max-w-2xl leading-relaxed"
            >
              ResilAI continuously tests whether your organization's most critical security and operational controls actually work—and maintains the mathematical evidence proving it.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.3 }}
              className="flex flex-wrap items-center gap-4 pt-4"
            >
              <Link
                to="/login"
                className="inline-flex items-center gap-2 px-7 py-3.5 bg-gradient-to-br from-primary-600 to-emerald-500 text-white font-semibold rounded-2xl hover:shadow-lg hover:shadow-primary-500/25 transition-all duration-300 active:scale-[0.98]"
              >
                Get Started
                <ChevronRight className="w-5 h-5" />
              </Link>
              <a
                href="#how-it-works"
                className="inline-flex items-center gap-2 px-6 py-3.5 text-slate-700 dark:text-slate-300 font-semibold rounded-2xl border border-slate-300 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/60 transition-all active:scale-[0.98]"
              >
                See How It Works
              </a>
              <button
                onClick={handleEnterSandbox}
                className="inline-flex items-center gap-2 px-5 py-3.5 text-slate-600 dark:text-slate-400 font-medium rounded-2xl hover:text-slate-900 dark:hover:text-slate-100 transition-all text-sm"
              >
                <Sparkles className="w-4 h-4 text-amber-500" />
                Explore Demo
              </button>
            </motion.div>
          </div>

          {/* Live Telemetry & Deterministic Verification Stream */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="lg:col-span-5 relative"
          >
            <div className="absolute -inset-2 bg-gradient-to-r from-primary-500 to-emerald-400 rounded-[28px] blur-xl opacity-20 dark:opacity-30" />
            
            <div className="relative rounded-[24px] bg-slate-950 border border-slate-800 shadow-2xl overflow-hidden text-left font-mono">
              {/* Terminal Window Top Bar */}
              <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800 bg-slate-900/80 backdrop-blur-sm">
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1.5 mr-2">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                  </div>
                  <div className="flex items-center gap-1 p-0.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs">
                    <button
                      onClick={() => setTerminalTab('telemetry')}
                      className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                        terminalTab === 'telemetry'
                          ? 'bg-slate-800 text-emerald-400 font-semibold shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      Live Stream
                    </button>
                    <button
                      onClick={() => setTerminalTab('request')}
                      className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                        terminalTab === 'request'
                          ? 'bg-slate-800 text-primary-400 font-semibold shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      cURL
                    </button>
                    <button
                      onClick={() => setTerminalTab('response')}
                      className={`px-3 py-1.5 rounded-lg font-medium transition-all ${
                        terminalTab === 'response'
                          ? 'bg-slate-800 text-emerald-400 font-semibold shadow-sm'
                          : 'text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      JSON
                    </button>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-emerald-400 font-bold flex items-center gap-1.5 bg-emerald-950/60 border border-emerald-800/60 px-2 py-0.5 rounded-full">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    ENGINE ACTIVE
                  </span>
                  <button
                    onClick={handleCopy}
                    className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                    title="Copy to clipboard"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Terminal Body */}
              <div ref={logContainerRef} className="p-4 h-[280px] overflow-auto text-xs leading-relaxed text-slate-300 select-text scrollbar-thin">
                <AnimatePresence mode="wait">
                  {terminalTab === 'telemetry' ? (
                    <motion.div
                      key="telemetry"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="space-y-1.5 text-[11px]"
                    >
                      {telemetryLogs.map((log, index) => {
                        let color = 'text-slate-300';
                        if (log.includes('[WARN]')) color = 'text-amber-400 font-semibold';
                        if (log.includes('[SUCCESS]') || log.includes('Score=')) color = 'text-emerald-400';
                        if (log.includes('[SYNC]')) color = 'text-primary-400';
                        return (
                          <div key={index} className={color}>
                            <span className="text-slate-600 select-none">&gt;</span> {log}
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
                      className="whitespace-pre-wrap text-primary-300 text-[11px]"
                    >
                      <span className="text-slate-600 select-none">$</span> {requestText}
                    </motion.pre>
                  ) : (
                    <motion.pre
                      key="res"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="whitespace-pre text-emerald-400 text-[11px]"
                    >
                      {responseText}
                    </motion.pre>
                  )}
                </AnimatePresence>
              </div>

              {/* Terminal Footer */}
              <div className="px-4 py-2 bg-slate-900/60 border-t border-slate-800/80 flex items-center justify-between text-[11px] text-slate-400">
                <span className="flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Continuous Control Verification</span>
                </span>
                <span className="text-emerald-400 font-semibold">100% Deterministic</span>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Core Loop Section */}
      <section id="how-it-works" className="py-16 bg-slate-50 dark:bg-slate-900/60 border-y border-slate-200/60 dark:border-slate-800/80 transition-colors duration-300 scroll-mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-[12.5%] right-[12.5%] h-0.5 bg-gradient-to-r from-slate-200 via-primary-300 to-slate-200 dark:from-slate-800 dark:via-primary-800 dark:to-slate-800" />
            {loopSteps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 15 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="relative text-center z-10"
              >
                <div className="w-16 h-16 mx-auto bg-white dark:bg-slate-950 border-2 border-primary-100 dark:border-primary-900/50 rounded-2xl flex items-center justify-center mb-6 shadow-sm">
                  <step.icon className="w-7 h-7 text-primary-600 dark:text-primary-400" />
                </div>
                <h3 className="text-xl font-extrabold text-slate-900 dark:text-slate-50 tracking-tight">
                  {step.title}
                </h3>
                <p className="text-sm font-medium text-slate-600 dark:text-slate-400 mt-2 leading-relaxed max-w-[250px] mx-auto">
                  {step.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Pillars - Personas */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-3xl mx-auto mb-16 space-y-4">
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
              One truth, translated for every leader.
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
              ResilAI provides a unified, continuous readiness posture that speaks the right language to the right stakeholder.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {personas.map((persona, i) => (
              <motion.div
                key={persona.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: i * 0.05 }}
                className="group p-8 bg-slate-50 dark:bg-slate-900 border border-slate-200/60 dark:border-slate-800/80 rounded-[24px] hover:border-primary-450 hover:bg-white dark:hover:bg-slate-900/80 hover:shadow-xl hover:shadow-primary-500/5 transition-all duration-300"
              >
                <div className="w-12 h-12 bg-primary-100 dark:bg-primary-950/40 rounded-2xl flex items-center justify-center mb-6 group-hover:bg-primary-600 group-hover:scale-105 transition-all duration-300">
                  <persona.icon className="w-6 h-6 text-primary-600 dark:text-primary-400 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-lg font-bold text-slate-900 dark:text-slate-50 mb-3">
                  {persona.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  {persona.description}
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
              <div className="absolute -inset-4 bg-gradient-to-r from-primary-500 to-emerald-500 rounded-[32px] blur-2xl opacity-15 dark:opacity-25" />
              <div className="relative bg-white dark:bg-slate-900 rounded-[24px] shadow-2xl border border-slate-200/80 dark:border-slate-800/80 overflow-hidden text-left">
                {/* Banner header */}
                <div className="bg-gradient-to-r from-primary-600 to-emerald-600 px-6 py-5">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-white font-bold text-sm tracking-wide">ResilAI Readiness Verification</p>
                      <p className="text-white/80 text-xs">Readiness Intelligence OS</p>
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
                            className="h-full bg-primary-500 rounded-full"
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
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 dark:bg-primary-950/40 text-primary-700 dark:text-primary-300 rounded-full text-xs font-semibold border border-primary-100 dark:border-primary-900/50">
            <Clock className="w-3.5 h-3.5" />
            Deterministic verification in minutes
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
            Verify Your Operational Readiness Posture
          </h2>
          <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Verify whether the controls protecting your critical operations actually work. Establish an isolated workspace or explore our pre-populated clinic demo.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
            <Link
              to="/login"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-gradient-to-br from-primary-600 to-emerald-500 text-white text-base font-semibold rounded-2xl hover:shadow-lg hover:shadow-primary-500/25 transition-all active:scale-[0.98]"
            >
              Get Started
              <ArrowRight className="w-5 h-5" />
            </Link>
            <button
              onClick={handleEnterSandbox}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-4 bg-white dark:bg-slate-900 text-slate-800 dark:text-slate-200 text-base font-semibold rounded-2xl border border-slate-300 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-900/60 transition-all active:scale-[0.98]"
            >
              <Sparkles className="w-4 h-4 text-amber-500" />
              Explore Demo Sandbox
            </button>
          </div>
        </div>
      </section>

      {/* Unified Public Footer */}
      <Footer />
    </div>
  );
}
