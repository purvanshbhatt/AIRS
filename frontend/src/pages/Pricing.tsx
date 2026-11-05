import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
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
  Lock,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import { useAuth } from '../contexts/AuthContext';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { useCapabilities } from '../hooks/useCapabilities';
import { useToast } from '../components/ui/Toast';
import { SEOHead } from '../components/common/SEOHead';
import {
  activatePlan,
  createCheckoutSession,
  createBillingPortalSession,
  getPublicBillingConfig,
  type PublicBillingConfig,
} from '../api';

const PRICING_URL = 'https://resilai.org/pricing';
const FOUNDING_SEATS_FALLBACK = { total: 50, claimed: 38 };

export default function Pricing() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const { orgId, orgName, isDemo } = useActiveOrg();
  const { isPaid, plan, refresh: refreshCapabilities } = useCapabilities(orgId);
  const { addToast } = useToast();
  const [activatingTier, setActivatingTier] = useState<string | null>(null);
  const [billingConfig, setBillingConfig] = useState<PublicBillingConfig | null>(null);

  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  // Live founding-seat counter + trial terms (public, unauthenticated).
  useEffect(() => {
    let cancelled = false;
    getPublicBillingConfig()
      .then((cfg) => {
        if (!cancelled && cfg && cfg.founding_seats) setBillingConfig(cfg);
      })
      .catch(() => {
        /* keep static fallback */
      });
    return () => {
      cancelled = true;
    };
  }, []);

  // `?checkout=cancelled` — user backed out of Stripe Checkout; nothing was charged.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const params = new URLSearchParams(window.location.search);
    if (params.get('checkout') !== 'cancelled') return;
    addToast({
      title: 'Checkout cancelled',
      message: 'Checkout cancelled — nothing was charged.',
      type: 'info',
    });
    params.delete('checkout');
    const qs = params.toString();
    window.history.replaceState({}, '', `${window.location.pathname}${qs ? `?${qs}` : ''}${window.location.hash}`);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const foundingSeats = billingConfig?.founding_seats;
  const seatsTotal = foundingSeats?.total ?? FOUNDING_SEATS_FALLBACK.total;
  const seatsClaimed = foundingSeats?.claimed ?? FOUNDING_SEATS_FALLBACK.claimed;
  const foundingSoldOut = foundingSeats?.sold_out ?? false;
  const seatsPct = seatsTotal > 0 ? Math.min(100, Math.round((seatsClaimed / seatsTotal) * 100)) : 0;
  const foundingBadge = foundingSoldOut
    ? `All ${seatsTotal} founding seats claimed`
    : `Founding Sysadmin Program · ${seatsClaimed}/${seatsTotal} Claimed`;

  // Trial terms. Backend is authoritative; fall back to 14 days only while loading / on failure.
  const trialDays = billingConfig ? billingConfig.trial_days : 14;
  const trialTerms = trialDays > 0
    ? `${trialDays}-day free trial · no card required · cancel anytime`
    : null;

  const openBillingPortal = async () => {
    if (!orgId) return;
    const portal = await createBillingPortalSession(orgId, `${window.location.origin}/connectors`);
    if (!portal?.url) throw new Error('Billing portal returned no URL.');
    window.location.href = portal.url;
  };

  const isStaging = import.meta.env.MODE === 'staging' || 
                    import.meta.env.VITE_APP_ENV === 'staging' || 
                    (typeof window !== 'undefined' && (
                      window.location.hostname.includes('staging') || 
                      window.location.hostname.includes('localhost') || 
                      window.location.hostname.includes('127.0.0.1')
                    ));

  const handleStartPlan = async (planKey: string) => {
    if (!orgId) {
      navigate('/login');
      return;
    }
    setActivatingTier(planKey);

    if (isStaging) {
      // Staging evaluation flow
      try {
        await activatePlan(orgId, planKey);
        await refreshCapabilities();
        addToast({
          title: 'Design Partner Access Granted',
          message: `Staging evaluation access activated for ${orgName || 'your organization'}. Connectors unlocked.`,
          type: 'ready',
        });
        navigate('/connectors');
      } catch (err: any) {
        console.error('Plan activation error:', err);
        addToast({
          title: 'Activation Failed',
          message: err.message || 'Failed to activate evaluation access.',
          type: 'error',
        });
      } finally {
        setActivatingTier(null);
      }
    } else {
      // Production commercial Stripe checkout flow
      try {
        const origin = window.location.origin;
        const res = await createCheckoutSession(orgId, {
          plan: planKey,
          success_url: `${origin}/connectors?session_id={CHECKOUT_SESSION_ID}&checkout=success`,
          cancel_url: `${origin}/pricing?checkout=cancelled`,
        });
        if (res.checkout_url) {
          window.location.href = res.checkout_url;
        } else {
          throw new Error('No checkout URL returned from payment provider');
        }
      } catch (err: any) {
        if (err?.code === 'SUBSCRIPTION_EXISTS') {
          // Org already subscribed — manage the existing subscription in the portal instead.
          try {
            await openBillingPortal();
            return;
          } catch (portalErr: any) {
            addToast({
              title: 'Subscription Already Active',
              message: portalErr?.message || 'This workspace already has a subscription, but the billing portal could not be opened.',
              type: 'error',
            });
            setActivatingTier(null);
            return;
          }
        }
        console.error('Checkout error:', err);
        addToast({
          title: err?.code === 'FOUNDING_SOLD_OUT' ? 'Founding Seats Sold Out' : 'Checkout Initialization Failed',
          message: err.message || 'Unable to redirect to Stripe checkout. Please contact billing support.',
          type: 'error',
        });
        setActivatingTier(null);
      }
    }
  };

  const tiers = [
    {
      id: 'design-partner',
      name: 'Design Partner Program',
      tagline: 'Solo IT & Healthcare Clinic Starter (Founding Member Pricing)',
      price: '$149',
      originalPrice: '$199',
      period: '/month · Locked for life for first 50 customers',
      badge: foundingBadge,
      description: 'Built specifically for 1-person IT teams, clinics, and law firms tired of noisy SOC dashboards. Verifies whole network topology, air-gapped backups, and incident readiness in under 15 minutes.',
      features: [
        'Up to 250 network nodes & endpoints',
        'Interactive Whole Network Topology Map & Lateral Containment Simulator',
        'Automated Monday Morning "1-Page Boss Report" (forwardable to non-technical leadership)',
        '1-Click Cyber Insurance Underwriter Verification Binder (Coalition, Chubb, Travelers)',
        '100% Agentless Ingestion (Read-only PowerShell & AWS CloudFormation)',
        'Continuous 24/7 deterministic scoring & overnight verification',
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
      tagline: 'Multi-Site Clinics, Regional Firms & Scaling Operations',
      price: '$399',
      originalPrice: '$499',
      period: '/month · Billed annually ($3,990/yr)',
      badge: null,
      description: 'For growing clinics and organizations requiring continuous posture visibility across multiple identity and operational systems.',
      features: [
        'Up to 500 network nodes & endpoints',
        'All 7 technology domain mini-products (Identity, Devices, Backups, Email, Network, Cloud, AI)',
        'Multi-cloud telemetry (AWS + Azure/Entra ID + Google Cloud)',
        'Continuous automated drift alerting & webhook notifications',
        'Cryptographic SHA-256 evidence ledger for auditor inspection',
        'Team access (up to 5 administrators) & standard business-hours SLA',
        'Actionable Needs Attention triage & 1-click remediation workflows',
      ],
      cta: 'Start Growth Plan ($399/mo)',
      ctaTo: '/contact?tier=growth',
      featured: false,
    },
    {
      id: 'enterprise',
      name: 'Enterprise',
      tagline: 'Multi-Facility Health Systems & Regulated Enterprises',
      price: 'Custom Deployment',
      originalPrice: null,
      period: 'Tailored Contract & Dedicated Hosting',
      badge: null,
      description: 'For hospital networks, multi-facility clinics, and compliance-regulated organizations with complex tenancy and sovereignty needs.',
      features: [
        'Unlimited assets & multi-tenant organization hierarchy & RBAC',
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

  const faqs = useMemo(() => [
    {
      question: 'Is there a free trial?',
      answer: trialDays > 0
        ? `Yes. Every self-serve plan starts with a ${trialDays}-day free trial — no card required. You can set up connectors and ingest telemetry during the trial. When you subscribe, Stripe Checkout collects a billing address and tax ID so the invoice can be expensed through your organization.`
        : 'Not at the moment. Self-serve plans are billed through Stripe Checkout, which collects a billing address and tax ID so the invoice can be expensed through your organization.',
    },
    {
      question: 'How does the Founding Sysadmin ($149/mo) program work?',
      answer: 'We are locking in $149/month for life for our first 50 customers (regularly $199/month). In exchange, founding members agree to a single 20-minute onboarding screen-share with our engineers so we can observe telemetry ingestion and collect raw product feedback.',
    },
    {
      question: 'Do I have to install software agents on all company laptops?',
      answer: 'No. ResilAI is 100% agentless. Ingestion connects via pre-baked, copy-paste read-only PowerShell commands for Microsoft 365 / Entra ID / Defender and 1-click AWS CloudFormation templates. Nothing is installed on client endpoints.',
    },
    {
      question: 'Can I cancel anytime? Is there a long-term contract?',
      answer: 'Yes, you can cancel anytime with a single click in your workspace settings. There are no mandatory multi-year commitments or lock-in penalties on self-serve tiers.',
    },
    {
      question: 'What telemetry connectors are supported?',
      answer: 'ResilAI supports Splunk MCP, Wazuh HEC/API, Microsoft Graph, Azure AD / Entra ID, AWS CloudTrail, Veeam backup logs, CrowdStrike, and custom JSON webhook ingestion.',
    },
    {
      question: 'Does ResilAI send confidential log data to external LLMs?',
      answer: 'No. Layer 1 scoring is strictly deterministic and evaluated on-server via mathematical rules. Only normalized finding summaries (with zero raw confidential telemetry) flow into Gemini for plain-English executive translation.',
    },
    {
      question: 'Can we test ResilAI without connecting our live systems?',
      answer: 'Yes. You can explore our pre-populated Acme Health Systems sandbox immediately with zero setup required to inspect executive morning briefs and progressive disclosure workflows.',
    },
  ], [trialDays]);

  // Structured data: FAQPage from the rendered FAQs + Product with one Offer per tier.
  const seoSchema = useMemo(() => [
    {
      '@context': 'https://schema.org',
      '@type': 'FAQPage',
      mainEntity: faqs.map((faq) => ({
        '@type': 'Question',
        name: faq.question,
        acceptedAnswer: { '@type': 'Answer', text: faq.answer },
      })),
    },
    {
      '@context': 'https://schema.org',
      '@type': 'Product',
      name: 'ResilAI',
      url: PRICING_URL,
      description: 'Agentless incident readiness verification for clinics, law firms, and regulated organizations.',
      brand: { '@type': 'Brand', name: 'ResilAI' },
      offers: {
        '@type': 'AggregateOffer',
        priceCurrency: 'USD',
        lowPrice: '149',
        highPrice: '399',
        offerCount: 3,
        url: PRICING_URL,
        offers: [
          {
            '@type': 'Offer',
            name: 'Design Partner Program',
            price: '149',
            priceCurrency: 'USD',
            url: PRICING_URL,
            availability: foundingSoldOut ? 'https://schema.org/SoldOut' : 'https://schema.org/InStock',
          },
          {
            '@type': 'Offer',
            name: 'Growth',
            price: '399',
            priceCurrency: 'USD',
            url: PRICING_URL,
            availability: 'https://schema.org/InStock',
          },
          {
            '@type': 'Offer',
            name: 'Enterprise',
            priceCurrency: 'USD',
            url: 'https://resilai.org/contact?tier=enterprise',
            availability: 'https://schema.org/InStock',
          },
        ],
      },
    },
  ], [faqs, foundingSoldOut]);

  return (
    <div className="min-h-screen bg-background text-on-surface flex flex-col selection:bg-primary-500/20 transition-colors duration-300">
      <SEOHead
        title="ResilAI Pricing — Early Access & Enterprise Tiers"
        description="Transparent pricing for agentless incident readiness: $149/mo Founding Sysadmin seats, $399/mo Growth, and custom Enterprise deployments. Free trial, no card required."
        keywords="ResilAI pricing, incident readiness pricing, security posture pricing, founding sysadmin"
        canonicalUrl={PRICING_URL}
        schema={seoSchema}
      />
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
              <span className="heading-gradient-general">
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
            {/* Authenticated Workspace Status Banner */}
            {user && !isDemo && orgId && (
              <div className="mb-10 p-4 bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-primary-500/10 border border-primary-500/30 flex items-center justify-center text-primary-600 dark:text-primary-400 shrink-0">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-900 dark:text-slate-100">Workspace:</span>
                      <span className="text-xs font-mono font-bold text-primary-600 dark:text-primary-400">{orgName || orgId}</span>
                    </div>
                    <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                      Logged in as <span className="font-mono text-slate-800 dark:text-slate-200">{user.email}</span> · Current Status:{' '}
                      <strong className="font-mono uppercase text-slate-900 dark:text-slate-100">
                        {plan} ({isPaid ? 'Active' : 'Unpaid'})
                      </strong>
                    </p>
                  </div>
                </div>
                {isPaid ? (
                  <Link
                    to="/connectors"
                    className="px-4 py-2 bg-emerald-500 text-white font-bold text-xs rounded-xl hover:bg-emerald-600 transition-all flex items-center gap-1.5 shrink-0"
                  >
                    <span>Manage Connectors</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                ) : (
                  <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-500/15 text-amber-600 dark:text-amber-400 border border-amber-500/30 shrink-0">
                    Select a plan below to unlock live infrastructure
                  </span>
                )}
              </div>
            )}

            {/* Founding Sysadmin First 50 Customers Offer Banner */}
            <div className="mb-12 p-6 sm:p-8 rounded-3xl bg-gradient-to-r from-indigo-900/30 via-slate-900 to-emerald-950/40 border-2 border-indigo-500/40 shadow-xl relative overflow-hidden text-left">
              <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
                <div className="space-y-2 max-w-2xl">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                    <span>EARLY ADOPTER INCENTIVE · FIRST 50 CUSTOMERS</span>
                  </div>
                  <h3 className="text-xl sm:text-2xl font-black text-white">
                    Founding Sysadmin Tier: $149/mo Locked for Life
                  </h3>
                  <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                    Regularly $199/month. In exchange for locked-in $149/mo lifetime pricing, founding members agree to a single 20-minute onboarding screen-share with our engineering team to observe telemetry ingestion. No pushy sales calls, no lock-in, 100% agentless.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-4 shrink-0 w-full md:w-auto">
                  <div className="bg-slate-900/80 border border-slate-700/80 px-4 py-3 rounded-2xl text-center">
                    <div className="text-xs text-slate-400 font-medium">Founding Seats</div>
                    <div className="text-lg font-black text-emerald-400 font-mono">
                      {foundingSoldOut ? `All ${seatsTotal} founding seats claimed` : `${seatsClaimed} / ${seatsTotal} Claimed`}
                    </div>
                    <div className="w-full bg-slate-800 rounded-full h-1.5 mt-1.5 overflow-hidden">
                      <div className="bg-emerald-500 h-1.5 rounded-full" style={{ width: `${foundingSoldOut ? 100 : seatsPct}%` }}></div>
                    </div>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    {foundingSoldOut ? (
                      <button
                        type="button"
                        disabled
                        className="px-6 py-3.5 bg-slate-700 text-slate-300 font-bold text-sm rounded-xl cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        <span>All {seatsTotal} founding seats claimed</span>
                      </button>
                    ) : user && !isDemo && orgId ? (
                      <button
                        type="button"
                        onClick={() => handleStartPlan('design-partner')}
                        disabled={activatingTier === 'design-partner'}
                        className="px-6 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm rounded-xl hover:shadow-lg hover:shadow-emerald-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        <span>Claim Founding Seat ($149/mo)</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    ) : (
                      <Link
                        to="/contact?tier=design-partner"
                        className="px-6 py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-bold text-sm rounded-xl hover:shadow-lg hover:shadow-emerald-500/20 active:scale-[0.98] transition-all flex items-center justify-center gap-2"
                      >
                        <span>Claim Founding Seat ($149/mo)</span>
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    )}
                    {trialTerms && !foundingSoldOut && (
                      <p className="text-center text-[11px] text-emerald-300/90 font-medium">{trialTerms}</p>
                    )}
                  </div>
                </div>
              </div>
            </div>

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
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-xs font-mono font-bold uppercase tracking-wider bg-gradient-to-r from-primary-600 to-emerald-500 text-white shadow-sm whitespace-nowrap">
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
                        {tier.originalPrice && (
                          <span className="text-xl font-bold text-slate-400 dark:text-slate-500 line-through">
                            {tier.originalPrice}
                          </span>
                        )}
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

                  <div className="pt-8 space-y-2">
                    {user && !isDemo && orgId && (tier.id === 'design-partner' || tier.id === 'growth') ? (
                      isPaid && (plan === tier.id || plan === 'enterprise') ? (
                        <Link
                          to="/connectors"
                          className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-bold text-sm bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/25 transition-all"
                        >
                          <Check className="w-4 h-4" />
                          <span>Active Plan — Go to Connectors</span>
                        </Link>
                      ) : (
                        <>
                          {isStaging ? (
                            <>
                              <button
                                type="button"
                                onClick={() => handleStartPlan(tier.id)}
                                disabled={activatingTier === tier.id}
                                className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-bold text-sm bg-gradient-to-r from-primary-600 to-emerald-500 text-white hover:shadow-lg hover:shadow-primary-500/20 active:scale-[0.98] transition-all disabled:opacity-50"
                              >
                                <span>
                                  {activatingTier === tier.id
                                    ? 'Activating Access...'
                                    : `Activate ${tier.name}`}
                                </span>
                                <ArrowRight className="w-4 h-4" />
                              </button>
                              <p className="text-center text-[11px] text-amber-500/90 font-medium pt-1">
                                Staging-only access for ResilAI evaluation. No payment required.
                              </p>
                            </>
                          ) : (
                            <>
                              <button
                                type="button"
                                onClick={() => handleStartPlan(tier.id)}
                                disabled={activatingTier === tier.id || (tier.id === 'design-partner' && foundingSoldOut)}
                                className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-bold text-sm bg-gradient-to-r from-primary-600 to-emerald-500 text-white hover:shadow-lg hover:shadow-primary-500/20 active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                              >
                                <span>
                                  {activatingTier === tier.id
                                    ? 'Redirecting to Checkout...'
                                    : tier.id === 'design-partner' && foundingSoldOut
                                      ? `All ${seatsTotal} founding seats claimed`
                                      : `Start ${tier.name} ($${tier.price.replace('$', '')}/mo)`}
                                </span>
                                {!(tier.id === 'design-partner' && foundingSoldOut) && <ArrowRight className="w-4 h-4" />}
                              </button>
                              {trialTerms && (
                                <p className="text-center text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold pt-1">
                                  {trialTerms}
                                </p>
                              )}
                              <p className="text-center text-[11px] text-slate-500 dark:text-slate-400 font-medium pt-1">
                                Billed securely through Stripe. Connectors unlock instantly after checkout.
                              </p>
                            </>
                          )}
                          <Link
                            to={tier.ctaTo}
                            className="block text-center text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors pt-1"
                          >
                            or request enterprise onboarding walkthrough &rarr;
                          </Link>
                        </>
                      )
                    ) : tier.id === 'design-partner' && foundingSoldOut ? (
                      <button
                        type="button"
                        disabled
                        className="w-full inline-flex items-center justify-center gap-2 py-3.5 px-6 rounded-xl font-bold text-sm bg-slate-200 dark:bg-slate-800 text-slate-500 dark:text-slate-400 cursor-not-allowed"
                      >
                        <span>All {seatsTotal} founding seats claimed</span>
                      </button>
                    ) : (
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
                    )}
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
