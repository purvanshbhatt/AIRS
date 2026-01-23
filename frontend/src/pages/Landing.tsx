import { Link } from 'react-router-dom';
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
} from 'lucide-react';

const features = [
  {
    icon: Target,
    title: 'Comprehensive Assessment',
    description:
      'Evaluate your security posture across 5 critical domains with 30+ targeted questions designed by incident response experts.',
  },
  {
    icon: BarChart3,
    title: 'Instant Scoring & Insights',
    description:
      'Get immediate visibility into your readiness level with weighted scores, maturity ratings, and prioritized findings.',
  },
  {
    icon: FileText,
    title: 'Executive-Ready Reports',
    description:
      'Generate professional PDF reports with AI-powered narratives, actionable recommendations, and benchmark comparisons.',
  },
];

const stats = [
  { value: '5', label: 'Security Domains' },
  { value: '30+', label: 'Assessment Questions' },
  { value: '15+', label: 'Detection Rules' },
  { value: '<5min', label: 'Time to Complete' },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-2">
              <div className="w-9 h-9 bg-primary-600 rounded-xl flex items-center justify-center">
                <Shield className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">AIRS</span>
            </div>
            <div className="flex items-center gap-4">
              <Link
                to="/dashboard"
                className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
              >
                Dashboard
              </Link>
              <Link
                to="/assessment/new"
                className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 transition-colors"
              >
                Get Started
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-6">
              <Zap className="w-4 h-4" />
              Open Source Security Assessment
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 tracking-tight mb-6">
              Know Your{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary-600 to-primary-400">
                AI Incident Readiness
              </span>{' '}
              Score
            </h1>
            <p className="text-xl text-gray-600 mb-10 max-w-2xl mx-auto leading-relaxed">
              Assess your organization's security posture in minutes. Get actionable insights,
              identify gaps, and generate executive-ready reports powered by AI.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Link
                to="/assessment/new"
                className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 text-white text-lg font-semibold rounded-xl hover:bg-primary-700 transition-all shadow-lg shadow-primary-600/25 hover:shadow-xl hover:shadow-primary-600/30 hover:-translate-y-0.5"
              >
                Run Demo Assessment
                <ChevronRight className="w-5 h-5" />
              </Link>
              <a
                href="https://github.com/purvanshbhatt/AIRS"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-6 py-4 text-gray-700 text-lg font-medium hover:text-gray-900 transition-colors"
              >
                <Github className="w-5 h-5" />
                View on GitHub
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Bar */}
      <section className="py-12 bg-gray-50 border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-3xl sm:text-4xl font-bold text-primary-600">{stat.value}</p>
                <p className="text-sm text-gray-600 mt-1">{stat.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Value Pillars */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
              Everything You Need to Assess Readiness
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Built by security professionals for security professionals. Get from zero to
              actionable insights in under 5 minutes.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {features.map((feature) => (
              <div
                key={feature.title}
                className="group p-8 bg-white rounded-2xl border border-gray-200 hover:border-primary-200 hover:shadow-xl hover:shadow-primary-600/5 transition-all duration-300"
              >
                <div className="w-14 h-14 bg-primary-100 rounded-xl flex items-center justify-center mb-6 group-hover:bg-primary-600 group-hover:scale-110 transition-all duration-300">
                  <feature.icon className="w-7 h-7 text-primary-600 group-hover:text-white transition-colors" />
                </div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{feature.title}</h3>
                <p className="text-gray-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Report Preview Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-gray-50 to-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 bg-success-50 text-success-700 rounded-full text-sm font-medium mb-6">
                <TrendingUp className="w-4 h-4" />
                AI-Powered Insights
              </div>
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
                Professional Reports in Seconds
              </h2>
              <p className="text-lg text-gray-600 mb-8 leading-relaxed">
                Generate comprehensive PDF reports that executives and auditors love. Includes
                domain-by-domain analysis, severity-ranked findings, and AI-generated narratives.
              </p>
              <ul className="space-y-4">
                {[
                  'Executive summary with maturity rating',
                  'Domain heatmap visualization',
                  'Prioritized security findings',
                  'Actionable remediation steps',
                ].map((item) => (
                  <li key={item} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-success-500 flex-shrink-0" />
                    <span className="text-gray-700">{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Report Preview Placeholder */}
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-r from-primary-600/20 to-primary-400/20 rounded-3xl blur-2xl" />
              <div className="relative bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
                {/* Mock Report Header */}
                <div className="bg-gradient-to-r from-primary-600 to-primary-500 px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                      <Shield className="w-6 h-6 text-white" />
                    </div>
                    <div>
                      <p className="text-white font-semibold">AIRS Assessment Report</p>
                      <p className="text-white/70 text-sm">AI Incident Readiness Score</p>
                    </div>
                  </div>
                </div>

                {/* Mock Report Content */}
                <div className="p-6 space-y-6">
                  {/* Score Circle */}
                  <div className="flex items-center gap-6">
                    <div className="w-24 h-24 rounded-full border-8 border-success-500 flex items-center justify-center">
                      <span className="text-3xl font-bold text-success-600">78</span>
                    </div>
                    <div>
                      <p className="text-lg font-semibold text-gray-900">Overall Score</p>
                      <p className="text-sm text-gray-500">Maturity Level: Managed</p>
                    </div>
                  </div>

                  {/* Mock Domain Bars */}
                  <div className="space-y-3">
                    {[
                      { name: 'Telemetry & Logging', score: 85 },
                      { name: 'Detection Coverage', score: 72 },
                      { name: 'Identity Visibility', score: 68 },
                    ].map((domain) => (
                      <div key={domain.name}>
                        <div className="flex justify-between text-sm mb-1">
                          <span className="text-gray-700">{domain.name}</span>
                          <span className="font-medium text-gray-900">{domain.score}%</span>
                        </div>
                        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-primary-500 rounded-full"
                            style={{ width: `${domain.score}%` }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Mock Finding */}
                  <div className="p-4 bg-warning-50 border border-warning-200 rounded-lg">
                    <div className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-warning-500 rounded text-white flex items-center justify-center text-xs font-bold">
                        !
                      </div>
                      <div>
                        <p className="font-medium text-warning-900">MFA Not Enforced</p>
                        <p className="text-sm text-warning-700">
                          Multi-factor authentication should be required for all users...
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Decorative Elements */}
                <div className="absolute -bottom-2 -right-2 w-32 h-32 bg-primary-100 rounded-full blur-3xl opacity-50" />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm font-medium mb-6">
            <Clock className="w-4 h-4" />
            Takes less than 5 minutes
          </div>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-6">
            Ready to Assess Your Security Posture?
          </h2>
          <p className="text-lg text-gray-600 mb-10">
            Start with a demo assessment using sample data, or create your organization to track
            progress over time.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to="/assessment/new"
              className="inline-flex items-center gap-2 px-8 py-4 bg-primary-600 text-white text-lg font-semibold rounded-xl hover:bg-primary-700 transition-all shadow-lg shadow-primary-600/25"
            >
              Start Free Assessment
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              to="/org/new"
              className="inline-flex items-center gap-2 px-8 py-4 bg-white text-gray-700 text-lg font-medium rounded-xl border border-gray-300 hover:border-gray-400 hover:bg-gray-50 transition-colors"
            >
              Create Organization
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 sm:px-6 lg:px-8 bg-gray-900">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row items-center justify-between gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white/10 rounded-lg flex items-center justify-center">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <span className="text-white font-semibold">AIRS</span>
              <span className="text-gray-500">•</span>
              <span className="text-gray-400 text-sm">AI Incident Readiness Score</span>
            </div>

            <div className="flex items-center gap-6">
              <a
                href="https://github.com/purvanshbhatt/AIRS"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
              >
                <Github className="w-5 h-5" />
                <span className="text-sm">GitHub</span>
              </a>
              <a
                href="mailto:contact@example.com"
                className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
              >
                <Mail className="w-5 h-5" />
                <span className="text-sm">Contact</span>
              </a>
            </div>

            <p className="text-gray-500 text-sm">
              © {new Date().getFullYear()} AIRS. Open source under MIT license.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
