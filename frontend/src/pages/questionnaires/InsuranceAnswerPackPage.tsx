import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { ClipboardCheck, Download, FileSignature, Loader2, PlugZap, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui';
import { useActiveOrgId } from '../../hooks/useActiveOrgId';
import {
  downloadInsuranceAnswerPackPdf,
  getInsuranceAnswerPack,
  type InsuranceAnswerPack,
  type QuestionnaireAnswer,
  type QuestionnaireAnswerValue,
  type QuestionnaireSource,
} from '../../api';

/**
 * Insurance answer pack: a cyber-insurance application pre-filled from live
 * evidence (`GET /api/v1/questionnaires/insurance`). Every answer shows the
 * evidence it rests on, when that evidence was observed and what was not
 * looked at. Nothing here is computed in the browser; the page only filters
 * and lays out what the server decided. The customer signs; ResilAI never
 * submits the application.
 */

type Filter = 'all' | QuestionnaireAnswerValue;

const VALUE_ORDER: QuestionnaireAnswerValue[] = ['yes', 'no', 'partial', 'not_verified', 'human_only'];

const FILTER_LABELS: Record<QuestionnaireAnswerValue, string> = {
  yes: 'Yes',
  no: 'No',
  partial: 'Partly',
  not_verified: 'Not verified',
  human_only: 'You answer',
};

/** Design tokens only (same set as the network map). */
const VALUE_BADGE_CLASS: Record<QuestionnaireAnswerValue, string> = {
  yes: 'border-ready-emerald/40 bg-ready-emerald/10 text-ready-emerald',
  no: 'border-red-500/40 bg-red-500/10 text-red-500',
  partial: 'border-drift-amber/40 bg-drift-amber/10 text-drift-amber',
  not_verified: 'border-outline-variant bg-surface-container-high text-on-surface-variant',
  human_only: 'border-outline-variant bg-surface-container text-on-surface',
};

const VALUE_DOT_CLASS: Record<QuestionnaireAnswerValue, string> = {
  yes: 'bg-ready-emerald',
  no: 'bg-red-500',
  partial: 'bg-drift-amber',
  not_verified: 'bg-on-surface-variant/40',
  human_only: 'bg-on-surface',
};

const SOURCE_STATE_LABEL: Record<QuestionnaireSource['state'], string> = {
  fresh: 'Usable',
  stale: 'Out of date',
  failed: 'Failing',
  no_data: 'No data yet',
  not_connected: 'Not connected',
};

export function formatEvidenceTime(iso: string | null | undefined): string {
  if (!iso) return 'an unknown time';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZoneName: 'short',
  });
}

function AnswerRow({ answer }: { answer: QuestionnaireAnswer }) {
  const { coverage } = answer;
  const hasCoverage = coverage.checked.length > 0 || coverage.not_checked.length > 0;
  return (
    <li className="py-4 first:pt-0 last:pb-0" data-testid={`answer-${answer.id}`} data-value={answer.value}>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
        <p className="min-w-0 text-sm font-semibold text-on-surface">{answer.question}</p>
        <span
          className={`inline-flex shrink-0 items-center gap-1.5 self-start rounded-full border px-2.5 py-0.5 text-xs font-bold ${VALUE_BADGE_CLASS[answer.value]}`}
        >
          <span className={`h-1.5 w-1.5 rounded-full ${VALUE_DOT_CLASS[answer.value]}`} aria-hidden />
          {answer.value_label}
        </span>
      </div>
      <p className="mt-1.5 text-sm text-on-surface-variant">{answer.basis}</p>
      <p className="mt-1 text-xs text-on-surface-variant" data-testid={`evidence-${answer.id}`}>
        {answer.evidence_source ? (
          <>
            <span className="font-semibold text-on-surface">Evidence:</span> {answer.evidence_source}, as of{' '}
            {formatEvidenceTime(answer.evidence_time)}
          </>
        ) : answer.value === 'human_only' ? (
          <>No connected system can answer this. You answer it.</>
        ) : (
          <>No evidence used. Answer this one yourself.</>
        )}
      </p>
      {hasCoverage && answer.value !== 'human_only' && (
        <details className="mt-1.5 text-xs text-on-surface-variant">
          <summary className="cursor-pointer select-none font-semibold text-on-surface-variant hover:text-on-surface">
            What was and was not looked at
          </summary>
          <div className="mt-1.5 space-y-1 pl-3">
            {coverage.checked.length > 0 && (
              <p>
                <span className="font-semibold text-on-surface">Looked at:</span> {coverage.checked.join('; ')}
              </p>
            )}
            {coverage.not_checked.length > 0 && (
              <p>
                <span className="font-semibold text-on-surface">Not looked at:</span> {coverage.not_checked.join('; ')}
              </p>
            )}
          </div>
        </details>
      )}
    </li>
  );
}

