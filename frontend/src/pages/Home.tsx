import { Link } from 'react-router-dom';
import { Card, Badge } from '../components/ui';
import {
  Shield,
  Search,
  Users,
  FileCheck,
  Database,
  Plus,
  ClipboardList,
  ArrowRight,
  Zap,
  Target,
  Layers,
  Building2,
  CheckCircle2,
  Clock,
  Lock,
  Sparkles,
} from 'lucide-react';

const domains = [
  {
    name: 'Telemetry & Logging',
    description: 'Log pipeline coverage, retention, and alerting fidelity',
    weight: 25,
    icon: Database,
    color: 'bg-blue-500',
    accent: 'border-blue-200 dark:border-blue-800 hover:border-blue-400 dark:hover:border-blue-600',
    iconBg: 'bg-blue-100 dark:bg-blue-900/30 group-hover:bg-blue-500',
    iconText: 'text-blue-600 group-hover:text-white',
    barColor: 'bg-blue-500',
  },
  {
    name: 'Detection Coverage',
    description: 'Rule quality, MITRE ATT&CK alignment, and false-positive tuning',
    weight: 20,
    icon: Search,
    color: 'bg-purple-500',
    accent: 'border-purple-200 dark:border-purple-800 hover:border-purple-400 dark:hover:border-purple-600',
    iconBg: 'bg-purple-100 dark:bg-purple-900/30 group-hover:bg-purple-500',
    iconText: 'text-purple-600 group-hover:text-white',
    barColor: 'bg-purple-500',
  },
  {
    name: 'Identity Visibility',
    description: 'IAM hygiene, MFA enforcement, and privileged access monitoring',
    weight: 20,
    icon: Users,
    color: 'bg-green-500',
    accent: 'border-green-200 dark:border-green-800 hover:border-green-400 dark:hover:border-green-600',
    iconBg: 'bg-green-100 dark:bg-green-900/30 group-hover:bg-green-500',
    iconText: 'text-green-600 group-hover:text-white',
    barColor: 'bg-green-500',
  },
  {
    name: 'IR Process',
    description: 'Playbook maturity, escalation paths, and tabletop drill results',
    weight: 15,
    icon: FileCheck,
    color: 'bg-orange-500',
    accent: 'border-orange-200 dark:border-orange-800 hover:border-orange-400 dark:hover:border-orange-600',
    iconBg: 'bg-orange-100 dark:bg-orange-900/30 group-hover:bg-orange-500',
    iconText: 'text-orange-600 group-hover:text-white',
    barColor: 'bg-orange-500',
  },
  {
    name: 'Resilience',
    description: 'Backup strategy, recovery testing, and business-continuity readiness',
    weight: 20,
    icon: Shield,
    color: 'bg-red-500',
    accent: 'border-red-200 dark:border-red-800 hover:border-red-400 dark:hover:border-red-600',
    iconBg: 'bg-red-100 dark:bg-red-900/30 group-hover:bg-red-500',
    iconText: 'text-red-600 group-hover:text-white',
    barColor: 'bg-red-500',
  },
];

const stats = [
  {
    label: 'Assessment Questions',
    value: '30',
    description: 'Across all five domains',
    icon: ClipboardList,
    accent: 'text-primary-600',
  },
  {
    label: 'Maturity Levels',
    value: '5',
    description: 'Initial to Optimized',
    icon: Layers,
    accent: 'text-success-600',
  },
  {
    label: 'Detection Rules',
    value: '15+',
    description: 'Automated findings engine',
    icon: Target,
    accent: 'text-warning-600',
  },
];

const quickActions = [
  {
    title: 'Create Organization',
    description: 'Set up your company profile to track assessments over time',
    to: '/org/new',
    icon: Building2,
    color: 'bg-primary-100 dark:bg-primary-900/30 text-primary-600',
  },
  {
    title: 'Run Assessment',
    description: 'Answer 30 questions and get an instant readiness score',
    to: '/assessment/new',
    icon: ClipboardList,
    color: 'bg-success-50 dark:bg-success-900/30 text-success-600',
  },
  {
    title: 'View Dashboard',
    description: 'See aggregated scores, trends, and integration status',
    to: '/dashboard',
    icon: Target,
    color: 'bg-warning-50 dark:bg-warning-900/30 text-warning-600',
  },
];

