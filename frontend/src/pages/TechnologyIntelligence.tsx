import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate, useSearchParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Cpu, Plus, X, AlertTriangle, Building, ArrowRight, Plug, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import { useActiveOrg } from '../hooks/useActiveOrg';
import { LoadingState } from '../components/readiness/ReadinessStates';
import { PaywallLockCard } from '../components/common/PaywallLockCard';
import {
  getSoftwareStack,
  refreshSoftwareStack,
  getTechAdvisories,
  getWebAssets,
  addWebAsset,
  deleteWebAsset,
  scanWebAsset,
  getTechDeployments,
  createTechStackItem,
  type StackResponse,
  type TechAdvisoriesResponse,
  type TechDeploymentsResponse,
  type WebAsset,
  type WebAssetScanResult,
} from '../api';
import { FixThisWeek } from '../components/techintel/FixThisWeek';
import { OverviewStrip, type RefreshState } from '../components/techintel/OverviewStrip';
import { SoftwareTable } from '../components/techintel/SoftwareTable';
import { AdvisoriesList } from '../components/techintel/AdvisoriesList';
import { WebAssetsPanel, type WebAssetActionError } from '../components/techintel/WebAssetsPanel';
import { DeploymentsPanel } from '../components/techintel/DeploymentsPanel';
import {
  SourceChips,
  deriveCoverage,
  deriveFixActions,
  errorStatus,
  feedsAsOf,
  plainError,
} from '../components/techintel/shared';

type TabId = 'software' | 'advisories' | 'websites' | 'cloud';

const TAB_IDS: TabId[] = ['software', 'advisories', 'websites', 'cloud'];

const TAB_LABEL: Record<TabId, string> = {
  software: 'Software & versions',
  advisories: 'All findings',
  websites: 'Websites & apps',
  cloud: 'Cloud services',
};

const MANUAL_CATEGORIES = [
  'Operating System',
  'Language Runtime',
  'Framework',
  'Database',
  'Web Server',
  'Container Runtime',
  'CI/CD',
  'Cloud Platform',
  'Library',
  'Other',
];

const isTab = (value: unknown): value is TabId => TAB_IDS.includes(value as TabId);

const EMPTY_STACK: StackResponse = {
  items: [],
  summary: { total: 0, vulnerable: 0, critical: 0, known_exploited: 0, end_of_life: 0, last_intel_refresh: null },
  sources: {},
  demo: false,
};

type SectionKey = 'stack' | 'advisories' | 'websites' | 'cloud';
type SectionErrors = Partial<Record<SectionKey, { message: string; detail?: string }>>;

function SectionError({ error, onRetry }: { error: { message: string; detail?: string }; onRetry: () => void }) {
  return (
    <div
      className="flex flex-col sm:flex-row sm:items-center gap-3 rounded-xl border border-critical-red/30 bg-critical-red/10 p-4"
      role="alert"
      data-testid="section-error"
    >
      <AlertTriangle className="w-4 h-4 text-critical-red shrink-0" aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold text-on-surface">{error.message}</p>
        {error.detail && <p className="mt-0.5 text-[11px] font-mono text-on-surface-variant break-words">{error.detail}</p>}
      </div>
      <button
        type="button"
        onClick={onRetry}
        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl border border-outline-variant text-sm font-semibold text-on-surface hover:bg-surface-container cursor-pointer shrink-0"
      >
        <RefreshCw className="w-4 h-4" aria-hidden="true" />
        Try again
      </button>
    </div>
  );
}

