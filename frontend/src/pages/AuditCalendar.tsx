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
  Calendar,
  Plus,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Clock,
  X,
} from 'lucide-react';
import {
  getOrganizations,
  getAuditCalendar,
  createAuditCalendarEntry,
  deleteAuditCalendarEntry,
  getAuditForecast,
  ApiRequestError,
} from '../api';
import type {
  Organization,
  AuditCalendarEntry,
  AuditCalendarCreate,
  AuditForecast,
} from '../types';

const COMMON_FRAMEWORKS = [
  'SOC 2 Type II',
  'HIPAA',
  'PCI-DSS v4.0',
  'NIST CSF 2.0',
  'ISO 27001',
  'CMMC Level 2',
  'GDPR',
  'FedRAMP',
];

export default function AuditCalendar() {
  const [searchParams] = useSearchParams();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState(searchParams.get('org') || '');
  const [entries, setEntries] = useState<AuditCalendarEntry[]>([]);
  const [upcomingCount, setUpcomingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [forecasts, setForecasts] = useState<Record<string, AuditForecast>>({});
  const [loadingForecast, setLoadingForecast] = useState<string | null>(null);

  // Add form state
  const [newEntry, setNewEntry] = useState<AuditCalendarCreate>({
    framework: '',
    audit_date: '',
    audit_type: 'external',
    reminder_days_before: 90,
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
    loadCalendar();
  }, [selectedOrgId]);

  const loadCalendar = async () => {
    if (!selectedOrgId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await getAuditCalendar(selectedOrgId);
      setEntries(data.entries);
      setUpcomingCount(data.upcoming_count);
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to load audit calendar'
      );
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!selectedOrgId || !newEntry.framework || !newEntry.audit_date) return;
    try {
      await createAuditCalendarEntry(selectedOrgId, newEntry);
      setShowAddForm(false);
      setNewEntry({ framework: '', audit_date: '', audit_type: 'external', reminder_days_before: 90 });
      await loadCalendar();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to add entry'
      );
    }
  };

  const handleDelete = async (entryId: string) => {
    if (!selectedOrgId) return;
    try {
      await deleteAuditCalendarEntry(selectedOrgId, entryId);
      await loadCalendar();
    } catch (err) {
      setError(
        err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to delete entry'
      );
    }
  };

  const loadForecast = async (entryId: string) => {
    if (!selectedOrgId || forecasts[entryId]) return;
    setLoadingForecast(entryId);
    try {
      const forecast = await getAuditForecast(selectedOrgId, entryId);
      setForecasts((prev) => ({ ...prev, [entryId]: forecast }));
    } catch {
      // Silently fail
    } finally {
      setLoadingForecast(null);
    }
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  if (loading && organizations.length === 0) {
    return <div className="space-y-6"><CardSkeleton /><CardSkeleton /></div>;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-amber-100 rounded-lg flex items-center justify-center">
            <Calendar className="w-5 h-5 text-amber-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">
              Audit Calendar
            </h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">
              Track upcoming audits and get pre-audit risk forecasts
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
            <Plus className="w-4 h-4" /> Schedule Audit
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

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card padding="md">
          <p className="text-sm text-gray-500 dark:text-slate-400">Total Audits</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{entries.length}</p>
        </Card>
        <Card padding="md">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-500" />
            <p className="text-sm text-gray-500 dark:text-slate-400">Upcoming</p>
          </div>
          <p className="text-2xl font-bold text-amber-600">{upcomingCount}</p>
        </Card>
        <Card padding="md">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-4 h-4 text-green-500" />
            <p className="text-sm text-gray-500 dark:text-slate-400">Completed</p>
          </div>
          <p className="text-2xl font-bold text-green-600">
            {entries.filter((e) => e.days_until_audit === 0 && !e.is_upcoming).length}
          </p>
        </Card>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <Card className="border-indigo-200 dark:border-indigo-800">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Schedule New Audit</CardTitle>
              <button onClick={() => setShowAddForm(false)}>
                <X className="w-5 h-5 text-gray-400 hover:text-gray-600" />
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Framework
                </label>
                <select
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newEntry.framework}
                  onChange={(e) => setNewEntry({ ...newEntry, framework: e.target.value })}
                >
                  <option value="">Select framework...</option>
                  {COMMON_FRAMEWORKS.map((f) => (
                    <option key={f} value={f}>{f}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Audit Date
                </label>
                <input
                  type="date"
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newEntry.audit_date}
                  onChange={(e) => setNewEntry({ ...newEntry, audit_date: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Type
                </label>
                <select
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newEntry.audit_type}
                  onChange={(e) => setNewEntry({ ...newEntry, audit_type: e.target.value as 'external' | 'internal' })}
                >
                  <option value="external">External</option>
                  <option value="internal">Internal</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-slate-300 mb-1">
                  Reminder (days before)
                </label>
                <input
                  type="number"
                  className="w-full rounded-lg border border-gray-300 dark:border-slate-700 px-3 py-2 text-sm bg-white dark:bg-slate-900"
                  value={newEntry.reminder_days_before || 90}
                  onChange={(e) => setNewEntry({ ...newEntry, reminder_days_before: parseInt(e.target.value) || 90 })}
                />
              </div>
            </div>
            <Button onClick={handleAdd} disabled={!newEntry.framework || !newEntry.audit_date}>
              Add to Calendar
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Entries */}
      {loading ? (
        <CardSkeleton />
      ) : entries.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Calendar className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 dark:text-slate-400">
              No audits scheduled. Click "Schedule Audit" to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => (
            <Card key={entry.id} className={entry.is_upcoming ? 'border-amber-200 dark:border-amber-800' : ''}>
              <CardContent className="py-4">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-lg font-semibold text-gray-900 dark:text-slate-100">
                        {entry.framework}
                      </span>
                      <Badge variant={entry.audit_type === 'external' ? 'default' : 'warning'}>
                        {entry.audit_type}
                      </Badge>
                      {entry.is_upcoming && (
                        <Badge variant="danger">
                          <Clock className="w-3 h-3 mr-1" />
                          {entry.days_until_audit} days
                        </Badge>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-slate-400">
                      Audit date: {new Date(entry.audit_date).toLocaleDateString()} |{' '}
                      {entry.days_until_audit > 0
                        ? `${entry.days_until_audit} days remaining`
                        : 'Past due'}
                    </p>
                    {entry.notes && (
                      <p className="text-xs text-gray-500 dark:text-slate-500 mt-1">{entry.notes}</p>
                    )}

                    {/* Forecast */}
                    {forecasts[entry.id] ? (
                      <div className={`mt-3 p-3 rounded-lg border ${getRiskColor(forecasts[entry.id].risk_level)}`}>
                        <p className="text-sm font-medium">
                          Risk Level: {forecasts[entry.id].risk_level.toUpperCase()}
                        </p>
                        <p className="text-xs mt-1">{forecasts[entry.id].recommendation}</p>
                        <p className="text-xs mt-1 opacity-75">
                          {forecasts[entry.id].related_findings_count} related findings |{' '}
                          {forecasts[entry.id].critical_high_count} critical/high
                        </p>
                      </div>
                    ) : (
                      <button
                        onClick={() => loadForecast(entry.id)}
                        disabled={loadingForecast === entry.id}
                        className="mt-2 text-xs text-indigo-600 hover:text-indigo-700 hover:underline"
                      >
                        {loadingForecast === entry.id ? 'Loading forecast...' : 'View Risk Forecast'}
                      </button>
                    )}
                  </div>
                  <button
                    onClick={() => handleDelete(entry.id)}
                    className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                    title="Delete entry"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
