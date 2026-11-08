import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Activity, AlertCircle, ArrowRight, Building2, ChevronDown, Scale, Users } from 'lucide-react';
import { createOrganization, ApiRequestError } from '../../api';
import { useAuth } from '../../contexts/AuthContext';
import type { OnboardingIndustry, OnboardingOrgProfile } from '../../types/onboarding';
import { INDUSTRY_CARDS, INITIAL_REAL_PROFILE, TEAM_SIZE_OPTIONS } from './onboardingData';

interface CreateWorkspaceScreenProps {
  /** True when the user already has a workspace and is adding another one. */
  isAdditional?: boolean;
  /** Where to go after the workspace exists. Defaults to the morning brief. */
  nextPath?: string;
}

const INDUSTRY_ICON = { healthcare: Activity, legal: Scale } as const;

/**
 * One screen, one button. Name the organisation, pick an industry, create the
 * workspace. Team size is optional and lives under "More". The first verdict,
 * connectors and the boss report are explained afterwards, on the morning
 * brief, by the FirstRunChecklist.
 */
export function CreateWorkspaceScreen({ isAdditional = false, nextPath = '/morning-brief' }: CreateWorkspaceScreenProps) {
  const navigate = useNavigate();
  const { refreshAuth } = useAuth();
  const [profile, setProfile] = useState<OnboardingOrgProfile>(INITIAL_REAL_PROFILE);
  const [showMore, setShowMore] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = profile.name.trim().length > 0 && !submitting;

  const selectIndustry = (industry: OnboardingIndustry) => setProfile((prev) => ({ ...prev, industry }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;
    setSubmitting(true);
    setError(null);
    try {
      const org = await createOrganization({
        name: profile.name.trim(),
        industry: profile.industry,
        size: profile.size,
      });
      localStorage.setItem('resilai_selected_org_id', org.id);
      localStorage.setItem('resilai_operating_profile', profile.industry);
      if (refreshAuth) {
        try {
          await refreshAuth();
        } catch (refreshErr) {
          console.warn('[CreateWorkspace] Could not refresh organisations:', refreshErr);
        }
      }
      navigate(nextPath, { replace: true });
    } catch (err) {
      if (err instanceof ApiRequestError) {
        setError(err.toDisplayMessage());
      } else {
        setError(err instanceof Error ? err.message : 'We could not create the workspace. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="w-full max-w-xl mx-auto bg-surface-container-low rounded-3xl border border-outline-variant/40 shadow-2xl p-6 sm:p-8 space-y-7 animate-in fade-in duration-300"
      data-testid="create-workspace-screen"
      noValidate
    >
      <div className="flex items-start gap-3.5">
        <div className="w-10 h-10 rounded-xl bg-ready-emerald/10 border border-ready-emerald/30 flex items-center justify-center text-ready-emerald shrink-0 mt-0.5">
          <Building2 className="w-5 h-5" aria-hidden="true" />
        </div>
        <div>
          <h1 className="text-xl sm:text-2xl font-bold text-on-surface tracking-tight">
            {isAdditional ? 'Add another workspace' : 'Set up your workspace'}
          </h1>
          <p className="text-sm text-on-surface-variant mt-1 leading-relaxed">
            Takes about a minute. You will see your morning brief right after.
          </p>
        </div>
      </div>

      {error && (
        <div
          role="alert"
          className="p-4 bg-critical-red/10 border border-critical-red/30 rounded-2xl text-critical-red text-xs flex items-start gap-2.5"
        >
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <span>{error}</span>
        </div>
      )}

      {/* Organisation name */}
      <div>
        <label htmlFor="workspace-name" className="block text-xs font-semibold text-on-surface mb-1.5">
          Organisation name
        </label>
        <div className="relative">
          <Building2 className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" aria-hidden="true" />
          <input
            id="workspace-name"
            type="text"
            value={profile.name}
            onChange={(e) => setProfile((prev) => ({ ...prev, name: e.target.value }))}
            placeholder="e.g. Riverside Family Practice"
            disabled={submitting}
            autoFocus
            autoComplete="organization"
            className="w-full pl-10 pr-4 h-11 bg-surface-container text-sm text-on-surface rounded-xl border border-outline-variant/60 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald disabled:opacity-80 transition-all placeholder-on-surface-variant/50"
          />
        </div>
      </div>

      {/* Industry cards */}
      <fieldset>
        <legend className="block text-xs font-semibold text-on-surface mb-2">What kind of organisation is it?</legend>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3" role="radiogroup" aria-label="Industry">
          {INDUSTRY_CARDS.map((card) => {
            const Icon = INDUSTRY_ICON[card.id];
            const isSelected = profile.industry === card.id;
            return (
              <button
                key={card.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => selectIndustry(card.id)}
                disabled={submitting}
                data-testid={`industry-card-${card.id}`}
                className={`p-4 rounded-2xl border text-left transition-all ${
                  isSelected
                    ? 'border-ready-emerald bg-ready-emerald/10 text-on-surface shadow-sm ring-1 ring-ready-emerald/40'
                    : 'border-outline-variant/40 bg-surface-container hover:border-outline-variant text-on-surface-variant'
                }`}
              >
                <div className="flex items-center gap-2 mb-1.5">
                  <Icon className={`w-5 h-5 ${isSelected ? 'text-ready-emerald' : 'text-on-surface-variant'}`} aria-hidden="true" />
                  <span className="text-sm font-bold text-on-surface">{card.title}</span>
                </div>
                <p className="text-[11px] text-on-surface-variant leading-relaxed">{card.caption}</p>
              </button>
            );
          })}
        </div>
        <div className="mt-2 text-[11px] text-on-surface-variant">
          {profile.industry === 'general' ? (
            <span data-testid="industry-other-selected">
              Using the general checks.{' '}
              <button type="button" onClick={() => selectIndustry('healthcare')} className="font-semibold text-ready-emerald hover:underline">
                Pick an industry instead
              </button>
            </span>
          ) : (
            <>
              Neither?{' '}
              <button
                type="button"
                onClick={() => selectIndustry('general')}
                className="font-semibold text-ready-emerald hover:underline"
                data-testid="industry-other-link"
              >
                Other
              </button>
            </>
          )}
        </div>
      </fieldset>

      {/* Optional details */}
      <div className="border-t border-outline-variant/30 pt-4">
        <button
          type="button"
          onClick={() => setShowMore((v) => !v)}
          aria-expanded={showMore}
          aria-controls="workspace-more"
          className="text-xs font-semibold text-on-surface-variant hover:text-on-surface inline-flex items-center gap-1.5"
        >
          <ChevronDown className={`w-3.5 h-3.5 transition-transform ${showMore ? 'rotate-180' : ''}`} aria-hidden="true" />
          More (optional)
        </button>
        {showMore && (
          <div id="workspace-more" className="mt-3">
            <label htmlFor="workspace-size" className="block text-xs font-semibold text-on-surface mb-1.5">
              Team size
            </label>
            <div className="relative">
              <Users className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-on-surface-variant" aria-hidden="true" />
              <select
                id="workspace-size"
                value={profile.size}
                onChange={(e) => setProfile((prev) => ({ ...prev, size: e.target.value as OnboardingOrgProfile['size'] }))}
                disabled={submitting}
                className="w-full pl-10 pr-8 h-11 bg-surface-container text-sm text-on-surface rounded-xl border border-outline-variant/60 focus:border-ready-emerald focus:ring-1 focus:ring-ready-emerald disabled:opacity-80 transition-all appearance-none"
              >
                {TEAM_SIZE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        )}
      </div>

      {/* Primary action */}
      <div className="space-y-3">
        <button
          type="submit"
          disabled={!canSubmit}
          className="w-full px-6 py-3.5 bg-ready-emerald text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-ready-emerald/20 hover:brightness-110 active:scale-[0.98] transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span>{submitting ? 'Creating your workspace...' : 'Create my workspace'}</span>
          {!submitting && <ArrowRight className="w-4 h-4" aria-hidden="true" />}
        </button>
        {!isAdditional && (
          <p className="text-center text-xs text-on-surface-variant">
            Not ready?{' '}
            <Link to="/demo" className="font-semibold text-ready-emerald hover:underline">
              Just show me an example
            </Link>
          </p>
        )}
      </div>
    </form>
  );
}
