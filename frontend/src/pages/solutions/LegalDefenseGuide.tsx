import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Lock,
  FileCheck,
  AlertTriangle,
  CheckCircle2,
  ArrowRight,
  Database,
  Key,
  Users,
  Terminal,
  HelpCircle,
  ChevronDown,
  Building,
  Check,
  Download,
  Share2
} from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { Footer } from '../../components/layout/Footer';
import { SEOHead } from '../../components/common/SEOHead';
import { useAuth } from '../../contexts/AuthContext';

export default function LegalDefenseGuide() {
  const navigate = useNavigate();
  const { signInAsDemo } = useAuth();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const handleLaunchLegalDemo = async () => {
    try {
      await signInAsDemo();
    } catch {
      // ignore
    } finally {
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', 'demo-northstar-cole');
      navigate('/morning-brief?vertical=legal');
    }
  };

  const faqItems = [
    {
      q: 'How do legal firms stop cyber attacks and protect client confidentiality?',
      a: 'To stop attacks on legal firms, firms must transition from annual check-the-box reviews to continuous verification. This requires: (1) Enforcing phishing-resistant hardware MFA on all Microsoft 365, Google Workspace, and DMS logins; (2) Maintaining immutable, air-gapped backups (WORM storage) that ransomware cannot delete; (3) Implementing matter-level Zero Trust access boundaries; (4) Continuously verifying endpoint EDR health; and (5) Using continuous incident readiness scoring like ResilAI to prove compliance with ABA Formal Opinion 477R.',
    },
    {
      q: 'Why are law practices targeted by ransomware and cyber criminals?',
      a: 'Law firms are high-leverage data aggregators. Rather than attacking large corporations directly, adversaries compromise law firms to access non-public M&A disclosures, litigation strategies, intellectual property, and client trust accounts. Threat actors use double-extortion tactics, threatening to publicly leak confidential client files unless multimillion-dollar ransoms are paid.',
    },
    {
      q: 'What is ABA Formal Opinion 477R, and how does it relate to cyber defense?',
      a: 'ABA Formal Opinion 477R interprets ABA Model Rule 1.6(c), stating that lawyers have an ethical duty to make reasonable efforts to prevent the inadvertent or unauthorized disclosure of, or unauthorized access to, client information. This explicitly mandates evaluating the sensitivity of data, implementing strong access controls, and continuously managing cybersecurity risks.',
    },
    {
      q: 'How does ResilAI help law firms prove incident readiness?',
      a: 'ResilAI continuously inspects your firm’s live operational infrastructure (Microsoft Entra ID, cloud document vaults, endpoint sensors, and backup systems) to calculate a daily, 100% deterministic incident readiness score. ResilAI provides Managing Partners with a plain-English "Are we ready?" answer, while providing legal IT and MSP teams with verifiable SHA-256 evidence for cyber insurance renewals and client audits.',
    },
    {
      q: 'Can a law firm recover from ransomware without paying the extortion fee?',
      a: 'Yes, but only if the firm possesses verified immutable backups. Standard cloud file versioning and local NAS backups are routinely targeted and purged by attackers weeks before detonating ransomware. ResilAI verifies that backup snapshots utilize Object Lock / WORM immutability, ensuring that clean case files can be restored without paying a ransom.',
    },
  ];

  // Schema.org Structured Data
  const jsonLdSchema = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        '@id': 'https://resilai.org/solutions/legal-firm-cyber-attacks#article',
        isPartOf: { '@type': 'WebSite', '@id': 'https://resilai.org/#website', name: 'ResilAI' },
        headline: 'How to Stop Cyber Attacks on Legal Firms & Law Practices',
        description:
          'A battle-tested 5-step operational protocol to prevent ransomware, safeguard client confidentiality, and enforce continuous ABA Formal Opinion 477R compliance.',
        url: 'https://resilai.org/solutions/legal-firm-cyber-attacks',
        author: { '@type': 'Organization', name: 'ResilAI Cybersecurity Research Team' },
        publisher: { '@type': 'Organization', name: 'ResilAI', logo: { '@type': 'ImageObject', url: 'https://resilai.org/favicon.png' } },
        datePublished: '2026-09-01T08:00:00Z',
        dateModified: '2026-09-27T12:00:00Z',
      },
      {
        '@type': 'HowTo',
        name: 'How to Stop Cyber Attacks on Legal Firms',
        description: 'Comprehensive 5-step checklist for managing partners and legal IT teams to prevent ransomware and client data breach.',
        step: [
          {
            '@type': 'HowToStep',
            name: 'Enforce Phishing-Resistant MFA & Conditional Device Health',
            text: 'Enforce FIDO2/WebAuthn or hardware security keys on all partner and associate Microsoft 365, Google Workspace, and DMS logins.',
          },
          {
            '@type': 'HowToStep',
            name: 'Implement Immutable Air-Gapped Case Backups',
            text: 'Store encrypted case archives in WORM immutable storage (AWS S3 Object Lock, Veeam) with zero deletion privileges.',
          },
          {
            '@type': 'HowToStep',
            name: 'Establish Matter-Level Zero Trust Boundaries',
            text: 'Segregate high-profile client files and continuously audit ethical walls to prevent unauthorized associate or lateral traversal.',
          },
          {
            '@type': 'HowToStep',
            name: 'Automate Continuous Telemetry Verification',
            text: 'Verify endpoint protection (EDR) agent health and patch currency across 100% of partner laptops and mobile devices.',
          },
          {
            '@type': 'HowToStep',
            name: 'Establish Deterministic Incident Readiness Scoring with ResilAI',
            text: 'Connect ResilAI to calculate a daily readiness score with SHA-256 evidence provenance to prove preparedness to cyber insurers and clients.',
          },
        ],
      },
      {
        '@type': 'FAQPage',
        mainEntity: faqItems.map((item) => ({
          '@type': 'Question',
          name: item.q,
          acceptedAnswer: {
            '@type': 'Answer',
            text: item.a,
          },
        })),
      },
    ],
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans selection:bg-primary-500/20">
      <SEOHead
        title="How to Stop Cyber Attacks on Legal Firms & Law Practices | ResilAI"
        description="Comprehensive 5-step operational protocol to stop cyber attacks, prevent ransomware, and protect confidential client matters in law firms. Aligned to ABA Opinion 477R."
        keywords="how to stop attacks on legal firms, law firm cybersecurity, prevent ransomware law firm, legal tech cyber defense, ABA Formal Opinion 477R, client confidentiality protection, law practice security checklist, ResilAI"
        canonicalUrl="https://resilai.org/solutions/legal-firm-cyber-attacks"
        schema={jsonLdSchema}
      />

      <PublicNavbar currentVertical="legal" />

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 border-b border-slate-200 dark:border-slate-800/80 bg-gradient-to-b from-white via-slate-50 to-slate-100 dark:from-slate-900 dark:via-slate-950 dark:to-slate-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-primary-100 dark:bg-primary-950/70 text-primary-800 dark:text-primary-300 border border-primary-200 dark:border-primary-800/60">
            <Lock className="w-3.5 h-3.5" />
            <span>Legal Cybersecurity Defense & Compliance Playbook</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
            How to Stop Cyber Attacks on <span className="heading-gradient-legal">Legal Firms</span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            Law firms are prime targets for ransomware, wire fraud, and data exfiltration. Here is the 5-step operational protocol to protect client confidentiality, satisfy ABA Formal Opinion 477R, and maintain continuous incident readiness.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={handleLaunchLegalDemo}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-primary-600 hover:bg-primary-500 text-white shadow-lg shadow-primary-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Explore Legal Demo Sandbox (Northstar & Cole LLP)</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <Link
              to="/pricing?vertical=legal"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-semibold text-sm bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition-colors flex items-center justify-center gap-2"
            >
              <span>View Firm Readiness Plans</span>
            </Link>
          </div>

          {/* Key Stat Cards */}
          <div className="pt-10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="text-2xl font-black text-rose-600 dark:text-rose-400">68%</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Of law firm breaches originate from stolen credentials or partner spear-phishing.</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="text-2xl font-black text-amber-600 dark:text-amber-400">$4.8M</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Average remediation, litigation, and client attrition cost following a legal breach.</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="text-2xl font-black text-primary-600 dark:text-primary-400">100%</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Deterministic SHA-256 evidence required by cyber insurers for policy validation.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-14 space-y-16">
        
        {/* Section 1: The Threat Landscape */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 text-xs font-mono font-bold uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            <span>Understanding The Threat Vector</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Why Cybercriminals Specifically Target Law Practices
          </h2>
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-base">
            Attorneys and managing partners are entrusted with society’s most critical commercial and private secrets: confidential mergers and acquisitions, sealed litigation filings, proprietary patent blueprints, and trust accounts holding millions in client escrow funds. Threat actors recognize that mid-size and boutique legal firms often possess enterprise-grade data protected only by boutique-grade IT defenses.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
            <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2 text-sm">
                <Lock className="w-4 h-4 text-primary-500" />
                Double-Extortion Ransomware
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Attackers do not just encrypt your case files; they exfiltrate privileged client communication first, threatening public disclosure to destroy client trust and trigger bar disciplinary proceedings.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2 text-sm">
                <Users className="w-4 h-4 text-indigo-500" />
                Escrow & Trust Wire Diversion
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                By gaining access to a single partner’s Microsoft 365 inbox, attackers silently monitor settlement closings and swap wire routing numbers moments before fund disbursement.
              </p>
            </div>
          </div>
        </section>

        {/* Section 2: The 5-Step Defense Protocol */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Shield className="w-4 h-4" />
            <span>The 5-Step Operational Protocol</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            5 Essential Actions to Stop Attacks on Legal Firms
          </h2>

          <div className="space-y-6 pt-2">
            {/* Step 1 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                  STEP 01
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Identity Hygiene</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Enforce Phishing-Resistant MFA & Conditional Device Compliance
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Standard SMS and push-notification MFA are routinely intercepted via reverse-proxy phishing kits (e.g. Evilginx). Legal firms must enforce FIDO2 hardware tokens (YubiKeys) or Windows Hello for Business with biometric verification across all Microsoft 365, Google Workspace, and NetDocuments / iManage logins. Furthermore, apply Conditional Access policies that refuse logins from personal, jailbroken, or unencrypted attorney laptops.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                  STEP 02
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Ransomware Immutability</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Implement Immutable Air-Gapped Case Repositories
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Ransomware actors actively dwell in law firm networks for an average of 16 days to locate and delete local backup snapshots. Enforce the 3-2-1-1-0 backup rule: maintain 3 copies of case files on 2 different media, with 1 offsite, 1 completely immutable (WORM storage via AWS S3 Object Lock or Azure Immutable Blob Storage), and 0 errors verified through automated daily test restores.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                  STEP 03
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Zero Trust Access</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Automate Matter-Level Ethical Walls & Least-Privilege Access
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Attorneys working on Practice Area A should never have blanket read access to the proprietary client files of Practice Area B. Implement automated ethical wall monitoring. If an associate's account is compromised, the blast radius is strictly confined to assigned active matters rather than granting the intruder full firm repository traversal.
              </p>
            </div>

            {/* Step 4 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                  STEP 04
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Continuous Verification</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Replace Annual Questionnaires with Automated Telemetry Audits
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                A point-in-time checklist filled out once a year is obsolete 24 hours later. An unpatched attorney laptop or a disabled EDR agent leaves a gaping vulnerability. Continuous API ingestion from CrowdStrike, Microsoft Defender, and Active Directory ensures you are alerted the exact moment a security control drifts out of policy.
              </p>
            </div>

            {/* Step 5 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-primary-50 dark:bg-primary-950 text-primary-700 dark:text-primary-300 border border-primary-200 dark:border-primary-800">
                  STEP 05
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Executive Visibility</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Quantify Incident Readiness Daily with ResilAI
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Deploy ResilAI to synthesize complex multi-cloud and on-premises telemetry into an unambiguous daily executive question: <strong>"If ransomware hit our firm tonight, can we protect client data and resume operations tomorrow morning?"</strong> Every readiness score is backed by cryptographic SHA-256 evidence that satisfies cyber insurance underwriters and prospective clients.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: Legal Regulatory Alignment Matrix */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 text-xs font-mono font-bold uppercase tracking-wider">
            <FileCheck className="w-4 h-4" />
            <span>Regulatory Standards & Bar Rules</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Aligning Security Telemetry to Legal Bar Standards
          </h2>
          <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
            ResilAI automatically aligns verified operational evidence with core legal obligations:
          </p>

          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
                <tr>
                  <th className="p-3.5 sm:p-4">Standard / Rule</th>
                  <th className="p-3.5 sm:p-4">Legal Mandate</th>
                  <th className="p-3.5 sm:p-4">How ResilAI Verifies It</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-slate-600 dark:text-slate-400">
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">ABA Formal Opinion 477R</td>
                  <td className="p-3.5 sm:p-4">Reasonable security efforts to prevent electronic interception of client matter data.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Continuous verification of encryption in transit and at rest across all document stores.</td>
                </tr>
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">ABA Model Rule 1.6(c)</td>
                  <td className="p-3.5 sm:p-4">Duty of confidentiality regarding all client representations and correspondence.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Audit logs proving zero unauthenticated external access or data exfiltration attempts.</td>
                </tr>
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">Cyber Insurance Policies</td>
                  <td className="p-3.5 sm:p-4">Mandatory 100% MFA deployment across endpoints, email, and remote administrative tools.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Mathematical proof of MFA registration across 100% of Active Directory accounts.</td>
                </tr>
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">State Bar Data Security Acts</td>
                  <td className="p-3.5 sm:p-4">E.g., NY SHIELD Act, California Privacy Rights Act (CPRA) data safeguarding.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Tamper-evident SHA-256 evidence logs ready for rapid breach notification defenses.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 4: Interactive FAQ (SEO & AI Schema Grounding) */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-primary-600 dark:text-primary-400 text-xs font-mono font-bold uppercase tracking-wider">
            <HelpCircle className="w-4 h-4" />
            <span>Frequently Asked Questions</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Legal Firm Cybersecurity & Attack Prevention FAQ
          </h2>

          <div className="space-y-3">
            {faqItems.map((item, index) => {
              const isOpen = openFaq === index;
              return (
                <div
                  key={index}
                  className="rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 overflow-hidden transition-all"
                >
                  <button
                    onClick={() => setOpenFaq(isOpen ? null : index)}
                    className="w-full p-4 sm:p-5 text-left font-semibold text-slate-900 dark:text-slate-100 flex items-center justify-between gap-4 cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors"
                  >
                    <span className="text-sm sm:text-base">{item.q}</span>
                    <ChevronDown className={`w-4 h-4 text-slate-400 shrink-0 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
                  </button>
                  {isOpen && (
                    <div className="px-4 sm:px-5 pb-5 text-xs sm:text-sm text-slate-600 dark:text-slate-400 leading-relaxed border-t border-slate-100 dark:border-slate-800/60 pt-3">
                      {item.a}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </section>

        {/* Bottom CTA Card */}
        <section className="p-8 sm:p-10 rounded-2xl bg-gradient-to-r from-primary-900 via-indigo-950 to-slate-900 text-white shadow-xl space-y-6 text-center">
          <div className="inline-flex p-3 rounded-2xl bg-white/10 text-primary-300">
            <Building className="w-8 h-8" />
          </div>
          <h2 className="text-2xl sm:text-4xl font-bold tracking-tight max-w-xl mx-auto">
            Test Your Law Firm’s Incident Readiness in Real Time
          </h2>
          <p className="text-sm sm:text-base text-slate-300 max-w-xl mx-auto leading-relaxed">
            Experience the ResilAI legal sandbox pre-populated with realistic law firm telemetry (Northstar & Cole LLP). Verify document vault resilience, MFA coverage, and executive readiness in under 2 minutes.
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={handleLaunchLegalDemo}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-white text-slate-900 hover:bg-slate-100 shadow-md transition-all cursor-pointer"
            >
              Launch Legal Firm Sandbox
            </button>
            <Link
              to="/contact?vertical=legal"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-semibold text-sm bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-colors"
            >
              Schedule Partner Briefing
            </Link>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
