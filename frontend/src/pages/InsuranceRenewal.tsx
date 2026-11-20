import { Link } from 'react-router-dom';
import {
  ArrowRight,
  FileText,
  FileSignature,
  Plug,
  ListChecks,
  PenLine,
  X,
} from 'lucide-react';
import { PublicNavbar } from '../components/layout/PublicNavbar';
import { Footer } from '../components/layout/Footer';
import { SEOHead } from '../components/common/SEOHead';

/**
 * Public offer page: /insurance-renewal
 *
 * One job: get an IT provider (or a practice) to send one cyber-insurance
 * renewal. Everything said here describes the insurance answer pack as it is
 * built in app/services/questionnaires/ (question bank 2026.11.1) and rendered
 * by app/reports/questionnaire_pdf.py.
 */

/** Where "Send us one renewal" goes. Contact.tsx already reads `?tier=design-partner`. */
export const RENEWAL_CTA_TO = '/contact?tier=design-partner';
export const SAMPLE_PACK_HREF = '/samples/insurance-answer-pack-sample.pdf';

const PRIMARY_BUTTON =
  'w-full sm:w-auto inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 font-bold rounded-xl shadow-sm transition-all duration-200 active:scale-[0.98] min-h-[48px] text-sm text-center whitespace-nowrap';
const SECONDARY_BUTTON =
  'w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 text-on-surface font-semibold rounded-xl border border-outline-variant/60 bg-surface-container-low hover:bg-surface-container-high transition-all active:scale-[0.98] min-h-[48px] text-sm text-center whitespace-nowrap';

const SECTION = 'py-20 sm:py-28 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40';
const EYEBROW = 'text-xs uppercase tracking-widest font-mono font-bold text-ready-emerald';
const H2 = 'text-3xl sm:text-4xl font-semibold tracking-tight text-on-surface [text-wrap:balance]';
const LEAD = 'text-sm sm:text-base text-on-surface-variant leading-relaxed [text-wrap:pretty]';
const CARD = 'p-6 sm:p-8 rounded-2xl bg-surface-container-low border border-outline-variant/60';

type AnswerValue = 'yes' | 'no' | 'not_verified' | 'human_only';

interface SampleRow {
  /** Question id in app/services/questionnaires/insurance_bank.py */
  id: string;
  question: string;
  value: AnswerValue;
  /** Label from ANSWER_LABELS in insurance_answers.py */
  label: string;
  basis: string;
  evidence?: { source: string; time: string };
  lookedAt?: string;
  notLookedAt?: string;
}

/**
 * Four rows of the sample pack (the same demo organisation as the PDF at
 * SAMPLE_PACK_HREF). Question wording is the question bank's; the answers,
 * reasons and coverage lines are what the answer engine returned for that
 * demo workspace.
 */
const SAMPLE_ROWS: SampleRow[] = [
  {
    id: 'SECURITY_MONITORING',
    question: 'Is security activity on your systems watched by a tool that raises alerts?',
    value: 'yes',
    label: 'Yes',
    basis: 'Microsoft Defender is raising alerts (1 alert in the latest sync).',
    evidence: { source: 'Microsoft 365', time: '14 Nov 2026, 02:23 UTC' },
    lookedAt: 'Microsoft Defender alert feed',
    notLookedAt: 'Systems that no connected monitoring tool covers',
  },
  {
    id: 'DEVICE_ENCRYPTION',
    question: 'Are the hard drives of company laptops and desktops encrypted?',
    value: 'no',
    label: 'No',
    basis: 'Microsoft Intune reports 1 device without disk encryption: FRONT-DESK-PC.',
    evidence: { source: 'Microsoft 365', time: '14 Nov 2026, 02:23 UTC' },
    lookedAt: 'Microsoft Intune: 1 enrolled device',
    notLookedAt: 'Computers that are not enrolled in Microsoft Intune; Phones and tablets',
  },
  {
    id: 'ENDPOINT_PROTECTION',
    question:
      'Is endpoint protection (antivirus or EDR) installed, running and reporting on company computers and servers?',
    value: 'not_verified',
    label: 'Not verified: answer manually',
    basis: 'Wazuh is not connected in this sample workspace. Answer this question yourself.',
  },
  {
    id: 'IR_PLAN',
    question: 'Do you have a written plan for responding to a cyber incident such as ransomware or a data breach?',
    value: 'human_only',
    label: 'You answer this',
    basis:
      'A plan is a document; no connected system can confirm it exists or is current. You answer this question yourself.',
  },
];