export function TechnologyIntelligence() {
  const [searchParams] = useSearchParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { orgId: activeOrgId, orgs, hasOrg, isDemo, loading: orgLoading, selectOrg } = useActiveOrg();
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || activeOrgId || '');

  const requestedTab = searchParams.get('tab') || (location.state as { tab?: string } | null)?.tab;
  const [activeTab, setActiveTab] = useState<TabId>(isTab(requestedTab) ? requestedTab : 'software');
  // "Everything we checked" stays closed unless a link asks for a specific tab.
  const [everythingOpen, setEverythingOpen] = useState(isTab(requestedTab));
  const openTab = (tab: TabId) => {
    setActiveTab(tab);
    setEverythingOpen(true);
  };

  useEffect(() => {
    if (activeOrgId && !searchParams.get('org')) {
      setSelectedOrgId(activeOrgId);
    }
  }, [activeOrgId, searchParams]);

  // Data, straight from the API. Nothing here is filled in client-side.
  const [stack, setStack] = useState<StackResponse>(EMPTY_STACK);
  const [advisories, setAdvisories] = useState<TechAdvisoriesResponse>({ advisories: [], generated_at: null });
  const [webAssets, setWebAssets] = useState<WebAsset[]>([]);
  const [deployments, setDeployments] = useState<TechDeploymentsResponse>({ deployments: [], sources: {}, collected_at: null });
  const [sectionErrors, setSectionErrors] = useState<SectionErrors>({});
  const [loading, setLoading] = useState(true);

  // "Check now"
  const [refresh, setRefresh] = useState<RefreshState>({ running: false, result: null, error: null });
  const [paywalled, setPaywalled] = useState(false);

  // Website scans (this session)
  const [scans, setScans] = useState<Record<string, WebAssetScanResult>>({});
  const [scanningId, setScanningId] = useState<string | null>(null);
  const [scanErrors, setScanErrors] = useState<Record<string, WebAssetActionError>>({});

  // Add software by hand
  const [showAddForm, setShowAddForm] = useState(false);
  const [newItem, setNewItem] = useState({ component_name: '', version: '', category: 'Framework' });
  const [addError, setAddError] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);

  // Ignore answers that arrive after the organization changed.
  const loadSeq = useRef(0);

  const fetchAllData = useCallback(
    async (opts: { silent?: boolean } = {}) => {
      if (!selectedOrgId) {
        setLoading(false);
        return;
      }
      const seq = ++loadSeq.current;
      if (!opts.silent) setLoading(true);

      // Each call is wrapped so a missing endpoint or an automatic sign-out never breaks the others.
      const settle = <T,>(fn: () => Promise<T>): Promise<{ ok: boolean; value?: T; error?: unknown }> =>
        Promise.resolve()
          .then(fn)
          .then(
            value => ({ ok: true, value }),
            (error: unknown) => ({ ok: false, error })
          );

      const [stackRes, advRes, webRes, depRes] = await Promise.all([
        settle(() => getSoftwareStack(selectedOrgId)),
        settle(() => getTechAdvisories(selectedOrgId)),
        settle(() => getWebAssets(selectedOrgId)),
        settle(() => getTechDeployments(selectedOrgId)),
      ]);
      if (seq !== loadSeq.current) return;

      const errors: SectionErrors = {};
      // 404 means "nothing recorded for this workspace yet": that is an empty state, not an error.
      // 401 in the example workspace is the same (there is no account to sign in to); for a real
      // account the API client is already sending the person to the sign-in page.
      const failed = (res: { error?: unknown }, key: SectionKey, action: string) => {
        const status = errorStatus(res.error);
        if (status === 404 || (status === 401 && isDemo)) return;
        errors[key] = plainError(res.error, action);
      };

      if (stackRes.ok) {
        const items = Array.isArray(stackRes.value?.items) ? stackRes.value.items : [];
        setStack({
          ...EMPTY_STACK,
          ...(stackRes.value || {}),
          items,
          summary: { ...EMPTY_STACK.summary, ...(stackRes.value?.summary || {}) },
          sources: stackRes.value?.sources || {},
          demo: Boolean(stackRes.value?.demo),
        });
      } else {
        setStack(EMPTY_STACK);
        failed(stackRes, 'stack', 'load your software list');
      }

      if (advRes.ok) {
        setAdvisories({
          ...(advRes.value || {}),
          advisories: Array.isArray(advRes.value?.advisories) ? advRes.value.advisories : [],
          generated_at: advRes.value?.generated_at || null,
        });
      } else {
        setAdvisories({ advisories: [], generated_at: null });
        failed(advRes, 'advisories', 'load the list of fixes');
      }

      if (webRes.ok) {
        setWebAssets(Array.isArray(webRes.value?.assets) ? webRes.value.assets : []);
      } else {
        setWebAssets([]);
        failed(webRes, 'websites', 'load your websites');
      }

      if (depRes.ok) {
        setDeployments({
          deployments: Array.isArray(depRes.value?.deployments) ? depRes.value.deployments : [],
          sources: depRes.value?.sources || {},
          collected_at: depRes.value?.collected_at || null,
        });
      } else {
        setDeployments({ deployments: [], sources: {}, collected_at: null });
        failed(depRes, 'cloud', 'load your cloud services');
      }

      setSectionErrors(errors);
      setLoading(false);
    },
    [selectedOrgId, isDemo]
  );

  useEffect(() => {
    if (selectedOrgId) {
      setRefresh({ running: false, result: null, error: null });
      setPaywalled(false);
      setScans({});
      setScanErrors({});
      fetchAllData();
    } else if (!orgLoading) {
      setLoading(false);
    }
  }, [selectedOrgId, orgLoading, fetchAllData]);

  const handleRefresh = async () => {
    if (!selectedOrgId || refresh.running) return;
    setRefresh({ running: true, result: null, error: null });
    setPaywalled(false);
    try {
      const result = await refreshSoftwareStack(selectedOrgId);
      setRefresh({
        running: false,
        result: { ...result, errors: Array.isArray(result?.errors) ? result.errors : [] },
        error: null,
      });
      await fetchAllData({ silent: true });
    } catch (err) {
      if (errorStatus(err) === 402) {
        setPaywalled(true);
        setRefresh({ running: false, result: null, error: null });
        return;
      }
      setRefresh({ running: false, result: null, error: plainError(err, 'run the check') });
    }
  };

  const handleAddWebAsset = async (data: { url: string; label: string }) => {
    try {
      const created = await addWebAsset(selectedOrgId, data);
      if (created && typeof created === 'object' && created.id) {
        setWebAssets(prev => [...prev.filter(a => a.id !== created.id), created]);
      } else {
        const res = await getWebAssets(selectedOrgId);
        setWebAssets(Array.isArray(res?.assets) ? res.assets : []);
      }
    } catch (err) {
      throw plainError(err, 'save that address');
    }
  };

  const handleScan = async (assetId: string) => {
    if (!selectedOrgId || scanningId) return;
    setScanningId(assetId);
    setScanErrors(prev => {
      const { [assetId]: _cleared, ...rest } = prev;
      return rest;
    });
    try {
      const result = await scanWebAsset(selectedOrgId, assetId);
      if (result && typeof result === 'object') {
        setScans(prev => ({ ...prev, [assetId]: result }));
      }
    } catch (err) {
      const plain =
        errorStatus(err) === 402
          ? { message: 'Website scans start once this workspace has an active plan.' }
          : plainError(err, 'scan this site');
      setScanErrors(prev => ({ ...prev, [assetId]: plain }));
    } finally {
      setScanningId(null);
    }
  };

  const handleDeleteWebAsset = async (assetId: string) => {
    try {
      await deleteWebAsset(selectedOrgId, assetId);
      setWebAssets(prev => prev.filter(a => a.id !== assetId));
      setScans(prev => {
        const { [assetId]: _removed, ...rest } = prev;
        return rest;
      });
    } catch (err) {
      throw plainError(err, 'remove that address');
    }
  };

  const handleAddSoftware = async (e: React.FormEvent) => {
    e.preventDefault();
    const name = newItem.component_name.trim();
    const version = newItem.version.trim();
    if (!selectedOrgId || !name || !version || adding) return;
    setAdding(true);
    setAddError(null);
    try {
      await createTechStackItem(selectedOrgId, {
        component_name: name,
        version,
        category: newItem.category,
      });
      setShowAddForm(false);
      setNewItem({ component_name: '', version: '', category: 'Framework' });
      await fetchAllData({ silent: true });
      openTab('software');
    } catch (err) {
      setAddError(plainError(err, 'add that program').message);
    } finally {
      setAdding(false);
    }
  };

  if (orgLoading || loading) return <LoadingState message="Loading your software and versions..." />;

  if (!hasOrg && !isDemo) {
    return (
      <div className="space-y-8 animate-fade-up max-w-2xl mx-auto py-12">
        <div className="bg-white dark:bg-slate-900/60 rounded-3xl border border-slate-200 dark:border-slate-800 shadow-sm p-8 sm:p-10 text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-2xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <Building className="w-8 h-8 text-emerald-500" />
          </div>
          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-slate-100">
              Set up your readiness workspace
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 max-w-md mx-auto leading-relaxed">
              Create an organization to see which software you run, which versions need an update, and what to fix first.
            </p>
          </div>
          <div>
            <Link
              to="/onboarding?new=true"
              className="inline-flex items-center gap-2 px-6 py-3.5 bg-gradient-to-br from-primary-600 to-emerald-500 text-white text-sm font-semibold rounded-xl hover:shadow-lg hover:shadow-primary-500/25 transition-all active:scale-[0.98]"
            >
              <Building className="w-4 h-4" />
              <span>Create Organization</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </div>
    );
  }

  const readOnly = isDemo;

  // The short list: the backend's `top_actions` when it sends them, otherwise derived from what we have.
  const topActions = Array.isArray(advisories.top_actions)
    ? advisories.top_actions
    : Array.isArray(stack.top_actions)
      ? stack.top_actions
      : null;
  const fixActions = deriveFixActions({ topActions, advisories: advisories.advisories, items: stack.items });
  const coverage = deriveCoverage(stack.coverage || advisories.coverage, stack.sources, deployments.sources);
  // No connected source and no software listed: we cannot say anything, least of all "all clear".
  const hasSource = coverage.checked.length > 0 || stack.items.length > 0;
  if (coverage.checked.length === 0 && stack.items.length > 0) coverage.checked = ['the software on your list'];
  const asOf =
    stack.as_of ||
    advisories.as_of ||
    feedsAsOf(stack.feeds || advisories.feeds) ||
    stack.summary.last_intel_refresh ||
    advisories.generated_at ||
    null;
  const stale = Boolean(stack.stale || advisories.stale);
  const inputClass =
    'w-full rounded-xl border border-outline-variant bg-surface-container px-3.5 py-2.5 text-sm text-on-surface placeholder:text-on-surface-variant/70 focus:outline-none focus:ring-2 focus:ring-ready-emerald/30';

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="space-y-6 text-left"
      data-testid="technology-intelligence"
    >
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-violet-50/15 dark:bg-violet-950/20 border border-violet-200 dark:border-violet-800/40 rounded-2xl flex items-center justify-center shrink-0">
            <Cpu className="w-5 h-5 text-violet-650 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Software Watch
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-semibold">
              The few software fixes that matter this week, in plain English.
            </p>
          </div>
        </div>
        <div className="flex flex-wrap gap-3 items-center">
          {orgs.length > 1 && (
            <select
              aria-label="Select Organization"
              className="rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-w-[220px] max-w-full focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-bold"
              value={selectedOrgId}
              onChange={(e) => {
                setSelectedOrgId(e.target.value);
                selectOrg(e.target.value);
              }}
            >
              {orgs.map((org) => (
                <option key={org.id} value={org.id}>{org.name}</option>
              ))}
            </select>
          )}
          {!readOnly && (
            <button
              type="button"
              onClick={() => {
                setShowAddForm(true);
                openTab('software');
              }}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl font-extrabold text-sm shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer"
              data-testid="add-software-button"
            >
              <Plus className="w-4 h-4" aria-hidden="true" /> Add software
            </button>
          )}
        </div>
      </div>

      {sectionErrors.stack ? (
        <SectionError error={sectionErrors.stack} onRetry={() => fetchAllData()} />
      ) : (
        <>
          <FixThisWeek actions={fixActions} hasSource={hasSource} onAddWebsite={readOnly ? undefined : () => openTab('websites')} />
          <OverviewStrip
            coverage={coverage}
            asOf={asOf}
            stale={stale}
            demo={stack.demo}
            refresh={refresh}
            onRefresh={handleRefresh}
          />
        </>
      )}

      {paywalled && (
        <div className="space-y-2" data-testid="refresh-paywall">
          <PaywallLockCard
            compact
            feature="Checking your software against live security databases"
            requiredPlan="design-partner"
            onUpgrade={() => navigate('/pricing')}
          />
          <p className="text-xs text-on-surface-variant">
            Your list and everything already found stay visible. Live checks start once this workspace has an active plan.
          </p>
        </div>
      )}

      {/* Everything else, collapsed by default */}
      <section
        className="rounded-2xl border border-outline-variant bg-surface-container-lowest/60"
        aria-labelledby="everything-checked-title"
        data-testid="everything-checked"
      >
        <button
          type="button"
          onClick={() => setEverythingOpen(o => !o)}
          aria-expanded={everythingOpen}
          aria-controls="everything-checked-panel"
          className="w-full px-5 py-4 flex items-center justify-between gap-3 text-left rounded-2xl hover:bg-surface-container transition-colors cursor-pointer"
          data-testid="everything-toggle"
        >
          <span className="min-w-0">
            <span id="everything-checked-title" className="block text-base font-bold text-on-surface">
              Everything we checked
            </span>
            <span className="block text-xs text-on-surface-variant mt-0.5">
              Full software list, matches we could not confirm, websites and cloud services. For your IT person.
            </span>
          </span>
          {everythingOpen ? (
            <ChevronUp className="w-5 h-5 text-on-surface-variant shrink-0" aria-hidden="true" />
          ) : (
            <ChevronDown className="w-5 h-5 text-on-surface-variant shrink-0" aria-hidden="true" />
          )}
        </button>

        {everythingOpen && (
          <div id="everything-checked-panel" className="px-5 pb-5 pt-4 space-y-5 border-t border-outline-variant">
            <SourceChips sources={stack.sources} label="List built from" testId="stack-sources" />

      {/* Add software by hand */}
      {showAddForm && !readOnly && (
        <form
          onSubmit={handleAddSoftware}
          className="rounded-2xl border border-outline-variant bg-surface-container-low p-5 space-y-4"
          data-testid="add-software-form"
        >
          <div className="flex items-start justify-between gap-3">
            <div>
              <h2 className="text-base font-bold text-on-surface">Add software by hand</h2>
              <p className="text-sm text-on-surface-variant mt-0.5">
                For a program we cannot see automatically. The version is on its "About" screen, or ask IT.
              </p>
            </div>
            <button
              type="button"
              onClick={() => {
                setShowAddForm(false);
                setAddError(null);
              }}
              aria-label="Close"
              className="p-1 rounded-xl text-on-surface-variant hover:text-on-surface hover:bg-surface-container cursor-pointer"
            >
              <X className="w-5 h-5" aria-hidden="true" />
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="add-software-name" className="block text-xs font-semibold text-on-surface mb-1">
                Program name
              </label>
              <input
                id="add-software-name"
                type="text"
                placeholder="e.g. PostgreSQL"
                className={inputClass}
                value={newItem.component_name}
                onChange={(e) => setNewItem({ ...newItem, component_name: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="add-software-version" className="block text-xs font-semibold text-on-surface mb-1">
                Version
              </label>
              <input
                id="add-software-version"
                type="text"
                placeholder="e.g. 15.4"
                className={inputClass}
                value={newItem.version}
                onChange={(e) => setNewItem({ ...newItem, version: e.target.value })}
              />
            </div>
            <div>
              <label htmlFor="add-software-category" className="block text-xs font-semibold text-on-surface mb-1">
                Kind of software
              </label>
              <select
                id="add-software-category"
                className={inputClass}
                value={newItem.category}
                onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
              >
                {MANUAL_CATEGORIES.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          </div>
          {addError && (
            <p className="text-sm font-semibold text-critical-red" role="alert" data-testid="add-software-error">
              {addError}
            </p>
          )}
          <button
            type="submit"
            disabled={adding || !newItem.component_name.trim() || !newItem.version.trim()}
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-ready-emerald text-slate-950 text-sm font-bold hover:bg-ready-emerald/90 disabled:opacity-60 disabled:cursor-not-allowed cursor-pointer"
          >
            {adding ? 'Adding...' : 'Add to the list'}
          </button>
        </form>
      )}

      {/* Tabs Selector */}
      <div
        className="flex border-b border-slate-200 dark:border-slate-800 space-x-6 text-sm font-bold text-slate-500 dark:text-slate-400 overflow-x-auto"
        role="tablist"
        aria-label="Technology sections"
      >
        {TAB_IDS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            id={`techintel-tab-${tab}`}
            aria-selected={activeTab === tab}
            aria-controls={`techintel-panel-${tab}`}
            className={`pb-3 border-b-2 transition-all relative whitespace-nowrap cursor-pointer ${
              activeTab === tab
                ? 'text-indigo-600 border-indigo-650 dark:text-indigo-400 dark:border-indigo-400'
                : 'border-transparent hover:text-slate-900 dark:hover:text-slate-200'
            }`}
            onClick={() => setActiveTab(tab)}
            data-testid={`tab-${tab}`}
          >
            {TAB_LABEL[tab]}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="mt-4" role="tabpanel" id={`techintel-panel-${activeTab}`} aria-labelledby={`techintel-tab-${activeTab}`}>
        {activeTab === 'software' &&
          (sectionErrors.stack ? (
            <p className="text-sm text-on-surface-variant">Your software list will appear here once it loads.</p>
          ) : (
            <SoftwareTable
              items={stack.items}
              emptyAction={
                <>
                  <Link
                    to="/connectors"
                    className="inline-flex items-center gap-2 px-5 py-2.5 bg-ready-emerald hover:bg-ready-emerald/90 text-slate-950 text-sm font-bold rounded-xl"
                  >
                    <Plug className="w-4 h-4" aria-hidden="true" />
                    Connect a system
                  </Link>
                  <button
                    type="button"
                    onClick={() => openTab('websites')}
                    className="px-5 py-2.5 rounded-xl border border-outline-variant text-sm font-semibold text-on-surface hover:bg-surface-container cursor-pointer"
                  >
                    Add a website
                  </button>
                </>
              }
            />
          ))}

        {activeTab === 'advisories' &&
          (sectionErrors.advisories ? (
            <SectionError error={sectionErrors.advisories} onRetry={() => fetchAllData()} />
          ) : (
            <AdvisoriesList
              advisories={advisories.advisories}
              generatedAt={advisories.generated_at}
              nothingTracked={stack.items.length === 0}
            />
          ))}

        {activeTab === 'websites' && (
          <div className="space-y-4">
            {sectionErrors.websites && <SectionError error={sectionErrors.websites} onRetry={() => fetchAllData()} />}
            <WebAssetsPanel
              assets={webAssets}
              scans={scans}
              scanningId={scanningId}
              scanErrors={scanErrors}
              readOnly={readOnly}
              onAdd={handleAddWebAsset}
              onScan={handleScan}
              onDelete={handleDeleteWebAsset}
            />
          </div>
        )}

        {activeTab === 'cloud' &&
          (sectionErrors.cloud ? (
            <SectionError error={sectionErrors.cloud} onRetry={() => fetchAllData()} />
          ) : (
            <DeploymentsPanel
              deployments={deployments.deployments}
              sources={deployments.sources}
              collectedAt={deployments.collected_at}
            />
          ))}
      </div>
          </div>
        )}
      </section>
    </motion.div>
  );
}

export default TechnologyIntelligence;
