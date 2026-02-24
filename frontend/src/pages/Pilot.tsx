import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Rocket,
  Send,
  CheckCircle,
  Shield,
  BarChart3,
  Map,
  Users,
  Zap,
  MessageSquare,
  Star,
  Building2,
  Clock,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, Input } from '../components/ui';
import { submitEnterprisePilotLead, ApiRequestError } from '../api';
import { Footer } from '../components/layout/Footer';
import ThemeToggle from '../components/ui/ThemeToggle';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface EnterpriseFormState {
  contact_name: string;
  company_name: string;
  email: string;
  industry: string;
  company_size: string;
  team_size: string;
  current_security_tools: string;
  ai_usage_description: string;
  current_siem_provider: string;
}

const defaultState: EnterpriseFormState = {
  contact_name: '',
  company_name: '',
  email: '',
  industry: '',
  company_size: '',
  team_size: '',
  current_security_tools: '',
  ai_usage_description: '',
  current_siem_provider: '',
};

// ---------------------------------------------------------------------------
// Benefits data
// ---------------------------------------------------------------------------

const BENEFITS = [
  {
    icon: Shield,
    title: '90-Day Structured Engagement',
    description:
      'A dedicated 90-day programme with onboarding, mid-point review, and executive wrap-up — so your team sees measurable progress.',
  },
  {
    icon: BarChart3,
    title: 'AI Resilience Baseline',
    description:
      'Establish your organisation\'s maturity baseline against NIST CSF 2.0 functions before the market demands it from vendors or regulators.',
  },
  {
    icon: Map,
    title: 'Prioritised Remediation Roadmap',
    description:
      'Receive an effort-vs-impact ranked roadmap validated by our advisory team — ready to present to your CISO or board.',
  },
  {
    icon: Building2,
    title: 'Executive Reporting Package',
    description:
      'Board-ready PDF reports in plain language, including a 1-page executive summary aligned to your industry risk profile.',
  },
  {
    icon: MessageSquare,
    title: 'Dedicated Slack Channel',
    description:
      'Direct access to the ResilAI team during your pilot. Ask questions, share context, and get expert interpretation of findings.',
  },
  {
    icon: Star,
    title: 'Early Feature Access',
    description:
      'Co-shape the product. Pilot participants get early access to new framework integrations, integrations, and SaaS modules before GA.',
  },
];

// ---------------------------------------------------------------------------
// Page component
// ---------------------------------------------------------------------------