const BADGE_CLASS: Record<AnswerValue, string> = {
  yes: 'border-ready-emerald/60 bg-ready-emerald/15 text-emerald-950 dark:text-ready-emerald',
  no: 'border-red-500/40 bg-red-500/10 text-red-700 dark:text-red-400',
  not_verified: 'border-outline-variant bg-surface-container-high text-on-surface-variant',
  human_only: 'border-outline-variant bg-surface-container text-on-surface',
};

const DOT_CLASS: Record<AnswerValue, string> = {
  yes: 'bg-ready-emerald',
  no: 'bg-red-500',
  not_verified: 'bg-on-surface-variant/40',
  human_only: 'bg-on-surface',
};

const ANSWER_STATES = [
  {
    name: 'Yes, No or Partly',
    meaning: 'Answered from what a connected system reports. The source and the time are printed beside it.',
  },
  {
    name: 'Not verified',
    meaning:
      'There is no evidence, the evidence is more than 48 hours old, or the connection is failing. You answer it yourself. An old answer is never reused.',
  },
  {
    name: 'You answer',
    meaning: 'No connected system can answer this kind of question, so it is always left to you.',
  },
];

const STEPS = [
  {
    number: '01',
    icon: Plug,
    title: 'Connect read-only',
    body: 'You or your IT provider connect the systems the practice already uses, such as Microsoft 365, AWS, Veeam, Duo, Wazuh or Splunk. ResilAI asks for read access and installs nothing on your computers.',
  },
  {
    number: '02',
    icon: ListChecks,
    title: 'We map evidence to the questions',
    body: 'Fixed rules match what those systems report to each question on the application. No AI writes or rewrites an answer. Where there is no evidence, the answer is left for you.',
  },
  {
    number: '03',
    icon: PenLine,
    title: 'You review and sign',
    body: 'Check each answer, correct any that are wrong and answer the ones marked for you. Then download the PDF, sign it and send it yourself.',
  },
];

const LIMITS = [
  {
    title: 'Plans, training and vendors stay with you',
    body: 'The question bank has 38 questions. Connected systems can answer 17 of them at most. The other 21, about written plans, staff training, payment checks, vendors and past incidents, are always yours to answer.',
  },
  {
    title: 'It only sees what is connected',
    body: 'An answer covers the systems you have connected and nothing else. Each answer lists what was looked at and what was not, so a gap is visible before you sign.',
  },
  {
    title: 'It is not legal or insurance advice',
    body: 'ResilAI does not tell you what an insurer will accept, what a policy covers or what it will cost. Ask your broker or lawyer.',
  },
  {
    title: 'It makes no pass or fail statement',
    body: 'It never says a practice "is compliant" with a law or a standard. It reports what your systems show, with the source and the time.',
  },
];

function PrimaryCta() {
  return (
    <Link to={RENEWAL_CTA_TO} className={PRIMARY_BUTTON} data-testid="renewal-primary-cta">
      <span>Send us one renewal</span>
      <ArrowRight className="w-4 h-4 shrink-0" aria-hidden />
    </Link>
  );
}

function SampleLink() {
  return (
    <a href={SAMPLE_PACK_HREF} target="_blank" rel="noopener noreferrer" className={SECONDARY_BUTTON}>
      <FileText className="w-4 h-4 text-ready-emerald shrink-0" aria-hidden />
      <span>See a sample</span>
      <span className="sr-only"> (PDF, opens in a new tab)</span>
    </a>
  );
}