const roadmapPhases = [
  {
    phase: 1,
    title: 'Core Governance Engine',
    status: 'complete' as const,
    icon: CheckCircle2,
    color: 'text-green-600 bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800',
    iconColor: 'text-green-600',
    features: [
      'Deterministic GHI (Governance Health Index) scoring',
      'NIST CSF 2.0 framework mapping',
      'Multi-tenant Firestore persistence',
      'Auditor View with evidence collection',
      'Executive-ready PDF reports',
    ],
  },
  {
    phase: 2,
    title: 'Continuous Compliance',
    status: 'in-progress' as const,
    icon: Clock,
    color: 'text-amber-600 bg-amber-50 border-amber-200 dark:bg-amber-900/20 dark:border-amber-800',
    iconColor: 'text-amber-600',
    features: [
      'Drift detection with baseline comparison',
      'Audit forecasting and risk prediction',
      'Splunk OCSF integration export',
      'Automated finding remediation tracking',
      'Compliance calendar with smart reminders',
    ],
  },
  {
    phase: 3,
    title: 'Zero-Knowledge Enterprise Mode',
    status: 'planned' as const,
    icon: Lock,
    color: 'text-purple-600 bg-purple-50 border-purple-200 dark:bg-purple-900/20 dark:border-purple-800',
    iconColor: 'text-purple-600',
    features: [
      'Client-side AES-256 encryption (PBKDF2)',
      'Bring-your-own-storage architecture',
      'Compliance prediction engine',
      'Zero server-side data access',
      'Enterprise key management (HSM)',
    ],
  },
];

