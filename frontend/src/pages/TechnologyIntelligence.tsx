import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Cpu, Plus, X, AlertTriangle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, Button } from '../components/ui';
import {
  getOrganizations,
  getTechInventory,
  getTechLifecycle,
  getTechExposure,
  getFrameworkCoverage,
  createTechStackItem,
  getTechStack,
  ApiRequestError,
  TechInventoryItem,
  TechLifecycleAnalysis,
  TechExposureItem,
  FrameworkCoverageItem,
} from '../api';
import { useIsReadOnly } from '../contexts';
import type { Organization } from '../types';

// Import Tab Components
import InventoryTab from '../components/technology/InventoryTab';
import LifecycleTab from '../components/technology/LifecycleTab';
import ExposureTab from '../components/technology/ExposureTab';
import DependenciesTab from '../components/technology/DependenciesTab';
import TimelineTab from '../components/technology/TimelineTab';
import InsightsTab from '../components/technology/InsightsTab';

const BASE_CATEGORIES = [
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

const LTS_OPTIONS = [
  { value: 'lts', label: 'LTS (Long Term Support)' },
  { value: 'active', label: 'Active' },
  { value: 'deprecated', label: 'Deprecated' },
  { value: 'eol', label: 'EOL (End of Life)' },
];

export function TechnologyIntelligence() {
  const [searchParams] = useSearchParams();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [activeTab, setActiveTab] = useState<'inventory' | 'lifecycle' | 'exposure' | 'dependencies' | 'timeline' | 'insights'>('inventory');
  
  // Data States
  const [inventory, setInventory] = useState<TechInventoryItem[]>([]);
  const [lifecycle, setLifecycle] = useState<TechLifecycleAnalysis[]>([]);
  const [exposure, setExposure] = useState<TechExposureItem[]>([]);
  const [coverage, setCoverage] = useState<FrameworkCoverageItem[]>([]);
  
  // Loading & Error States
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [newItem, setNewItem] = useState<{
    component_name: string;
    version: string;
    lts_status: 'lts' | 'active' | 'deprecated' | 'eol';
    major_versions_behind: number;
    category: string;
  }>({
    component_name: '',
    version: '',
    lts_status: 'active',
    major_versions_behind: 0,
    category: 'Framework',
  });
  
  const isReadOnly = useIsReadOnly();

  // Load organizations on mount
  useEffect(() => {
    getOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
      })
      .catch((err) => {
        console.error('Failed to load organizations', err);
      });
  }, []);

  // Fetch all intelligence data when org changes
  const fetchAllData = async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const [invData, lcData, expData, covData] = await Promise.all([
        getTechInventory(selectedOrgId),
        getTechLifecycle(selectedOrgId),
        getTechExposure(selectedOrgId),
        getFrameworkCoverage(selectedOrgId),
      ]);
      setInventory(invData);
      setLifecycle(lcData);
      setExposure(expData);
      setCoverage(covData);
    } catch (err) {
      setError(
        err instanceof ApiRequestError 
          ? err.toDisplayMessage() 
          : 'Failed to synchronize technology intelligence streams.'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
  }, [selectedOrgId]);

  const handleAdd = async () => {
    if (!selectedOrgId || !newItem.component_name || !newItem.version) return;
    try {
      // In Sprint 1.8, creating a tech stack item updates the underlying inventory
      await createTechStackItem(selectedOrgId, {
        component_name: newItem.component_name,
        version: newItem.version,
        lts_status: newItem.lts_status,
        major_versions_behind: newItem.major_versions_behind,
        category: newItem.category,
      });
      setShowAddForm(false);
      setNewItem({
        component_name: '',
        version: '',
        lts_status: 'active',
        major_versions_behind: 0,
        category: 'Framework',
      });
      await fetchAllData();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to register component.'
      );
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="space-y-6 text-left"
    >
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-violet-50/15 dark:bg-violet-950/20 border border-violet-200 dark:border-violet-800/40 rounded-2xl flex items-center justify-center">
            <Cpu className="w-5 h-5 text-violet-650 dark:text-violet-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 tracking-tight">
              Technology Intelligence & AI Estate
            </h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-semibold">
              Are our technology platforms supported and free of active vulnerabilities?
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            aria-label="Select Organization"
            className="rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-bold"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
          {!isReadOnly && (
            <Button onClick={() => setShowAddForm(true)} className="gap-1.5 rounded-xl font-extrabold shadow-sm bg-indigo-600 hover:bg-indigo-700 text-white">
              <Plus className="w-4 h-4" /> Add Component
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Card className="rounded-2xl border-red-200 bg-red-50/20 dark:bg-red-950/10 dark:border-red-900/40 shadow-sm">
          <CardContent className="py-3.5">
            <p className="text-sm text-red-700 dark:text-red-400 font-bold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-red-500" />
              {error}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Add Component Form */}
      {showAddForm && (
        <Card className="rounded-3xl border border-indigo-200 dark:border-indigo-850/80 shadow-md bg-white/60 dark:bg-slate-950/20 transition-all duration-300">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-900 dark:text-slate-100 font-extrabold text-base">Register Technology Component</CardTitle>
              <button onClick={() => setShowAddForm(false)} className="p-1 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
                <X className="w-5 h-5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-200" />
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
                  Component Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Python"
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newItem.component_name}
                  onChange={(e) => setNewItem({ ...newItem, component_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
                  Version
                </label>
                <input
                  type="text"
                  placeholder="e.g. 3.12.0"
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newItem.version}
                  onChange={(e) => setNewItem({ ...newItem, version: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
                  Category
                </label>
                <select
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newItem.category}
                  onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
                >
                  {BASE_CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
                  LTS Status
                </label>
                <select
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newItem.lts_status}
                  onChange={(e) => setNewItem({ ...newItem, lts_status: e.target.value as 'lts' | 'active' | 'deprecated' | 'eol' })}
                >
                  {LTS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-[10px] font-bold text-slate-400 dark:text-slate-500 uppercase tracking-wider mb-1.5">
                  Major Versions Behind
                </label>
                <input
                  type="number"
                  min={0}
                  className="w-full rounded-xl border border-slate-200 dark:border-slate-800 px-3.5 py-2 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newItem.major_versions_behind}
                  onChange={(e) => setNewItem({ ...newItem, major_versions_behind: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
            <div className="pt-2">
              <Button onClick={handleAdd} disabled={!newItem.component_name || !newItem.version} className="rounded-xl font-bold bg-indigo-600 hover:bg-indigo-700 text-white">
                Register Component
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs Selector */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 space-x-6 text-sm font-bold text-slate-500 dark:text-slate-400">
        {(['inventory', 'lifecycle', 'exposure', 'dependencies', 'timeline', 'insights'] as const).map((tab) => (
          <button
            key={tab}
            className={`pb-3 capitalize border-b-2 transition-all relative ${
              activeTab === tab 
                ? 'text-indigo-600 border-indigo-650 dark:text-indigo-400 dark:border-indigo-400' 
                : 'border-transparent hover:text-slate-900 dark:hover:text-slate-200'
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab Panels */}
      <div className="mt-4">
        {activeTab === 'inventory' && (
          <InventoryTab 
            items={inventory} 
            isLoading={loading} 
            error={error} 
            onRetry={fetchAllData} 
          />
        )}
        {activeTab === 'lifecycle' && (
          <LifecycleTab 
            items={lifecycle} 
            isLoading={loading} 
            error={error} 
            onRetry={fetchAllData} 
          />
        )}
        {activeTab === 'exposure' && (
          <ExposureTab 
            items={exposure} 
            isLoading={loading} 
            error={error} 
            onRetry={fetchAllData} 
          />
        )}
        {activeTab === 'dependencies' && (
          <DependenciesTab 
            items={coverage} 
            isLoading={loading} 
            error={error} 
            onRetry={fetchAllData} 
          />
        )}
        {activeTab === 'timeline' && <TimelineTab />}
        {activeTab === 'insights' && <InsightsTab />}
      </div>
    </motion.div>
  );
}

export default TechnologyIntelligence;
