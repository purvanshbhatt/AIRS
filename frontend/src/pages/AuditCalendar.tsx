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
  TrendingUp,
  ShieldAlert,
  Timer,
} from 'lucide-react';
import {
  getOrganizations,
  getAuditCalendar,
  createAuditCalendarEntry,
  deleteAuditCalendarEntry,
  getAuditForecast,
  ApiRequestError,
} from '../api';
import { useIsReadOnly } from '../contexts';
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
  const isReadOnly = useIsReadOnly();

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

  // Risk-Based Color Bands for days until audit
  const getUrgencyBand = (daysUntil: number) => {
    if (daysUntil < 0) return { 
      bg: 'bg-red-500', 
      text: 'text-white', 
      border: 'border-red-600',
      label: 'OVERDUE',
      icon: ShieldAlert
    };
    if (daysUntil <= 14) return { 
      bg: 'bg-red-100 dark:bg-red-900/30', 
      text: 'text-red-700 dark:text-red-400', 
      border: 'border-red-300 dark:border-red-700',
      label: 'Critical',
      icon: AlertTriangle
    };
    if (daysUntil <= 30) return { 
      bg: 'bg-orange-100 dark:bg-orange-900/30', 
      text: 'text-orange-700 dark:text-orange-400', 
      border: 'border-orange-300 dark:border-orange-700',
      label: 'Urgent',
      icon: Clock
    };
    if (daysUntil <= 60) return { 
      bg: 'bg-yellow-100 dark:bg-yellow-900/30', 
      text: 'text-yellow-700 dark:text-yellow-400', 
      border: 'border-yellow-300 dark:border-yellow-700',
      label: 'Upcoming',
      icon: Timer
    };
    return { 
      bg: 'bg-green-100 dark:bg-green-900/30', 
      text: 'text-green-700 dark:text-green-400', 
      border: 'border-green-300 dark:border-green-700',
      label: 'Healthy',
      icon: CheckCircle
    };
  };

  // Calculate Audit Health Score (0-100)
  const calculateHealthScore = () => {
    if (entries.length === 0) return 100;
    
    const scores = entries.map(e => {
      const days = e.days_until_audit;
      if (days < 0) return 0;  // Overdue = critical
      if (days <= 14) return 20;
      if (days <= 30) return 50;
      if (days <= 60) return 75;
      return 100;
    });
    
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  // Find next critical deadline
  const getNextCriticalDeadline = () => {
    const upcoming = entries
      .filter(e => e.days_until_audit > 0)
      .sort((a, b) => a.days_until_audit - b.days_until_audit);
    
    if (upcoming.length === 0) return null;
    return upcoming[0];
  };

  // Get likely risk area based on forecasts
  const getLikelyRiskArea = () => {
    const forecastList = Object.values(forecasts);
    const criticalForecasts = forecastList.filter(f => 
      f.risk_level === 'critical' || f.risk_level === 'high'
    );
    if (criticalForecasts.length === 0) return null;
    return criticalForecasts[0];
  };

  const healthScore = calculateHealthScore();
  const nextDeadline = getNextCriticalDeadline();
  const likelyRisk = getLikelyRiskArea();

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
          {!isReadOnly && (
            <Button onClick={() => setShowAddForm(true)} className="gap-2">
              <Plus className="w-4 h-4" /> Schedule Audit
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Card className="border-red-200 bg-red-50 dark:bg-red-900/20">
          <CardContent className="py-3">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Audit Health Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Audit Health Score */}
        <Card padding="md" className={`border-2 ${
          healthScore >= 80 ? 'border-green-200 dark:border-green-800' :
          healthScore >= 50 ? 'border-yellow-200 dark:border-yellow-800' :
          'border-red-200 dark:border-red-800'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              healthScore >= 80 ? 'bg-green-100 dark:bg-green-900/30' :
              healthScore >= 50 ? 'bg-yellow-100 dark:bg-yellow-900/30' :
              'bg-red-100 dark:bg-red-900/30'
            }`}>
              <TrendingUp className={`w-6 h-6 ${
                healthScore >= 80 ? 'text-green-600' :
                healthScore >= 50 ? 'text-yellow-600' :
                'text-red-600'
              }`} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400 font-medium uppercase tracking-wide">
                Audit Readiness
              </p>
              <p className={`text-2xl font-bold ${
                healthScore >= 80 ? 'text-green-600' :
                healthScore >= 50 ? 'text-yellow-600' :
                'text-red-600'
              }`}>
                {healthScore}%
              </p>
            </div>
          </div>
          <div className="mt-3 h-1.5 bg-gray-100 dark:bg-gray-800 rounded-full overflow-hidden">
            <div 
              className={`h-full rounded-full transition-all duration-500 ${
                healthScore >= 80 ? 'bg-green-500' :
                healthScore >= 50 ? 'bg-yellow-500' :
                'bg-red-500'
              }`}
              style={{ width: `${healthScore}%` }}
            />
          </div>
        </Card>

        {/* Next Critical Deadline */}
        <Card padding="md" className={`border-2 ${
          nextDeadline 
            ? getUrgencyBand(nextDeadline.days_until_audit).border 
            : 'border-green-200 dark:border-green-800'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              nextDeadline 
                ? getUrgencyBand(nextDeadline.days_until_audit).bg 
                : 'bg-green-100 dark:bg-green-900/30'
            }`}>
              <Timer className={`w-6 h-6 ${
                nextDeadline 
                  ? getUrgencyBand(nextDeadline.days_until_audit).text 
                  : 'text-green-600'
              }`} />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400 font-medium uppercase tracking-wide">
                Next Critical Deadline
              </p>
              {nextDeadline ? (
                <>
                  <p className={`text-lg font-bold ${getUrgencyBand(nextDeadline.days_until_audit).text}`}>
                    {nextDeadline.days_until_audit} days
                  </p>
                  <p className="text-xs text-gray-500 dark:text-slate-400 truncate max-w-[150px]">
                    {nextDeadline.framework}
                  </p>
                </>
              ) : (
                <p className="text-lg font-bold text-green-600">No upcoming</p>
              )}
            </div>
          </div>
        </Card>

        {/* Total Audits */}
        <Card padding="md">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
              <Calendar className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-xs text-gray-500 dark:text-slate-400 font-medium uppercase tracking-wide">
                Total Audits
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-slate-100">{entries.length}</p>
            </div>
          </div>
        </Card>

        {/* Likely Risk Area */}
        <Card padding="md" className={likelyRisk ? 'border-2 border-orange-200 dark:border-orange-800' : ''}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${
              likelyRisk ? 'bg-orange-100 dark:bg-orange-900/30' : 'bg-gray-100 dark:bg-gray-800'
            }`}>
              <ShieldAlert className={`w-6 h-6 ${
                likelyRisk ? 'text-orange-600' : 'text-gray-400'
              }`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-gray-500 dark:text-slate-400 font-medium uppercase tracking-wide">
                Likely Risk Area
              </p>
              {likelyRisk ? (
                <p className="text-sm font-medium text-orange-600 dark:text-orange-400 truncate">
                  {likelyRisk.recommendation?.split(' ').slice(0, 4).join(' ')}...
                </p>
              ) : (
                <p className="text-sm text-gray-400 dark:text-slate-500">Run forecasts to identify</p>
              )}
            </div>
          </div>
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
          {entries.map((entry) => {
            const urgency = getUrgencyBand(entry.days_until_audit);
            const UrgencyIcon = urgency.icon;
            
            return (
              <Card 
                key={entry.id} 
                className={`${urgency.border} ${urgency.bg} transition-all duration-300`}
              >
                <CardContent className="py-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        {/* Risk band indicator */}
                        <div className={`px-2 py-1 rounded-md text-xs font-bold ${urgency.bg} ${urgency.text} border ${urgency.border} flex items-center gap-1`}>
                          <UrgencyIcon className="w-3 h-3" />
                          {urgency.label}
                        </div>
                        <span className="text-lg font-semibold text-gray-900 dark:text-slate-100">
                          {entry.framework}
                        </span>
                        <Badge variant={entry.audit_type === 'external' ? 'default' : 'warning'}>
                          {entry.audit_type}
                        </Badge>
                      </div>

                      {/* Days countdown with prominent display */}
                      <div className="flex items-center gap-4 mb-2">
                        <div className={`text-2xl font-bold ${urgency.text}`}>
                          {entry.days_until_audit > 0 
                            ? `${entry.days_until_audit} days` 
                            : entry.days_until_audit === 0 
                              ? 'Today!' 
                              : `${Math.abs(entry.days_until_audit)} days overdue`}
                        </div>
                        <span className="text-sm text-gray-500 dark:text-slate-400">
                          {new Date(entry.audit_date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short', 
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                      </div>

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
                    {!isReadOnly && (
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                        title="Delete entry"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