function SampleAnswerRow({ row }: { row: SampleRow }) {
  return (
    <li className="py-5 first:pt-0 last:pb-0" data-testid={`sample-answer-${row.id}`} data-value={row.value}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <p className="min-w-0 text-sm font-semibold text-on-surface">{row.question}</p>
        <span
          className={`inline-flex shrink-0 items-center gap-1.5 self-start rounded-full border px-2.5 py-0.5 text-xs font-bold ${BADGE_CLASS[row.value]}`}
        >
          <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOT_CLASS[row.value]}`} aria-hidden />
          {row.label}
        </span>
      </div>
      <p className="mt-1.5 text-sm text-on-surface-variant">{row.basis}</p>
      <p className="mt-1 text-xs text-on-surface-variant">
        {row.evidence ? (
          <>
            <span className="font-semibold text-on-surface">Evidence:</span> {row.evidence.source}, as of{' '}
            {row.evidence.time}
          </>
        ) : row.value === 'human_only' ? (
          <>No connected system can answer this. You answer it.</>
        ) : (
          <>No evidence used. Answer this one yourself.</>
        )}
      </p>
      {(row.lookedAt || row.notLookedAt) && (
        <div className="mt-1.5 space-y-0.5 text-xs text-on-surface-variant">
          {row.lookedAt && (
            <p>
              <span className="font-semibold text-on-surface">Looked at:</span> {row.lookedAt}
            </p>
          )}
          {row.notLookedAt && (
            <p>
              <span className="font-semibold text-on-surface">Not looked at:</span> {row.notLookedAt}
            </p>
          )}
        </div>
      )}
    </li>
  );
}

export default function InsuranceRenewalPage() {
  return (
    <div className="min-h-screen bg-background text-on-surface selection:bg-ready-emerald/20 transition-colors duration-300 flex flex-col font-sans">
      <SEOHead
        title="Answer your insurance renewal with proof | ResilAI"
        description="ResilAI fills in a cyber-insurance application from what your connected systems show today, with the source and time beside every answer. You review, sign and send it."
        canonicalUrl="https://resilai.org/insurance-renewal"
      />

      <PublicNavbar />

      <main className="flex-1" data-testid="insurance-renewal-page">
        {/* 1. Hero */}
        <section className="relative pt-12 sm:pt-16 pb-20 px-4 sm:px-6 lg:px-8 border-b border-outline-variant/40">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            <div className="inline-flex items-center gap-2 px-3.5 py-1 bg-surface-container-high text-on-surface-variant rounded-full text-xs font-mono font-medium border border-outline-variant/60">
              <span className="w-2 h-2 rounded-full bg-ready-emerald shrink-0" aria-hidden />
              <span>Cyber-insurance renewals</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold tracking-tight text-on-surface [text-wrap:balance] leading-[1.1]">
              Answer your insurance renewal with proof
            </h1>

            <p className="text-lg sm:text-xl font-medium text-on-surface-variant max-w-2xl mx-auto leading-relaxed [text-wrap:pretty]">
              ResilAI fills in a cyber-insurance application from what a practice&apos;s systems show today, and prints
              the source and the time beside every answer.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
              <PrimaryCta />
              <SampleLink />
            </div>

            <p className="text-xs text-on-surface-variant/80 font-medium">
              Free for the first three design partners for 60 days. You sign and send the application yourself.
            </p>
          </div>
        </section>

        {/* 2. What you get */}
        <section className={SECTION} aria-labelledby="what-you-get">
          <div className="max-w-5xl mx-auto space-y-12">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <p className={EYEBROW}>What you get</p>
              <h2 id="what-you-get" className={H2}>
                An application you can check line by line
              </h2>
              <p className={LEAD}>
                Each answer says which system it came from, when that was seen, what was looked at and what was not. The
                same pack downloads as a PDF with a blank signature block.
              </p>
            </div>

            <div className="max-w-3xl mx-auto rounded-2xl bg-surface-container-low border border-outline-variant/60 p-5 sm:p-6 text-left">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between pb-4 border-b border-outline-variant/60">
                <div className="flex items-start gap-2.5">
                  <FileSignature className="mt-0.5 h-5 w-5 shrink-0 text-ready-emerald" aria-hidden />
                  <p className="text-sm font-bold text-on-surface">
                    You attest. ResilAI shows the evidence it has, as of 14 Nov 2026, 02:23 UTC.
                  </p>
                </div>
                <span
                  className="inline-flex shrink-0 items-center self-start rounded-full border border-outline-variant bg-surface-container-high px-2.5 py-0.5 text-xs font-bold text-on-surface"
                  data-testid="sample-data-label"
                >
                  Sample data from a demo organisation
                </span>
              </div>

              <ul className="divide-y divide-outline-variant/60 pt-5">
                {SAMPLE_ROWS.map((row) => (
                  <SampleAnswerRow key={row.id} row={row} />
                ))}
              </ul>

              <p className="mt-5 pt-4 border-t border-outline-variant/60 text-xs text-on-surface-variant">
                Four of the 38 answers in the sample pack. It describes no real organisation.{' '}
                <a
                  href={SAMPLE_PACK_HREF}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-semibold text-on-surface underline underline-offset-2 hover:text-ready-emerald"
                >
                  Open the full sample (PDF)
                </a>
              </p>
            </div>

            <dl className="grid gap-6 sm:grid-cols-3 max-w-5xl mx-auto">
              {ANSWER_STATES.map((state) => (
                <div key={state.name} className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-2">
                  <dt className="text-base font-bold text-on-surface">{state.name}</dt>
                  <dd className="text-sm text-on-surface-variant leading-relaxed">{state.meaning}</dd>
                </div>
              ))}
            </dl>
          </div>
        </section>

        {/* 3. How it works */}
        <section className={`${SECTION} bg-surface-container-low/40`} aria-labelledby="how-it-works">
          <div className="max-w-5xl mx-auto space-y-12">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <p className={EYEBROW}>How it works</p>
              <h2 id="how-it-works" className={H2}>
                Three steps, and the last one is yours
              </h2>
            </div>

            <ol className="grid gap-6 md:grid-cols-3">
              {STEPS.map((step) => {
                const Icon = step.icon;
                return (
                  <li key={step.number} className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-ready-emerald bg-ready-emerald/10 border border-ready-emerald/20 px-2 py-0.5 rounded">
                        Step {step.number}
                      </span>
                      <Icon className="w-5 h-5 text-ready-emerald" aria-hidden />
                    </div>
                    <h3 className="text-base font-bold text-on-surface">{step.title}</h3>
                    <p className="text-sm text-on-surface-variant leading-relaxed">{step.body}</p>
                  </li>
                );
              })}
            </ol>

            <div className="max-w-3xl mx-auto rounded-2xl bg-surface-container-low border border-outline-variant/60 p-5 sm:p-6 text-center space-y-2">
              <p className="text-base font-bold text-on-surface" data-testid="never-submits">
                You sign and submit the application. ResilAI never submits anything to an insurer.
              </p>
              <p className="text-sm text-on-surface-variant">
                <Link
                  to="/trust/data-access"
                  className="font-semibold text-on-surface underline underline-offset-2 hover:text-ready-emerald"
                >
                  See what ResilAI reads, and where it is kept
                </Link>
              </p>
            </div>
          </div>
        </section>

        {/* 4. Why this is different */}
        <section className={SECTION} aria-labelledby="why-different">
          <div className="max-w-5xl mx-auto space-y-12">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <p className={EYEBROW}>Why this is different</p>
              <h2 id="why-different" className={H2}>
                It starts from your systems, and it does one job
              </h2>
            </div>

            <div className="grid md:grid-cols-2 gap-6">
              <div className={`${CARD} space-y-3`}>
                <h3 className="text-xl font-bold text-on-surface">Compared with questionnaire tools</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">
                  Tools that help you fill in forms store the answers you type and reuse them next year. They do not
                  look at your systems, so an answer is only as good as someone&apos;s memory.
                </p>
                <p className="text-sm text-on-surface leading-relaxed">
                  ResilAI starts from what your systems report today and shows where each answer came from.
                </p>
              </div>

              <div className={`${CARD} space-y-3`}>
                <h3 className="text-xl font-bold text-on-surface">Compared with big compliance platforms</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">
                  Large compliance platforms are built for teams that have a person whose job is compliance. A practice
                  with a manager and an outside IT provider has no such person.
                </p>
                <p className="text-sm text-on-surface leading-relaxed">
                  ResilAI does one job: the insurance application, with proof beside each answer.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 5. What it will not do */}
        <section className={`${SECTION} bg-surface-container-low/40`} aria-labelledby="limits">
          <div className="max-w-5xl mx-auto space-y-12">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <p className={EYEBROW}>What it will not do</p>
              <h2 id="limits" className={H2}>
                The limits, before you send anything
              </h2>
            </div>

            <ul className="grid gap-6 sm:grid-cols-2">
              {LIMITS.map((limit) => (
                <li key={limit.title} className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 flex items-start gap-3">
                  <X className="mt-0.5 w-5 h-5 shrink-0 text-on-surface-variant" aria-hidden />
                  <div className="space-y-1.5">
                    <h3 className="text-base font-bold text-on-surface">{limit.title}</h3>
                    <p className="text-sm text-on-surface-variant leading-relaxed">{limit.body}</p>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </section>

        {/* 6. For IT providers */}
        <section className={SECTION} aria-labelledby="for-it-providers">
          <div className="max-w-5xl mx-auto space-y-12">
            <div className="max-w-3xl mx-auto text-center space-y-4">
              <p className={EYEBROW}>For IT providers</p>
              <h2 id="for-it-providers" className={H2}>
                Send one client with a renewal coming up
              </h2>
              <p className={LEAD} data-testid="design-partner-offer">
                Send one client with a cyber-insurance renewal in the next 60 days. ResilAI fills the application from
                their live systems, with proof for each answer. Free for the first three design partners for 60 days.
              </p>
            </div>

            <div className="grid gap-6 md:grid-cols-3">
              <div className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-2">
                <h3 className="text-base font-bold text-on-surface">What you get</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">
                  The answer pack for that client, built from their connected systems, for the 60 days. A practice
                  without an IT provider can send its own renewal on the same terms.
                </p>
              </div>
              <div className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-2">
                <h3 className="text-base font-bold text-on-surface">What we ask in return</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">
                  A 20-minute call each week for the 60 days. If it worked, a quote from you that we may publish, only
                  with your permission.
                </p>
              </div>
              <div className="p-6 rounded-2xl bg-surface-container-low border border-outline-variant/60 space-y-2">
                <h3 className="text-base font-bold text-on-surface">What it costs after</h3>
                <p className="text-sm text-on-surface-variant leading-relaxed">
                  After the 60 days the listed prices apply: $149 per month, or $399 per month billed annually on the
                  Growth plan.{' '}
                  <Link
                    to="/pricing"
                    className="font-semibold text-on-surface underline underline-offset-2 hover:text-ready-emerald"
                  >
                    See pricing
                  </Link>
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* 7. Final call to action */}
        <section className="py-20 sm:py-28 px-4 sm:px-6 lg:px-8 bg-surface-container-low/40">
          <div className="max-w-3xl mx-auto text-center space-y-6">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-semibold tracking-tight text-on-surface [text-wrap:balance]">
              One renewal is enough to find out
            </h2>
            <p className="text-sm sm:text-base text-on-surface-variant max-w-xl mx-auto leading-relaxed [text-wrap:pretty]">
              Tell us which client and when the renewal is due, and we will take it from there.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-3.5 pt-2">
              <PrimaryCta />
              <SampleLink />
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
