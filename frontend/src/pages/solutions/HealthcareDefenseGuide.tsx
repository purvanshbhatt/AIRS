import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Shield,
  Activity,
  HeartPulse,
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
  Server,
  Lock
} from 'lucide-react';
import { PublicNavbar } from '../../components/layout/PublicNavbar';
import { Footer } from '../../components/layout/Footer';
import { SEOHead } from '../../components/common/SEOHead';
import { useAuth } from '../../contexts/AuthContext';

export default function HealthcareDefenseGuide() {
  const navigate = useNavigate();
  const { signInAsDemo } = useAuth();
  const [openFaq, setOpenFaq] = useState<number | null>(null);

  const handleLaunchHealthcareDemo = async () => {
    try {
      await signInAsDemo();
    } catch {
      // ignore
    } finally {
      localStorage.setItem('resilai_demo_user', 'true');
      localStorage.setItem('resilai_selected_org_id', 'demo-northstar-health');
      navigate('/morning-brief?vertical=healthcare');
    }
  };

  const faqItems = [
    {
      q: 'How do healthcare businesses and clinics stop cyber attacks and ransomware?',
      a: 'Stopping attacks on healthcare businesses requires a clinical-first defense strategy: (1) Segmenting clinical networks so medical devices and EHR systems are isolated from general office Wi-Fi and billing; (2) Enforcing 100% immutable 3-2-1-1-0 backups (Veeam / AWS S3 Object Lock) that ransomware cannot encrypt or delete; (3) Implementing strict clinical identity hygiene with session timeouts on shared nurse terminals; (4) Continuously verifying security controls against HIPAA Security Rule and HHS Cybersecurity Performance Goals (CPGs); and (5) Utilizing ResilAI to provide clinic directors with a daily deterministic readiness score answering "Can we safely treat patients today?".',
    },
    {
      q: 'Why are hospitals, medical practices, and healthcare businesses targeted so frequently?',
      a: 'Healthcare businesses are targeted because patient care cannot tolerate operational downtime. Threat actors recognize that when clinical electronic health records (EHR) and diagnostic imaging systems are locked, patient lives are put at risk, creating extreme pressure on leadership to pay multimillion-dollar ransoms immediately. Furthermore, protected health information (PHI) commands high prices on the dark web for identity theft and fraudulent billing.',
    },
    {
      q: 'What is the difference between HIPAA compliance and actual incident readiness?',
      a: 'HIPAA compliance is typically evaluated through periodic, point-in-time annual audits and subjective policy documents. Incident readiness is operational: it verifies whether clinical backups will actually restore in under 4 hours, whether EDR sensors are active on every clinical workstation, and whether EHR databases can withstand an active ransomware attack without data corruption. ResilAI bridges this gap by continuously converting live technical telemetry into verifiable proof.',
    },
    {
      q: 'How does ResilAI protect healthcare clinics from ransomware?',
      a: 'ResilAI continuously verifies operational controls across your healthcare IT stack (Microsoft Entra ID, clinical EHR servers, Veeam immutable backups, cloud repositories, and endpoint detection). ResilAI immediately flags configuration drift—such as disabled immutable backup policies, orphaned clinical user accounts, or unencrypted storage volumes—giving healthcare IT and MSPs actionable remediation steps before attackers can strike.',
    },
    {
      q: 'What are HHS Cybersecurity Performance Goals (CPGs)?',
      a: 'The U.S. Department of Health and Human Services (HHS) published Cybersecurity Performance Goals (CPGs) to provide clear, high-impact cybersecurity practices tailored to healthcare organizations. Key requirements include essential actions like revoking credentials for departed workforce members, securing medical imaging protocols, implementing immutable backups, and enforcing multi-factor authentication across all external access points.',
    },
  ];

  // Schema.org Structured Data
  const jsonLdSchema = {
    '@context': 'https://schema.org',
    '@graph': [
      {
        '@type': 'Article',
        '@id': 'https://resilai.org/solutions/healthcare-cyber-attacks#article',
        isPartOf: { '@type': 'WebSite', '@id': 'https://resilai.org/#website', name: 'ResilAI' },
        headline: 'How to Stop Attacks on Healthcare Businesses & Medical Clinics',
        description:
          'A clinical-first operational protocol to prevent ransomware attacks, safeguard EHR systems, and guarantee patient care continuity in healthcare practices.',
        url: 'https://resilai.org/solutions/healthcare-cyber-attacks',
        author: { '@type': 'Organization', name: 'ResilAI Healthcare Security Research Team' },
        publisher: { '@type': 'Organization', name: 'ResilAI', logo: { '@type': 'ImageObject', url: 'https://resilai.org/favicon.png' } },
        datePublished: '2026-09-01T08:00:00Z',
        dateModified: '2026-09-27T12:00:00Z',
      },
      {
        '@type': 'HowTo',
        name: 'How to Stop Attacks on Healthcare Businesses',
        description: 'Comprehensive 5-step operational protocol for healthcare executives, clinic directors, and health IT teams to prevent ransomware and maintain clinical continuity.',
        step: [
          {
            '@type': 'HowToStep',
            name: 'Isolate EHR & Clinical Networks with Zero Trust Micro-segmentation',
            text: 'Enforce strict network isolation between patient Wi-Fi, administrative billing, medical IoT equipment, and core clinical EHR databases.',
          },
          {
            '@type': 'HowToStep',
            name: 'Deploy 100% Immutable Ransomware-Proof Backups',
            text: 'Configure write-once-read-many (WORM) storage with Veeam and AWS S3 Object Lock, validating daily that Recovery Time Objective (RTO) remains under 4 hours.',
          },
          {
            '@type': 'HowToStep',
            name: 'Enforce Clinical Identity Hygiene & 24/7 Access Monitoring',
            text: 'Enforce biometric/hardware MFA for provider remote access, implement automatic screen lock on shared nurse terminals, and purge inactive workforce credentials.',
          },
          {
            '@type': 'HowToStep',
            name: 'Automate Continuous HIPAA Security Rule & HHS CPG Verification',
            text: 'Replace subjective annual HIPAA checklists with continuous automated telemetry monitoring mapped directly to 45 CFR Part 164 standards.',
          },
          {
            '@type': 'HowToStep',
            name: 'Deliver Daily Executive Morning Briefings with ResilAI',
            text: 'Provide clinic managing partners with an unmistakable daily verdict: "Can we safely treat patients today?" backed by tamper-evident cryptographic evidence.',
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
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 text-slate-900 dark:text-slate-100 flex flex-col font-sans selection:bg-emerald-500/20">
      <SEOHead
        title="How to Stop Attacks on Healthcare Businesses & Medical Clinics | ResilAI"
        description="Learn how to stop cyber attacks and prevent ransomware in healthcare businesses. Protect clinical EHR systems, maintain patient continuity, and ensure continuous HIPAA compliance."
        keywords="how to stop attacks on healthcare businesses, healthcare ransomware prevention, protect clinic EHR, hospital cybersecurity, HIPAA Security Rule, clinical continuity, healthcare cyber defense checklist, ResilAI"
        canonicalUrl="https://resilai.org/solutions/healthcare-cyber-attacks"
        schema={jsonLdSchema}
      />

      <PublicNavbar currentVertical="healthcare" />

      {/* Hero Section */}
      <section className="relative pt-16 pb-20 border-b border-slate-200 dark:border-slate-800/80 bg-gradient-to-b from-white via-slate-50 to-emerald-50/20 dark:from-slate-900 dark:via-slate-950 dark:to-slate-950">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-100 dark:bg-emerald-950/70 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60">
            <HeartPulse className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span>Healthcare Clinical Continuity & Ransomware Defense Playbook</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-slate-900 dark:text-white leading-[1.15]">
            How to Stop Cyber Attacks on <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-600 to-teal-600 dark:from-emerald-400 dark:to-teal-300">Healthcare Businesses</span>
          </h1>

          <p className="text-lg sm:text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
            In healthcare, cybersecurity is patient safety. When ransomware shuts down your EHR and diagnostic systems, patient care ceases. Here is the 5-step operational protocol to guarantee clinical continuity, stop ransomware, and maintain continuous HIPAA compliance.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={handleLaunchHealthcareDemo}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-emerald-600 hover:bg-emerald-500 text-white shadow-lg shadow-emerald-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <span>Explore Healthcare Demo Sandbox (Northstar Family Health)</span>
              <ArrowRight className="w-4 h-4" />
            </button>
            <Link
              to="/pricing?vertical=healthcare"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-semibold text-sm bg-white dark:bg-slate-900 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-800 dark:text-slate-200 border border-slate-300 dark:border-slate-700 transition-colors flex items-center justify-center gap-2"
            >
              <span>View Healthcare Clinic Plans</span>
            </Link>
          </div>

          {/* Key Stat Cards */}
          <div className="pt-10 grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="text-2xl font-black text-rose-600 dark:text-rose-400">24 Days</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Average EHR downtime following a successful healthcare ransomware attack.</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="text-2xl font-black text-amber-600 dark:text-amber-400">46%</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Of healthcare attacks force ambulance diversions and canceled clinical procedures.</p>
            </div>
            <div className="p-4 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs">
              <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">&lt; 4 Hours</div>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">Target Recovery Time Objective (RTO) guaranteed by ResilAI immutable backup verification.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Main Content Area */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 py-14 space-y-16">
        
        {/* Section 1: The Threat Landscape */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            <span>Understanding Healthcare Attack Vectors</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Why Ransomware Groups Prioritize Medical Practices
          </h2>
          <p className="text-slate-600 dark:text-slate-300 leading-relaxed text-base">
            Healthcare businesses are under relentless attack by organized Ransomware-as-a-Service (RaaS) syndicates. Attackers recognize that unlike standard commercial businesses that can afford hours of administrative delay, a medical practice or outpatient surgical clinic must treat patients continuously. Attackers weaponize clinical urgency to extort ransom payments.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4">
            <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2 text-sm">
                <Lock className="w-4 h-4 text-emerald-500" />
                EHR Encryption & Clinical Blackout
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                When Electronic Health Record databases (Epic, Cerner, AthenaHealth) are encrypted, patient allergy histories, medication doses, and appointment schedules disappear, paralyzing clinical care.
              </p>
            </div>

            <div className="p-5 rounded-xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-2">
              <h3 className="font-semibold text-slate-900 dark:text-slate-100 flex items-center gap-2 text-sm">
                <Server className="w-4 h-4 text-teal-500" />
                Unsegmented Medical IoT & DICOM
              </h3>
              <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                Legacy diagnostic equipment (X-rays, ultrasounds, MRI workstations) often run unsupported operating systems connected to the same subnet as administrative computers, giving attackers direct lateral traversal.
              </p>
            </div>
          </div>
        </section>

        {/* Section 2: The 5-Step Healthcare Defense Protocol */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Shield className="w-4 h-4" />
            <span>The 5-Step Healthcare Defense Protocol</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            5 Essential Steps to Stop Cyber Attacks on Healthcare Businesses
          </h2>

          <div className="space-y-6 pt-2">
            {/* Step 1 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  STEP 01
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Network Isolation</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Isolate Clinical EHR & Diagnostic Systems with Micro-segmentation
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Never allow medical devices, clinical EHR databases, and general clinic office networks to share the same subnet. Implement Zero Trust micro-segmentation across your firewalls and switches: patient waiting room Wi-Fi must be completely isolated, administrative billing workstations confined to a dedicated VLAN, and medical imaging servers accessible only via authenticated jump hosts.
              </p>
            </div>

            {/* Step 2 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  STEP 02
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Ransomware Immunity</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Deploy 100% Immutable 3-2-1-1-0 Clinical Backups
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Ransomware gangs actively dwell inside clinic networks for weeks to locate and delete local backup catalogs before encrypting servers. You must enforce immutable write-once-read-many (WORM) storage (AWS S3 Object Lock, Veeam Hardened Linux Repositories). ResilAI continuously tests backup snapshot validity and proves that your clinical Recovery Time Objective (RTO) is under 4 hours without paying any ransom.
              </p>
            </div>

            {/* Step 3 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  STEP 03
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Identity Hygiene</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Enforce Strict Clinical Identity Hygiene & Session Discipline
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Healthcare environments face unique identity challenges due to shared nurse workstations and roving clinical providers. Implement badge tap-and-pin authentication, enforce 5-minute inactivity session lockouts, and mandate phishing-resistant FIDO2 MFA for all external physician remote access. Immediately automate the de-provisioning of departed clinical staff and locum tenens providers.
              </p>
            </div>

            {/* Step 4 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  STEP 04
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Automated Governance</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Automate Continuous HIPAA Security Rule & HHS CPG Verification
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Periodic annual HIPAA risk assessments create a false sense of security. ResilAI continuously connects to your clinical infrastructure (Microsoft 365, Active Directory, AWS Security Hub, Veeam) and evaluates control compliance daily against 45 CFR Part 164 standards, turning compliance into an automated, living operational safeguard.
              </p>
            </div>

            {/* Step 5 */}
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="px-2.5 py-1 rounded-md text-xs font-mono font-bold bg-emerald-50 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
                  STEP 05
                </span>
                <span className="text-xs text-slate-500 dark:text-slate-400 font-mono">Clinical Leadership</span>
              </div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                Deliver the Executive "Morning Brief" to Clinic Leadership
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
                Clinic owners and medical directors cannot parse thousands of SIEM event logs. ResilAI delivers a 30-second Morning Brief that answers the only question that matters: <strong>"Can we safely open our doors and treat patients today?"</strong> Drill down through 4 progressive disclosure tiers to inspect exact technical root causes and cryptographic SHA-256 evidence proofs.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: Healthcare Standards Alignment Matrix */}
        <section className="space-y-4">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <Building className="w-4 h-4" />
            <span>Healthcare Compliance & Regulatory Standards</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Mapping Security Telemetry to Healthcare Standards
          </h2>
          <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
            ResilAI automatically aligns verified clinical telemetry with primary healthcare compliance benchmarks:
          </p>

          <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900">
            <table className="w-full text-left text-xs sm:text-sm">
              <thead className="bg-slate-50 dark:bg-slate-800/60 border-b border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-semibold">
                <tr>
                  <th className="p-3.5 sm:p-4">Standard / Rule</th>
                  <th className="p-3.5 sm:p-4">Clinical Mandate</th>
                  <th className="p-3.5 sm:p-4">How ResilAI Verifies It</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800 text-slate-600 dark:text-slate-400">
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">HIPAA 45 CFR §164.308(a)(7)</td>
                  <td className="p-3.5 sm:p-4">Contingency Plan: Data backup plan, disaster recovery, emergency mode operations.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Daily automated verification of immutable snapshot currency and verified RTO recovery.</td>
                </tr>
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">HIPAA 45 CFR §164.312(a)(1)</td>
                  <td className="p-3.5 sm:p-4">Access Control: Unique user identification and automatic logoff protocols.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Active verification of screensaver lock policies and Entra ID MFA enforcement across clinical staff.</td>
                </tr>
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">HHS Cybersecurity Goals (CPGs)</td>
                  <td className="p-3.5 sm:p-4">Essential healthcare cybersecurity practices (mitigating top attack vectors).</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Automated control evaluation tracking workforce credential hygiene and asset vulnerability status.</td>
                </tr>
                <tr>
                  <td className="p-3.5 sm:p-4 font-mono font-bold text-slate-900 dark:text-slate-200">NIST CSF 2.0 Healthcare Profile</td>
                  <td className="p-3.5 sm:p-4">Identify, Protect, Detect, Respond, Recover across clinical systems.</td>
                  <td className="p-3.5 sm:p-4 text-emerald-600 dark:text-emerald-400 font-medium">Deterministic score aggregation linking every NIST subcategory to cryptographic evidence.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* Section 4: Healthcare FAQ (SEO & AI Schema Grounding) */}
        <section className="space-y-6">
          <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 text-xs font-mono font-bold uppercase tracking-wider">
            <HelpCircle className="w-4 h-4" />
            <span>Frequently Asked Questions</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
            Healthcare Incident Readiness & Attack Prevention FAQ
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
        <section className="p-8 sm:p-10 rounded-2xl bg-gradient-to-r from-emerald-950 via-slate-900 to-teal-950 text-white shadow-xl space-y-6 text-center">
          <div className="inline-flex p-3 rounded-2xl bg-white/10 text-emerald-300">
            <HeartPulse className="w-8 h-8" />
          </div>
          <h2 className="text-2xl sm:text-4xl font-bold tracking-tight max-w-xl mx-auto">
            Test Clinical Continuity in the Healthcare Sandbox
          </h2>
          <p className="text-sm sm:text-base text-slate-300 max-w-xl mx-auto leading-relaxed">
            Experience the ResilAI healthcare sandbox pre-populated with realistic clinical practice telemetry (Northstar Family Health). Verify EHR uptime, Veeam immutable backup readiness, and clinical continuity in under 2 minutes.
          </p>
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={handleLaunchHealthcareDemo}
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-bold text-sm bg-white text-slate-900 hover:bg-slate-100 shadow-md transition-all cursor-pointer"
            >
              Launch Healthcare Clinic Sandbox
            </button>
            <Link
              to="/contact?vertical=healthcare"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl font-semibold text-sm bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-colors"
            >
              Schedule Clinical Briefing
            </Link>
          </div>
        </section>

      </main>

      <Footer />
    </div>
  );
}
