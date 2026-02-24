import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  Badge,
  CardSkeleton,
} from '../components/ui';
import {
  Cpu,
  Plus,
  Trash2,
  AlertTriangle,
  ShieldAlert,
  X,
} from 'lucide-react';
import {
  getOrganizations,
  getTechStack,
  createTechStackItem,
  deleteTechStackItem,
  ApiRequestError,
} from '../api';
import type {
  Organization,
  TechStackItem,
  TechStackItemCreate,
  TechStackSummary,
} from '../types';

const CATEGORIES = [
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

const LTS_OPTIONS: { value: string; label: string }[] = [
  { value: 'lts', label: 'LTS (Long Term Support)' },
  { value: 'active', label: 'Active' },
  { value: 'deprecated', label: 'Deprecated' },
  { value: 'eol', label: 'EOL (End of Life)' },
];

export default function TechStack() {
  const [searchParams] = useSearchParams();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [items, setItems] = useState<TechStackItem[]>([]);
  const [summary, setSummary] = useState<TechStackSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);

  const [newItem, setNewItem] = useState<TechStackItemCreate>({
    component_name: '',
    version: '',
    lts_status: 'active',
    major_versions_behind: 0,
    category: 'Framework',
  });

  useEffect(() => {
    getOrganizations()
      .then((orgs) => {
        setOrganizations(orgs);
        if (!selectedOrgId && orgs.length > 0) {
          setSelectedOrgId(orgs[0].id);
        }
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedOrgId) return;
    loadStack();
  }, [selectedOrgId]);

  const loadStack = async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getTechStack(selectedOrgId);
      setItems(data.items);
      setSummary(data.summary);
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to load tech stack'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!selectedOrgId || !newItem.component_name || !newItem.version) return;
    try {
      await createTechStackItem(selectedOrgId, newItem);
      setShowAddForm(false);
      setNewItem({
        component_name: '',
        version: '',
        lts_status: 'active',
        major_versions_behind: 0,
        category: 'Framework',
      });
      await loadStack();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to add item'
      );
    }
  };

  const handleDelete = async (itemId: string) => {
    if (!selectedOrgId) return;
    try {
      await deleteTechStackItem(selectedOrgId, itemId);
      await loadStack();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to delete item'
      );
    }
  };

  const getRiskBadge = (item: TechStackItem) => {
    if (item.lts_status === 'eol')
      return <Badge variant="danger"><ShieldAlert className="w-3 h-3 mr-1" />Critical</Badge>;
    if (item.lts_status === 'deprecated' || item.major_versions_behind >= 3)
      return <Badge variant="danger"><AlertTriangle className="w-3 h-3 mr-1" />High</Badge>;
    if (item.major_versions_behind >= 1)
      return <Badge variant="warning">Medium</Badge>;
    return <Badge variant="outline">Low</Badge>;
  };

  const getRowBg = (item: TechStackItem) => {
    if (item.lts_status === 'eol') return 'bg-red-50/50 dark:bg-red-900/10';
    if (item.lts_status === 'deprecated') return 'bg-orange-50/50 dark:bg-orange-900/10';
    if (item.major_versions_behind >= 3) return 'bg-orange-50/50 dark:bg-orange-900/10';
    return '';
  };

  if (loading && organizations.length === 0) {
    return <div className="space-y-6"><CardSkeleton /><CardSkeleton /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-violet-100 rounded-lg flex items-center justify-center">
            <Cpu className="w-5 h-5 text-violet-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">
              Tech Stack Registry
            </h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">
              Track component versions and lifecycle risk
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            className="rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 min-w-[220px]"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
          <Button onClick={() => setShowAddForm(true)} className="gap-2">
            <Plus className="w-4 h-4" /> Add Component
          </Button>
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="py-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Summary */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card padding="md">
            <p className="text-sm text-gray-500 dark:text-slate-400">Total Components</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{items.length}</p>
          </Card>
          <Card padding="md" className="border-red-200 dark:border-red-800">
            <p className="text-sm text-red-500">EOL</p>
            <p className="text-2xl font-bold text-red-600">{summary.eol_count}</p>
          </Card>
          <Card padding="md" className="border-orange-200 dark:border-orange-800">
            <p className="text-sm text-orange-500">Deprecated</p>
            <p className="text-2xl font-bold text-orange-600">{summary.deprecated_count}</p>
          </Card>
          <Card padding="md">
            <p className="text-sm text-gray-500 dark:text-slate-400">Risk Breakdown</p>
            <div className="flex items-center gap-2 mt-1">
              {Object.entries(summary.risk_breakdown).map(([level, count]) => (
                <span key={level} className="text-xs">
                  <span className={
                    level === 'critical' ? 'text-red-600' :
                    level === 'high' ? 'text-orange-600' :
                    level === 'medium' ? 'text-yellow-600' : 'text-green-600'
                  }>{level}: {count}</span>
                </span>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* Upgrade Governance Summary */}
      {summary?.upgrade_governance_summary && (
        <Card className="border-violet-200 dark:border-violet-800">
          <CardContent className="py-3">
            <p className="text-sm text-violet-700 dark:text-violet-300 font-medium">
              Upgrade Governance Summary
            </p>
            <p className="text-sm text-gray-600 dark:text-slate-400 mt-1">
              {summary.upgrade_governance_summary}
            </p>
          </CardContent>
        </Card>
      )}

      {/* Add Form */}
      {showAddForm && (
        <Card className="border-indigo-200 dark:border-indigo-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Add Component</CardTitle>
              <button onClick={() => setShowAddForm(false)}>
                <X className="w-5 h-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Component Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. Python"
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newItem.component_name}
                  onChange={(e) => setNewItem({ ...newItem, component_name: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Version
                </label>
                <input
                  type="text"
                  placeholder="e.g. 3.11.4"
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newItem.version}
                  onChange={(e) => setNewItem({ ...newItem, version: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Category
                </label>
                <select
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newItem.category}
                  onChange={(e) => setNewItem({ ...newItem, category: e.target.value })}
                >
                  {CATEGORIES.map((c) => (
                    <option key={c} value={c}>{c}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  LTS Status
                </label>
                <select
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newItem.lts_status}
                  onChange={(e) => setNewItem({ ...newItem, lts_status: e.target.value as TechStackItemCreate['lts_status'] })}
                >
                  {LTS_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Major Versions Behind
                </label>
                <input
                  type="number"
                  min={0}
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newItem.major_versions_behind || 0}
                  onChange={(e) => setNewItem({ ...newItem, major_versions_behind: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
            <Button onClick={handleAdd} disabled={!newItem.component_name || !newItem.version}>
              Add Component
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Table */}
      {loading ? (
        <CardSkeleton />
      ) : items.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Cpu className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-slate-400">
              No components tracked yet. Click "Add Component" to begin.
            </p>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-200 dark:border-slate-700">
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-slate-400">Component</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-slate-400">Version</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-slate-400">Category</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-slate-400">Status</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-slate-400">Behind</th>
                  <th className="text-left py-3 px-4 font-medium text-gray-500 dark:text-slate-400">Risk</th>
                  <th className="text-right py-3 px-4"></th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className={`border-b border-gray-100 dark:border-slate-800 ${getRowBg(item)}`}>
                    <td className="py-3 px-4 font-medium text-gray-900 dark:text-slate-100">
                      {item.component_name}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-slate-400 font-mono text-xs">
                      {item.version}
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-slate-400">{item.category || '—'}</td>
                    <td className="py-3 px-4">
                      <Badge variant={
                        item.lts_status === 'eol' ? 'danger' :
                        item.lts_status === 'deprecated' ? 'warning' :
                        item.lts_status === 'lts' ? 'default' : 'outline'
                      }>
                        {item.lts_status.toUpperCase()}
                      </Badge>
                    </td>
                    <td className="py-3 px-4 text-gray-600 dark:text-slate-400">
                      {item.major_versions_behind > 0 ? `${item.major_versions_behind} major` : '—'}
                    </td>
                    <td className="py-3 px-4">{getRiskBadge(item)}</td>
                    <td className="py-3 px-4 text-right">
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
}
