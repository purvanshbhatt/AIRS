import { useCallback, useEffect, useState } from 'react';
import { Plus, Scale, Trash2 } from 'lucide-react';
import { useActiveOrg } from '../../hooks/useActiveOrg';
import {
  createAIActSystem,
  deleteAIActSystem,
  getAIActQuestionnaire,
  listAIActSystems,
  setAIActDutyStatus,
} from '../../api';
import type {
  AIActDutyStatus,
  AIActQuestionnaire,
  AIActRiskClass,
  AIActRole,
  AIActSystem,
} from '../../api';

/**
 * EU AI Act inventory for a real organisation.
 *
 * The owner records each AI system, answers a fixed questionnaire, and sees a
 * first risk class with the duties that follow. Every word about the law and
 * every result comes from the server; this component only shows it. A status
 * next to a duty is the owner's own statement and is labelled as such.
 */

const RISK_STYLE: Record<AIActRiskClass, string> = {
  prohibited: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
  high: 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20',
  limited: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
  minimal: 'bg-ready-emerald/10 text-ready-emerald border-ready-emerald/20',
};

const STATUS_LABEL: Record<AIActDutyStatus, string> = {
  not_answered: 'Not answered',
  in_place: 'In place',
  not_in_place: 'Not in place',
};

const INPUT_CLASS =
  'w-full rounded-lg border border-outline-variant/60 bg-surface-container px-3 py-2 text-sm text-on-surface focus:outline-none focus:border-ready-emerald/60';

interface FormState {
  name: string;
  purpose: string;
  vendor: string;
  role: AIActRole;
  answers: Record<string, boolean>;
}

const EMPTY_FORM: FormState = { name: '', purpose: '', vendor: '', role: 'deployer', answers: {} };

function message(err: unknown, fallback: string): string {
  return err instanceof Error && err.message ? err.message : fallback;
}