export default function PilotPage() {
  const [form, setForm] = useState<EnterpriseFormState>(defaultState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);

  const update = (field: keyof EnterpriseFormState) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => setForm((prev) => ({ ...prev, [field]: e.target.value }));

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError('');
    try {
      await submitEnterprisePilotLead({
        contact_name: form.contact_name,
        company_name: form.company_name,
        email: form.email,
        industry: form.industry || undefined,
        company_size: form.company_size || undefined,
        team_size: form.team_size || undefined,
        current_security_tools: form.current_security_tools || undefined,
        ai_usage_description: form.ai_usage_description || undefined,
        current_siem_provider: form.current_siem_provider || undefined,
      });
      setSubmitted(true);
      setForm(defaultState);
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to submit. Please try again.'
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex flex-col">
      {/* Header */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800">
        <div className="max-w-5xl mx-auto px-4 h-16 flex items-center justify-between gap-4">
          <Link to="/" className="flex items-center gap-2 text-slate-900 dark:text-slate-100 font-semibold">
            <Rocket className="h-5 w-5 text-primary-600" />
            ResilAI
          </Link>
          <div className="flex items-center gap-4 text-sm">
            <ThemeToggle />
            <Link to="/about" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100">About</Link>
            <Link to="/security" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100">Security</Link>
            <Link to="/status" className="text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-slate-100">Status</Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* Hero */}
        <div className="bg-gradient-to-b from-primary-50 dark:from-primary-950/20 to-transparent border-b border-slate-200 dark:border-slate-800">
          <div className="max-w-5xl mx-auto px-4 py-14 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-xs font-medium mb-5">
              <Users className="h-3.5 w-3.5" />
              Limited Enterprise Pilot — Q3 2025 Cohort
            </div>
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-50 mb-4">
              Join the ResilAI Enterprise Pilot
            </h1>
            <p className="text-lg text-slate-600 dark:text-slate-300 max-w-2xl mx-auto mb-6">
              A structured 90-day programme that gives your security team a credible,
              NIST CSF 2.0-aligned AI resilience baseline — and the roadmap to act on it.
            </p>
            <div className="flex items-center justify-center gap-6 text-sm text-slate-500 dark:text-slate-400">
              <span className="flex items-center gap-1.5"><Clock className="h-4 w-4" />90-day engagement</span>
              <span className="flex items-center gap-1.5"><Shield className="h-4 w-4" />NIST CSF 2.0 aligned</span>
              <span className="flex items-center gap-1.5"><Zap className="h-4 w-4" />2-day response SLA</span>
            </div>
          </div>
        </div>

        <div className="max-w-5xl mx-auto px-4 py-12">
          {/* Benefits grid */}
          <div className="mb-14">
            <h2 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-6 text-center">
              What You Get
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {BENEFITS.map((b) => {
                const Icon = b.icon;
                return (
                  <div
                    key={b.title}
                    className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <div className="p-2 rounded-lg bg-primary-50 dark:bg-primary-900/30">
                        <Icon className="h-5 w-5 text-primary-600 dark:text-primary-400" />
                      </div>
                      <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-100">{b.title}</h3>
                    </div>
                    <p className="text-sm text-slate-500 dark:text-slate-400">{b.description}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Application form */}
          <div className="max-w-2xl mx-auto">
            <Card className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-card">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Rocket className="h-5 w-5 text-primary-500" />
                  Apply for the Enterprise Pilot
                </CardTitle>
                <p className="text-sm text-slate-500 dark:text-slate-400 mt-1">
                  We accept a limited cohort each quarter. We'll respond within 2 business days.
                </p>
              </CardHeader>
              <CardContent>
                {submitted ? (
                  <div className="py-10 text-center space-y-3">
                    <div className="inline-flex items-center justify-center h-16 w-16 rounded-full bg-green-100 dark:bg-green-900/30 mx-auto">
                      <CheckCircle className="h-9 w-9 text-green-600 dark:text-green-400" />
                    </div>
                    <h3 className="text-xl font-bold text-slate-900 dark:text-slate-100">Application Received</h3>
                    <p className="text-slate-600 dark:text-slate-400 max-w-sm mx-auto">
                      Thank you for applying. Our team will be in touch within{' '}
                      <strong>2 business days</strong> to discuss next steps.
                    </p>
                    <Button variant="outline" className="mt-4" onClick={() => setSubmitted(false)}>
                      Submit Another
                    </Button>
                  </div>
                ) : (
                  <>
                    {error && (
                      <div className="mb-5 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-300 text-sm">
                        {error}
                      </div>
                    )}

                    <form onSubmit={onSubmit} className="space-y-4" autoComplete="on">
                      {/* Row: name + email */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Input
                          required
                          label="Your Name"
                          value={form.contact_name}
                          placeholder="Jane Smith"
                          onChange={update('contact_name')}
                        />
                        <Input
                          required
                          type="email"
                          label="Work Email"
                          value={form.email}
                          placeholder="jane@company.com"
                          onChange={update('email')}
                        />
                      </div>

                      {/* Company + industry */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <Input
                          required
                          label="Company Name"
                          value={form.company_name}
                          placeholder="Acme Corp"
                          onChange={update('company_name')}
                        />
                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                            Industry
                          </label>
                          <select
                            className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                            value={form.industry}
                            onChange={update('industry')}
                          >
                            <option value="">Select industry…</option>
                            <option>Financial Services</option>
                            <option>Healthcare</option>
                            <option>Technology / SaaS</option>
                            <option>Critical Infrastructure</option>
                            <option>Government / Public Sector</option>
                            <option>Retail / E-commerce</option>
                            <option>Manufacturing</option>
                            <option>Professional Services</option>
                            <option>Other</option>
                          </select>
                        </div>
                      </div>

                      {/* Size fields */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                          <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                            Company Size
                          </label>
                          <select
                            className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                            value={form.company_size}
                            onChange={update('company_size')}
                          >
                            <option value="">Select size…</option>
                            <option>1–50</option>
                            <option>51–200</option>
                            <option>201–1,000</option>
                            <option>1,001–5,000</option>
                            <option>5,000+</option>
                          </select>
                        </div>
                        <Input
                          label="Security Team Size"
                          value={form.team_size}
                          placeholder="e.g. 5–10"
                          onChange={update('team_size')}
                        />
                      </div>

                      {/* Current tools */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                          Current Security Tools <span className="text-slate-400 font-normal">(optional)</span>
                        </label>
                        <textarea
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 px-3 py-2 text-sm min-h-20 resize-y focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                          value={form.current_security_tools}
                          onChange={update('current_security_tools')}
                          placeholder="SIEM, EDR, CNAPP, cloud monitoring stack…"
                        />
                      </div>

                      {/* SIEM Provider */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                          Current SIEM Provider <span className="text-slate-400 font-normal">(optional)</span>
                        </label>
                        <select
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                          value={form.current_siem_provider}
                          onChange={update('current_siem_provider')}
                        >
                          <option value="">Select SIEM provider…</option>
                          <option>Microsoft Sentinel</option>
                          <option>Splunk</option>
                          <option>IBM QRadar</option>
                          <option>Elastic SIEM</option>
                          <option>Google Chronicle</option>
                          <option>Sumo Logic</option>
                          <option>Datadog</option>
                          <option>CrowdStrike Falcon LogScale</option>
                          <option>Exabeam</option>
                          <option>LogRhythm</option>
                          <option>None – Planning to deploy</option>
                          <option>Other</option>
                        </select>
                      </div>

                      {/* AI usage */}
                      <div>
                        <label className="block text-sm font-medium text-slate-700 dark:text-slate-200 mb-1.5">
                          How does your org currently use AI? <span className="text-slate-400 font-normal">(optional)</span>
                        </label>
                        <textarea
                          className="w-full rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-900 text-slate-900 dark:text-slate-100 placeholder:text-slate-400 dark:placeholder:text-slate-500 px-3 py-2 text-sm min-h-20 resize-y focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-500"
                          value={form.ai_usage_description}
                          onChange={update('ai_usage_description')}
                          placeholder="Deployed LLM-assisted tools, AI in CI/CD, internal copilots, vendor AI services…"
                        />
                      </div>

                      <Button type="submit" disabled={loading} className="w-full gap-2">
                        <Send className="h-4 w-4" />
                        {loading ? 'Submitting…' : 'Apply for Enterprise Pilot'}
                      </Button>

                      <p className="text-center text-xs text-slate-400 dark:text-slate-500">
                        By submitting, you agree to our{' '}
                        <Link to="/security" className="underline">Privacy Policy</Link>.
                        We don't sell your data.
                      </p>
                    </form>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  );
}