export interface InsuranceAnswerPackPageProps {
  /** Override the active organisation (tests, embeds). */
  orgId?: string;
}

export function InsuranceAnswerPackPage({ orgId: orgIdProp }: InsuranceAnswerPackPageProps = {}) {
  const activeOrgId = useActiveOrgId();
  const orgId = orgIdProp || activeOrgId;

  const [pack, setPack] = useState<InsuranceAnswerPack | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!orgId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError(null);
    getInsuranceAnswerPack(orgId)
      .then((data) => {
        if (!cancelled) setPack(data);
      })
      .catch((err: any) => {
        if (!cancelled) setError(err?.message || 'Could not build the answer pack.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [orgId, tick]);

  const onDownload = useCallback(async () => {
    if (!orgId) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      const blob = await downloadInsuranceAnswerPackPdf(orgId);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `ResilAI_Insurance_Answer_Pack_${new Date().toISOString().slice(0, 10)}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err: any) {
      setDownloadError(err?.message || 'Could not download the PDF.');
    } finally {
      setDownloading(false);
    }
  }, [orgId]);

  const visible = useMemo(
    () => (pack ? pack.answers.filter((a) => filter === 'all' || a.value === filter) : []),
    [pack, filter],
  );

  const groups = useMemo(() => {
    if (!pack) return [];
    return pack.topics
      .map((topic) => ({ ...topic, answers: visible.filter((a) => a.topic === topic.id) }))
      .filter((group) => group.answers.length > 0);
  }, [pack, visible]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-5 text-left"
    >
      <header className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
        <div className="flex items-start gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-ready-emerald/30 bg-ready-emerald/15 text-ready-emerald">
            <ClipboardCheck className="h-5 w-5" aria-hidden />
          </div>
          <div className="min-w-0">
            <h1 className="text-2xl font-extrabold tracking-tight text-on-surface">Insurance Answer Pack</h1>
            <p className="mt-0.5 max-w-3xl text-sm text-on-surface-variant">
              A cyber-insurance application filled in from what your connected systems show today. Check each answer,
              answer the ones marked for you, then download the PDF, sign it and send it yourself.
            </p>
          </div>
        </div>
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => setTick((t) => t + 1)} disabled={loading || !orgId}>
            <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} aria-hidden />
            Refresh
          </Button>
          <Button size="sm" onClick={onDownload} disabled={!pack || downloading}>
            {downloading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden /> : <Download className="h-4 w-4" aria-hidden />}
            Download PDF
          </Button>
        </div>
      </header>

      {downloadError && (
        <p role="alert" className="rounded-xl border border-red-500/40 bg-red-500/10 px-3 py-2 text-sm text-red-500">
          {downloadError}
        </p>
      )}

      {loading && !pack && (
        <div className="flex h-48 items-center justify-center rounded-2xl border border-outline-variant bg-surface-container-low text-on-surface-variant">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" aria-hidden /> Reading your connected systems…
        </div>
      )}

      {!loading && !orgId && (
        <div className="rounded-2xl border border-outline-variant bg-surface-container-low p-8 text-center text-on-surface-variant">
          Choose a workspace to build its answer pack.
        </div>
      )}

      {error && !pack && (
        <div className="rounded-2xl border border-outline-variant bg-surface-container-low p-8 text-center">
          <p className="font-semibold text-on-surface">The answer pack could not be built.</p>
          <p className="mt-1 text-sm text-on-surface-variant">{error}</p>
        </div>
      )}

      {pack && (
        <>
          <section
            className="flex flex-col gap-2 rounded-2xl border border-outline-variant bg-surface-container-low p-4 md:flex-row md:items-center md:justify-between"
            aria-label="Attestation notice"
          >
            <div className="flex items-start gap-2.5">
              <FileSignature className="mt-0.5 h-5 w-5 shrink-0 text-ready-emerald" aria-hidden />
              <div>
                <p className="text-sm font-bold text-on-surface" data-testid="attestation-notice">
                  {pack.notice}
                </p>
                <p className="mt-0.5 text-xs text-on-surface-variant">
                  Evidence older than {pack.evidence_max_age_hours} hours, or from a connection that is failing, is never
                  used. ResilAI does not submit this application. Question bank {pack.questionnaire.version}.
                </p>
              </div>
            </div>
            <span
              className={`inline-flex shrink-0 items-center gap-1.5 self-start rounded-full border px-2.5 py-0.5 text-xs font-bold md:self-center ${
                pack.is_demo
                  ? 'border-drift-amber/40 bg-drift-amber/10 text-drift-amber'
                  : 'border-ready-emerald/40 bg-ready-emerald/10 text-ready-emerald'
              }`}
              data-testid="data-label"
            >
              {pack.data_label}
            </span>
          </section>

          {pack.is_demo && (
            <p className="rounded-xl border border-outline-variant bg-surface-container px-3 py-2 text-xs text-on-surface-variant">
              This is a sample workspace. Every answer comes from scripted sample telemetry and describes no real
              organisation; do not send it to an insurer.
            </p>
          )}

          {pack.sources.length === 0 ? (
            <div className="flex flex-col items-start gap-2 rounded-xl border border-dashed border-outline-variant bg-surface-container-low px-4 py-3 text-sm text-on-surface-variant sm:flex-row sm:items-center sm:justify-between">
              <span>No systems are connected yet, so every answer is yours to give.</span>
              <Link to="/connectors" className="inline-flex items-center gap-1.5 font-semibold text-ready-emerald hover:underline">
                <PlugZap className="h-4 w-4" aria-hidden /> Connect a system
              </Link>
            </div>
          ) : (
            <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 rounded-xl border border-outline-variant bg-surface-container-low px-3 py-2 text-xs">
              <span className="font-semibold text-on-surface">Read from:</span>
              {pack.sources.map((s) => (
                <span key={s.source} className="inline-flex items-center gap-1.5 text-on-surface-variant" title={s.reason || undefined}>
                  <span
                    className={`h-1.5 w-1.5 rounded-full ${s.state === 'fresh' ? 'bg-ready-emerald' : s.state === 'failed' ? 'bg-red-500' : 'bg-drift-amber'}`}
                    aria-hidden
                  />
                  {s.label}: {SOURCE_STATE_LABEL[s.state]}
                  {s.as_of && s.state === 'fresh' ? `, ${formatEvidenceTime(s.as_of)}` : ''}
                </span>
              ))}
            </div>
          )}

          <div className="flex flex-wrap gap-2" role="group" aria-label="Filter answers">
            {(['all', ...VALUE_ORDER] as Filter[]).map((value) => {
              const count = value === 'all' ? pack.summary.total : pack.summary.counts[value] ?? 0;
              const label = value === 'all' ? 'All' : FILTER_LABELS[value];
              const active = filter === value;
              return (
                <button
                  key={value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => setFilter(value)}
                  className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ready-emerald ${
                    active
                      ? 'border-outline-variant bg-surface-container-high text-on-surface'
                      : 'border-outline-variant bg-transparent text-on-surface-variant hover:bg-surface-container-low'
                  }`}
                >
                  {value !== 'all' && <span className={`h-1.5 w-1.5 rounded-full ${VALUE_DOT_CLASS[value]}`} aria-hidden />}
                  {label}
                  <span className="tabular-nums opacity-70">{count}</span>
                </button>
              );
            })}
          </div>

          {groups.length === 0 ? (
            <div className="rounded-2xl border border-outline-variant bg-surface-container-low p-8 text-center text-sm text-on-surface-variant">
              No answers match this filter.
            </div>
          ) : (
            <div className="space-y-4">
              {groups.map((group) => (
                <section
                  key={group.id}
                  className="rounded-2xl border border-outline-variant bg-surface-container-low p-4 md:p-5"
                  aria-labelledby={`topic-${group.id}`}
                >
                  <h2 id={`topic-${group.id}`} className="mb-3 text-xs font-bold uppercase tracking-wider text-on-surface-variant">
                    {group.label}
                  </h2>
                  <ul className="divide-y divide-outline-variant">
                    {group.answers.map((answer) => (
                      <AnswerRow key={answer.id} answer={answer} />
                    ))}
                  </ul>
                </section>
              ))}
            </div>
          )}

          <p className="text-xs text-on-surface-variant">{pack.attestation.statement}</p>
        </>
      )}
    </motion.div>
  );
}

export default InsuranceAnswerPackPage;