export function AIActInventory() {
  const { orgId } = useActiveOrg();
  const [questionnaire, setQuestionnaire] = useState<AIActQuestionnaire | null>(null);
  const [systems, setSystems] = useState<AIActSystem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState<FormState>(EMPTY_FORM);

  const load = useCallback(async () => {
    if (!orgId) return;
    setLoading(true);
    setError(null);
    try {
      const [questions, list] = await Promise.all([getAIActQuestionnaire(), listAIActSystems(orgId)]);
      setQuestionnaire(questions ?? null);
      setSystems(list?.systems ?? []);
    } catch (err) {
      setError(message(err, 'Could not load your AI systems.'));
    } finally {
      setLoading(false);
    }
  }, [orgId]);

  useEffect(() => {
    load();
  }, [load]);

  const replaceSystem = (updated: AIActSystem) =>
    setSystems((current) => current.map((s) => (s.id === updated.id ? updated : s)));

  const handleSave = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!orgId || !form.name.trim() || !form.purpose.trim()) return;
    setSaving(true);
    setError(null);
    try {
      const created = await createAIActSystem(orgId, {
        name: form.name.trim(),
        purpose: form.purpose.trim(),
        vendor: form.vendor.trim() || null,
        role: form.role,
        answers: form.answers,
      });
      setSystems((current) => [...current, created]);
      setForm(EMPTY_FORM);
      setAdding(false);
    } catch (err) {
      setError(message(err, 'The system was not saved.'));
    } finally {
      setSaving(false);
    }
  };

  const handleStatus = async (system: AIActSystem, dutyId: string, status: AIActDutyStatus) => {
    if (!orgId) return;
    setError(null);
    try {
      replaceSystem(await setAIActDutyStatus(orgId, system.id, dutyId, status));
    } catch (err) {
      setError(message(err, 'Your statement was not saved.'));
    }
  };

  const handleDelete = async (system: AIActSystem) => {
    if (!orgId) return;
    if (!window.confirm(`Remove "${system.name}" from the inventory? This cannot be undone.`)) return;
    setError(null);
    try {
      await deleteAIActSystem(orgId, system.id);
      setSystems((current) => current.filter((s) => s.id !== system.id));
    } catch (err) {
      setError(message(err, 'The system was not removed.'));
    }
  };

  const toggleAnswer = (key: string) =>
    setForm((current) => ({ ...current, answers: { ...current.answers, [key]: !current.answers[key] } }));

  return (
    <section
      className="max-w-5xl space-y-4 rounded-xl border border-surface-bright bg-surface-container-low p-5 text-left"
      data-testid="ai-act-inventory"
    >
      <header className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-ready-emerald/30 bg-ready-emerald/15 text-ready-emerald">
          <Scale className="h-5 w-5" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <h2 className="text-lg font-extrabold tracking-tight text-on-surface">EU AI Act: your AI systems</h2>
          <p className="mt-0.5 text-sm text-on-surface-variant">
            Record each AI tool you use or supply. You get a first risk class and the duties that follow, from your own
            answers. {questionnaire?.scope_note}
          </p>
        </div>
        {questionnaire && !adding && (
          <button
            type="button"
            onClick={() => setAdding(true)}
            className="flex shrink-0 items-center gap-2 rounded-xl border border-outline-variant/40 bg-surface-container px-3.5 py-2 text-xs font-semibold text-on-surface hover:bg-surface-container-high"
          >
            <Plus className="h-3.5 w-3.5" />
            <span>Add an AI system</span>
          </button>
        )}
      </header>

      {questionnaire && (
        <p className="text-xs text-on-surface-variant" data-testid="ai-act-disclaimer">
          {questionnaire.disclaimer}
        </p>
      )}

      {error && (
        <p role="alert" className="rounded-lg border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-600 dark:text-rose-400">
          {error}
        </p>
      )}

      {adding && questionnaire && (
        <form onSubmit={handleSave} className="space-y-4 rounded-xl border border-outline-variant/60 bg-surface-container p-4" aria-label="Add an AI system">
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="block text-xs font-semibold text-on-surface">
              Name
              <input
                className={`${INPUT_CLASS} mt-1`}
                value={form.name}
                maxLength={120}
                required
                onChange={(e) => setForm({ ...form, name: e.target.value })}
              />
            </label>
            <label className="block text-xs font-semibold text-on-surface">
              Supplier (optional)
              <input
                className={`${INPUT_CLASS} mt-1`}
                value={form.vendor}
                maxLength={120}
                onChange={(e) => setForm({ ...form, vendor: e.target.value })}
              />
            </label>
          </div>
          <label className="block text-xs font-semibold text-on-surface">
            What it is used for
            <textarea
              className={`${INPUT_CLASS} mt-1`}
              rows={2}
              value={form.purpose}
              maxLength={1000}
              required
              onChange={(e) => setForm({ ...form, purpose: e.target.value })}
            />
          </label>

          <fieldset className="space-y-1.5">
            <legend className="text-xs font-semibold text-on-surface">Your role</legend>
            {questionnaire.roles.map((role) => (
              <label key={role.key} className="flex items-start gap-2 text-xs text-on-surface-variant">
                <input
                  type="radio"
                  name="ai-act-role"
                  className="mt-0.5"
                  checked={form.role === role.key}
                  onChange={() => setForm({ ...form, role: role.key })}
                />
                <span>{role.text}</span>
              </label>
            ))}
          </fieldset>

          {questionnaire.sections.map((section) => (
            <fieldset key={section.id} className="space-y-1.5">
              <legend className="text-xs font-semibold text-on-surface">
                {section.title} <span className="font-mono font-normal text-on-surface-variant">({section.article})</span>
              </legend>
              <p className="text-[11px] text-on-surface-variant">{section.help}</p>
              {section.options.map((option) => (
                <label key={option.key} className="flex items-start gap-2 text-xs text-on-surface-variant">
                  <input
                    type="checkbox"
                    className="mt-0.5"
                    checked={!!form.answers[option.key]}
                    onChange={() => toggleAnswer(option.key)}
                  />
                  <span>{option.text}</span>
                </label>
              ))}
            </fieldset>
          ))}

          <div className="flex items-center gap-2">
            <button
              type="submit"
              disabled={saving || !form.name.trim() || !form.purpose.trim()}
              className="rounded-xl bg-ready-emerald px-4 py-2 text-xs font-bold text-white disabled:opacity-60"
            >
              {saving ? 'Saving...' : 'Save and classify'}
            </button>
            <button
              type="button"
              onClick={() => {
                setAdding(false);
                setForm(EMPTY_FORM);
              }}
              className="rounded-xl border border-outline-variant/40 px-4 py-2 text-xs font-semibold text-on-surface"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      {loading ? (
        <p className="text-xs text-on-surface-variant">Loading your AI systems...</p>
      ) : systems.length === 0 ? (
        !adding && (
          <div
            className="rounded-xl border border-dashed border-surface-bright bg-surface-container-low p-6 text-center"
            data-testid="ai-act-empty"
          >
            <h3 className="text-sm font-semibold text-on-surface">No AI systems recorded yet.</h3>
            <p className="mx-auto mt-1 max-w-md text-xs leading-relaxed text-on-surface-variant">
              Nothing is classified until you add a system and answer the questions. ResilAI does not detect AI tools
              for you.
            </p>
          </div>
        )
      ) : (
        <ul className="space-y-3" data-testid="ai-act-systems">
          {systems.map((system) => (
            <li key={system.id} className="space-y-3 rounded-xl border border-outline-variant/60 bg-surface-container p-4">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <h3 className="text-sm font-bold text-on-surface">{system.name}</h3>
                  <p className="text-xs text-on-surface-variant">
                    {system.role === 'provider' ? 'You supply this system' : 'You use this system'}
                    {system.vendor ? ` · Supplier: ${system.vendor}` : ''}
                  </p>
                  <p className="mt-1 text-xs text-on-surface-variant">{system.purpose}</p>
                </div>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded border px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${RISK_STYLE[system.risk_class] ?? ''}`}
                    data-testid={`ai-act-risk-${system.id}`}
                  >
                    {system.risk_label}
                  </span>
                  <button
                    type="button"
                    onClick={() => handleDelete(system)}
                    aria-label={`Remove ${system.name}`}
                    className="rounded-lg border border-outline-variant/40 p-1.5 text-on-surface-variant hover:text-rose-500"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>

              {system.basis.length > 0 && (
                <div>
                  <h4 className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">Why</h4>
                  <ul className="mt-1 space-y-0.5">
                    {system.basis.map((reason, index) => (
                      <li key={`${reason.article}-${index}`} className="text-xs text-on-surface-variant">
                        <span className="font-mono text-on-surface">{reason.article}</span>: {reason.text}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {system.exception_note && (
                <p className="rounded-lg border border-amber-500/20 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-300">
                  {system.exception_note}
                </p>
              )}

              <div>
                <h4 className="text-[11px] font-bold uppercase tracking-wider text-on-surface-variant">
                  Duties ({system.obligations.length})
                </h4>
                <p className="text-[11px] text-on-surface-variant">
                  The status is your own statement. ResilAI has not verified it.
                </p>
                <ul className="mt-2 space-y-2">
                  {system.obligations.map((duty) => (
                    <li key={duty.id} className="flex flex-wrap items-start justify-between gap-2 border-t border-outline-variant/30 pt-2">
                      <div className="min-w-0 flex-1">
                        <p className="text-xs font-semibold text-on-surface">
                          {duty.title} <span className="font-mono font-normal text-on-surface-variant">({duty.article})</span>
                          {duty.duty_of === 'supplier' && (
                            <span className="ml-2 rounded border border-outline-variant/60 px-1.5 py-0.5 text-[9px] font-bold uppercase tracking-wider text-on-surface-variant">
                              Supplier's duty
                            </span>
                          )}
                        </p>
                        <p className="text-xs text-on-surface-variant">{duty.detail}</p>
                      </div>
                      <select
                        aria-label={`${duty.title}: your statement for ${system.name}`}
                        value={duty.status}
                        onChange={(e) => handleStatus(system, duty.id, e.target.value as AIActDutyStatus)}
                        className="rounded-lg border border-outline-variant/60 bg-surface-container-low px-2 py-1 text-xs text-on-surface"
                      >
                        {(Object.keys(STATUS_LABEL) as AIActDutyStatus[]).map((status) => (
                          <option key={status} value={status}>
                            {STATUS_LABEL[status]}
                          </option>
                        ))}
                      </select>
                    </li>
                  ))}
                </ul>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default AIActInventory;
