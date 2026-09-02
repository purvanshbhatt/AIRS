import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Check,
  Shield,
  ArrowRight,
  Sparkles,
  HelpCircle,
  Zap,
  Building2,
  Users,
  ShieldCheck,
  Layers,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';

export default function Pricing() {
  useEffect(() => {
    document.title = 'ResilAI Pricing — Early Access & Enterprise Tiers';
    window.scrollTo(0, 0);
  }, []);

  const tiers = [
    {
      id: 'design-partner',
      name: 'Design Partner Program',
      tagline: 'Early Access for Healthcare & Enterprise Pioneers',
      price: 'Collaborative EAP',
      period: 'Custom Term',
      badge: 'Popular for Early Adopters',
      description: 'For healthcare practices, clinics, and security leaders actively collaborating with our engineering team to establish verifiable readiness standards.',
      features: [
        'White-glove guided onboarding & setup',
        'Direct live connector integration (Splunk, Wazuh, Microsoft 365, Azure AD)',
        'Continuous 24/7 deterministic scoring & overnight verification',
        'Executive Morning Briefs & leadership board report generation',
        'Direct founder Slack / communication channel access',
        'Bi-weekly posture reviews and custom framework crosswalks',
      ],
      cta: 'Become a Design Partner',
      ctaTo: '/contact?tier=design-partner',
      featured: true,
    },
    {
      id: 'growth',
      name: 'Growth',
      tagline: 'Continuous Incident Readiness for Growing Practices',
      price: 'Contact Us',
      period: 'Billed Annually',
      description: 'For growing clinics and organizations requiring continuous posture visibility across multiple identity and operational systems.',
      features: [
        'All 7 technology domain mini-products (Identity, Devices, Backups, Email, Network, Cloud, AI)',
        'Daily Morning Readiness Briefings (L1 Executive view)',
        'Actionable Needs Attention triage & 1-click remediation workflows',
        'Cryptographic SHA-256 evidence ledger for auditor inspection',
        'Executive PDF report downloads & audit calendar',
        'Standard business-hours support & SLA',
      ],
      cta: 'Contact Us for Pricing',
      ctaTo: '/contact?tier=growth',
      featured: false,
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      tagline: 'Multi-Facility Health Systems & Regulated Enterprises',
      price: 'Custom Deployment',
      period: 'Tailored Contract',
      description: 'For hospital networks, multi-facility clinics, and compliance-regulated organizations with complex tenancy and sovereignty needs.',
      features: [
        'Multi-tenant organization hierarchy & role-based access control (RBAC)',
        'Dedicated Cloud Run instance or private VPC deployment options',
        'Enterprise SSO / SAML integration & SCIM provisioning',
        'Custom regulatory framework mapping (NIST CSF 2.0, HIPAA, SOC 2, ISO 27001)',
        'Full REST API & webhook ingestion access',
        'Dedicated Technical Account Manager & 99.9% uptime SLA',
      ],
      cta: 'Talk to Enterprise Team',
      ctaTo: '/contact?tier=enterprise',
      featured: false,
    },
  ];

  const faqs = [
    {
      question: 'What telemetry connectors are supported?',
      answer: 'ResilAI supports Splunk MCP, Wazuh HEC/API, Microsoft Graph, Azure AD / Entra ID, AWS CloudTrail, Veeam backup logs, CrowdStrike, and custom JSON webhook ingestion.',
    },
    {
      question: 'Does ResilAI send confidential log data to external LLMs?',
      answer: 'No. Layer 1 scoring is strictly deterministic and evaluated on-server via mathematical rules. Only normalized finding summaries (with zero raw confidential telemetry) flow into Gemini for plain-English executive translation.',
    },
    {
      question: 'What are the requirements for the Design Partner Program?',
      answer: 'Design partners must have active security telemetry feeds (or be willing to connect test streams) and commit to bi-weekly feedback sessions as we refine specialized healthcare workflows.',
    },
    {
      question: 'Can we test ResilAI without connecting our live systems?',
      answer: 'Yes. You can explore our pre-populated Acme Health Systems sandbox immediately with zero setup required to inspect executive morning briefs and progressive disclosure workflows.',
    },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col selection:bg-primary-500/20 transition-colors duration-300">
      <PublicNavbar />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 lg:py-28 overflow-hidden border-b border-slate-200/80 dark:border-slate-800/80 bg-gradient-to-b from-slate-50/70 via-white to-white dark:from-slate-900/50 dark:via-slate-950 dark:to-slate-950">
          <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-semibold uppercase tracking-wider bg-primary-50 dark:bg-primary-950/60 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800/60 shadow-xs">
              <Zap className="w-3.5 h-3.5 text-primary-600 dark:text-primary-400" />
              <span>Transparent Engagement</span>
            </div>

            <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 leading-[1.15]">
              Verifiable Incident Readiness for{' '}
              <span className="bg-gradient-to-r from-primary-600 to-emerald-500 bg-clip-text text-transparent">
                Every Organization
              </span>
            </h1>

            <p className="text-base sm:text-lg text-slate-600 dark:text-slate-300 max-w-3xl mx-auto leading-relaxed">
              Early access programs for design partners and continuous readiness monitoring for growing clinics and health systems.
            </p>
          </div>
        </section>

        {/* Pricing Cards Grid */}
        <section className="py-16 lg:py-24">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-stretch">
              {tiers.map((tier) => (
                <div
                  key={tier.id}
                  className={`rounded-3xl p-8 flex flex-col justify-between transition-all duration-300 relative ${
                    tier.featured
                      ? 'bg-white dark:bg-slate-900 border-2 border-primary-500 dark:border-primary-500 shadow-xl shadow-primary-500/10'
                      : 'bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800'
                  }`}
                >
                  {tier.badge && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider bg-gradient-to-r from-primary-600 to-emerald-500 text-white shadow-sm">
                      {tier.badge}
                    </div>
                  )}

                  <div className="space-y-6">
                    <div>
                      <h3 className="text-xl font-bold text-slate-900 dark:text-slate-50">{tier.name}</h3>
                      <p className="text-xs font-semibold text-primary-600 dark:text-primary-400 mt-1">{tier.tagline}</p>
                    </div>

                    <div className="pb-4 border-b border-slate-200 dark:border-slate-800">
                      <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-extrabold text-slate-900 dark:text-slate-50">{tier.price}</span>
                      </div>
                      <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">{tier.period}</p>
                    </div>

                    <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                      {tier.description}
                    </p>

                    <div className="space-y-3 pt-2">
                      <p className="text-xs font-mono font-bold uppercase tracking-wider text-slate-900 dark:text-slate-200">
                        Included Capabilities
                      </p>
                      <ul className="space-y-2.5 text-sm text-slate-600 dark:text-slate-300">
                        {tier.features.map((feat) => (
                          <li key={feat} className="flex items-start gap-2.5">
                            <Check className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                            <span>{feat}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>

                  <div className="pt-8">
                    <Link
                      to={tier.ctaTo}
                      className={`w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-bold text-sm transition-all ${
                        tier.featured
                          ? 'bg-gradient-to-r from-primary-600 to-emerald-500 text-white hover:shadow-lg hover:shadow-primary-500/20 active:scale-[0.98]'
                          : 'bg-slate-900 dark:bg-slate-100 text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-white active:scale-[0.98]'
                      }`}
                    >
                      <span>{tier.cta}</span>
                      <ArrowRight className="w-4 h-4" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* FAQs Section */}
        <section className="py-16 lg:py-24 bg-slate-50/60 dark:bg-slate-900/30 border-t border-slate-200/80 dark:border-slate-800/80">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
            <div className="text-center max-w-2xl mx-auto space-y-3">
              <div className="inline-flex items-center gap-2 text-xs font-mono font-bold uppercase tracking-wider text-primary-600 dark:text-primary-400">
                <HelpCircle className="w-4 h-4" />
                <span>Common Questions</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                Frequently Asked Questions
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {faqs.map((faq) => (
                <div
                  key={faq.question}
                  className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2.5 shadow-xs"
                >
                  <h3 className="font-bold text-base text-slate-900 dark:text-slate-100">{faq.question}</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 leading-relaxed">{faq.answer}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Bottom CTA Banner */}
        <section className="py-20 bg-slate-900 text-white relative overflow-hidden">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight">
              Have Specific Architecture or Compliance Requirements?
            </h2>
            <p className="text-slate-300 text-base max-w-2xl mx-auto leading-relaxed">
              We work closely with healthcare managing partners, security directors, and compliance officers to ensure smooth onboarding.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
              <Link
                to="/contact"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-xl bg-gradient-to-r from-primary-600 to-emerald-500 text-white font-bold text-sm shadow-lg hover:shadow-primary-500/25 transition-all"
              >
                <span>Schedule a Conversation</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