export default function Home() {
  return (
    <div className="space-y-8">
      {/* Hero Welcome */}
      <div className="relative overflow-hidden rounded-2xl bg-linear-to-br from-primary-600 via-primary-700 to-primary-800 p-8 md:p-10">
        <div className="absolute -top-12 -right-12 w-64 h-64 bg-white/5 rounded-full blur-2xl" />
        <div className="absolute -bottom-16 -left-16 w-48 h-48 bg-white/5 rounded-full blur-3xl" />
        <div className="relative flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="flex-1">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-white/10 backdrop-blur-sm text-white/90 rounded-full text-sm font-medium mb-4">
              <Zap className="w-3.5 h-3.5" />
              Security Assessment Platform
            </div>
            <h1 className="text-3xl md:text-4xl font-bold text-white mb-3 tracking-tight">
              Welcome to ResilAI
            </h1>
            <p className="text-primary-100 max-w-xl leading-relaxed">
              Assess your organization's incident readiness across five critical security domains.
              Get actionable insights and executive-ready reports in minutes.
            </p>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link
              to="/org/new"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-white/10 backdrop-blur-sm text-white text-sm font-medium rounded-lg border border-white/20 hover:bg-white/20 transition-colors"
            >
              <Plus className="w-4 h-4" />
              New Organization
            </Link>
            <Link
              to="/assessment/new"
              className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-white text-primary-700 text-sm font-semibold rounded-lg hover:bg-primary-50 transition-colors shadow-lg shadow-primary-900/20"
            >
              <ClipboardList className="w-4 h-4" />
              Start Assessment
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>

      {/* Quick Stats */}
      <section>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {stats.map((stat) => (
            <Card key={stat.label} padding="md" className="group hover:shadow-medium transition-all duration-200">
              <div className="flex items-start gap-4">
                <div className="w-11 h-11 bg-gray-100 dark:bg-slate-800 rounded-xl flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
                  <stat.icon className={`w-5 h-5 ${stat.accent}`} />
                </div>
                <div className="min-w-0">
                  <p className="text-sm font-medium text-gray-500 dark:text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-gray-900 dark:text-slate-100 mt-0.5">{stat.value}</p>
                  <p className="text-xs text-gray-500 dark:text-slate-400 mt-1">{stat.description}</p>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Assessment Domains */}
      <section>
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Assessment Domains</h2>
            <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">Five weighted security pillars that compose your readiness score</p>
          </div>
          <Badge variant="outline" size="sm">5 domains</Badge>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {domains.map((domain) => (
            <Card
              key={domain.name}
              padding="md"
              variant="bordered"
              className={`group cursor-default ${domain.accent} hover:shadow-lg transition-all duration-300`}
            >
              <div
                className={`w-12 h-12 ${domain.iconBg} rounded-xl flex items-center justify-center mb-4 transition-all duration-300 group-hover:scale-110`}
              >
                <domain.icon className={`w-6 h-6 ${domain.iconText} transition-colors duration-300`} />
              </div>
              <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100 leading-tight">{domain.name}</h3>
              <p className="text-xs text-gray-500 dark:text-slate-400 mt-1.5 leading-relaxed line-clamp-2">{domain.description}</p>
              <div className="mt-4 pt-3 border-t border-gray-100 dark:border-gray-800">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-medium text-gray-500 dark:text-slate-400">Weight</span>
                  <span className="text-sm font-bold text-gray-900 dark:text-slate-100">{domain.weight}%</span>
                </div>
                <div className="h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
                  <div
                    className={`h-full ${domain.barColor} rounded-full transition-all duration-500`}
                    style={{ width: `${domain.weight * 4}%` }}
                  />
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Getting Started */}
      <section>
        <div className="mb-5">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Getting Started</h2>
          <p className="text-sm text-gray-500 dark:text-slate-400 mt-0.5">Three steps to your first readiness score</p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {quickActions.map((action, idx) => (
            <Link key={action.title} to={action.to} className="group">
              <Card
                padding="md"
                variant="bordered"
                className="h-full hover:border-primary-300 dark:hover:border-primary-700 hover:shadow-lg hover:shadow-primary-600/5 transition-all duration-300"
              >
                <div className="flex items-start gap-4">
                  <div className="relative shrink-0">
                    <span className="absolute -top-1 -left-1 w-5 h-5 bg-primary-600 rounded-full flex items-center justify-center text-[10px] font-bold text-white">
                      {idx + 1}
                    </span>
                    <div className={`w-11 h-11 ${action.color} rounded-xl flex items-center justify-center`}>
                      <action.icon className="w-5 h-5" />
                    </div>
                  </div>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-slate-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                      {action.title}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-1 leading-relaxed">{action.description}</p>
                  </div>
                  <ArrowRight className="w-4 h-4 text-gray-300 dark:text-slate-600 group-hover:text-primary-500 group-hover:translate-x-0.5 transition-all shrink-0 mt-0.5" />
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Strategic Product Roadmap */}
      <section>
        <div className="flex items-center justify-between mb-5">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <Sparkles className="w-5 h-5 text-purple-500" />
              <h2 className="text-lg font-semibold text-gray-900 dark:text-slate-100">Strategic Product Roadmap</h2>
            </div>
            <p className="text-sm text-gray-500 dark:text-slate-400">
              Building enterprise-grade governance intelligence — from scoring to zero-knowledge compliance
            </p>
          </div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {roadmapPhases.map((phase) => (
            <Card
              key={phase.phase}
              padding="md"
              variant="bordered"
              className={`relative overflow-hidden border ${phase.color} transition-all duration-300 hover:shadow-lg`}
            >
              {/* Phase indicator */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-gray-400 dark:text-slate-500 uppercase tracking-wide">
                    Phase {phase.phase}
                  </span>
                  {phase.status === 'complete' && (
                    <Badge variant="success" size="sm">Complete</Badge>
                  )}
                  {phase.status === 'in-progress' && (
                    <Badge variant="warning" size="sm">In Progress</Badge>
                  )}
                  {phase.status === 'planned' && (
                    <Badge variant="outline" size="sm">Planned</Badge>
                  )}
                </div>
                <phase.icon className={`w-5 h-5 ${phase.iconColor}`} />
              </div>

              {/* Title */}
              <h3 className="text-base font-semibold text-gray-900 dark:text-slate-100 mb-3">
                {phase.title}
              </h3>

              {/* Features list */}
              <ul className="space-y-2">
                {phase.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start gap-2 text-xs text-gray-600 dark:text-slate-400">
                    <CheckCircle2 
                      className={`w-3.5 h-3.5 shrink-0 mt-0.5 ${
                        phase.status === 'complete' 
                          ? 'text-green-500' 
                          : phase.status === 'in-progress' 
                            ? 'text-amber-500' 
                            : 'text-gray-300 dark:text-slate-600'
                      }`} 
                    />
                    <span className={phase.status === 'planned' ? 'text-gray-400 dark:text-slate-500' : ''}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>

              {/* Progress bar for in-progress */}
              {phase.status === 'in-progress' && (
                <div className="mt-4 pt-3 border-t border-amber-200 dark:border-amber-800">
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-amber-600 dark:text-amber-400 font-medium">Development Progress</span>
                    <span className="text-amber-600 dark:text-amber-400 font-bold">65%</span>
                  </div>
                  <div className="h-1.5 bg-amber-100 dark:bg-amber-900/30 rounded-full overflow-hidden">
                    <div className="h-full bg-amber-500 rounded-full" style={{ width: '65%' }} />
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

