import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { motion } from 'framer-motion';
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
  CalendarPlus,
} from 'lucide-react';
import {
  getOrganizations,
  getAuditCalendar,
  createAuditCalendarEntry,
  deleteAuditCalendarEntry,
  getAuditForecast,
  ApiRequestError,
} from '../api';
import { useIsReadOnly, useDemoMode } from '../contexts';
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
  const { systemStatus } = useDemoMode();
  const isStaging = systemStatus?.environment === 'staging';

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

  // ── ICS file generation (Staging-only Google Calendar sync) ─────────────
  const generateICSFile = (entry: AuditCalendarEntry) => {
    const auditDate = new Date(entry.audit_date);
    const dtStart = auditDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';
    const endDate = new Date(auditDate.getTime() + 60 * 60 * 1000); // 1 hour event
    const dtEnd = endDate.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z';

    const icsContent = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'PRODID:-//ResilAI//AIRS Audit Calendar//EN',
      'CALSCALE:GREGORIAN',
      'METHOD:PUBLISH',
      'BEGIN:VEVENT',
      `DTSTART:${dtStart}`,
      `DTEND:${dtEnd}`,
      `SUMMARY:${entry.framework} Audit (${entry.audit_type})`,
      `DESCRIPTION:Scheduled ${entry.audit_type} audit for ${entry.framework}. Managed by ResilAI AIRS.`,
      'STATUS:CONFIRMED',
      'BEGIN:VALARM',
      'TRIGGER:-P' + (entry.reminder_days_before || 90) + 'D',
      'ACTION:DISPLAY',
      `DESCRIPTION:${entry.framework} audit in ${entry.reminder_days_before || 90} days`,
      'END:VALARM',
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n');

    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `${entry.framework.replace(/\s+/g, '_')}_audit_${entry.audit_date}.ics`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical': return 'text-red-900 dark:text-red-305 bg-red-50/30 dark:bg-red-955/10 border-red-200 dark:border-red-900/50';
      case 'high': return 'text-orange-900 dark:text-orange-305 bg-orange-50/30 dark:bg-orange-955/10 border-orange-200 dark:border-orange-900/50';
      case 'medium': return 'text-yellow-900 dark:text-yellow-305 bg-yellow-50/30 dark:bg-yellow-955/10 border-yellow-250 dark:border-yellow-900/50';
      default: return 'text-green-900 dark:text-green-305 bg-green-50/30 dark:bg-green-955/10 border-green-200 dark:border-green-900/50';
    }
  };

  // Risk-Based Color Bands for days until audit
  const getUrgencyBand = (daysUntil: number) => {
    if (daysUntil < 0) return { 
      bg: 'bg-red-50/30 dark:bg-red-955/10', 
      text: 'text-red-700 dark:text-red-400', 
      textM3: 'text-red-900 dark:text-red-300',
      border: 'border-red-200 dark:border-red-900/50',
      label: 'OVERDUE',
      icon: ShieldAlert
    };
    if (daysUntil <= 14) return { 
      bg: 'bg-red-50/30 dark:bg-red-955/10', 
      text: 'text-red-700 dark:text-red-400', 
      textM3: 'text-red-900 dark:text-red-300',
      border: 'border-red-200 dark:border-red-900/50',
      label: 'Critical',
      icon: AlertTriangle
    };
    if (daysUntil <= 30) return { 
      bg: 'bg-orange-50/30 dark:bg-orange-955/10', 
      text: 'text-orange-700 dark:text-orange-400', 
      textM3: 'text-orange-900 dark:text-orange-300',
      border: 'border-orange-200 dark:border-orange-900/50',
      label: 'Urgent',
      icon: Clock
    };
    if (daysUntil <= 60) return { 
      bg: 'bg-yellow-50/30 dark:bg-yellow-955/10', 
      text: 'text-yellow-700 dark:text-yellow-400', 
      textM3: 'text-yellow-905 dark:text-yellow-300',
      border: 'border-yellow-250 dark:border-yellow-900/50',
      label: 'Upcoming',
      icon: Timer
    };
    return { 
      bg: 'bg-green-50/30 dark:bg-green-955/10', 
      text: 'text-green-700 dark:text-green-400', 
      textM3: 'text-green-900 dark:text-green-300',
      border: 'border-green-200 dark:border-green-900/50',
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

  const getNextCriticalDeadline = () => {
    const upcoming = entries
      .filter(e => e.days_until_audit > 0)
      .sort((a, b) => a.days_until_audit - b.days_until_audit);
    
    if (upcoming.length === 0) return null;
    return upcoming[0];
  };

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
    return (
      <div className="space-y-6">
        <CardSkeleton />
        <CardSkeleton />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className="space-y-6"
    >
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-amber-50/10 dark:bg-amber-955/20 border border-amber-205 dark:border-amber-805/40 rounded-2xl flex items-center justify-center">
            <Calendar className="w-5 h-5 text-amber-600 dark:text-amber-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-150 tracking-tight">
              Audit Calendar
            </h1>
            <p className="text-slate-505 dark:text-slate-455 text-sm font-semibold">
              Track upcoming audits and get pre-audit risk forecasts
            </p>
          </div>
        </div>
        <div className="flex gap-3 items-center">
          <select
            className="rounded-xl border border-slate-205 dark:border-slate-805 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-150 min-w-[220px] focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-bold"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
          >
            {organizations.map((org) => (
              <option key={org.id} value={org.id}>{org.name}</option>
            ))}
          </select>
          {!isReadOnly && (
            <Button onClick={() => setShowAddForm(true)} className="gap-1.5 rounded-xl font-extrabold transition-all duration-205 hover:scale-[1.01]">
              <Plus className="w-4 h-4" /> Schedule Audit
            </Button>
          )}
        </div>
      </div>

      {error && (
        <Card className="rounded-2xl border-red-200 bg-red-50/20 dark:bg-red-955/10 dark:border-red-900/40 shadow-sm">
          <CardContent className="py-3.5">
            <p className="text-sm text-red-700 dark:text-red-400 font-bold">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Audit Health Dashboard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Audit Health Score */}
        <Card padding="md" className={`rounded-3xl border shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md bg-white/60 dark:bg-slate-955/20 ${
          healthScore >= 80 ? 'border-green-200 dark:border-green-900/40' :
          healthScore >= 50 ? 'border-yellow-250 dark:border-yellow-900/40' :
          'border-red-205 dark:border-red-900/40'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
              healthScore >= 80 ? 'bg-green-50/30 dark:bg-green-955/10' :
              healthScore >= 50 ? 'bg-yellow-50/30 dark:bg-yellow-955/10' :
              'bg-red-50/30 dark:bg-red-955/10'
            }`}>
              <TrendingUp className={`w-6 h-6 ${
                healthScore >= 80 ? 'text-green-600 dark:text-green-400' :
                healthScore >= 50 ? 'text-yellow-605 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400'
              }`} />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-455 font-bold uppercase tracking-wider">
                Audit Readiness
              </p>
              <p className={`text-2xl font-extrabold mt-1 ${
                healthScore >= 80 ? 'text-green-605 dark:text-green-400' :
                healthScore >= 50 ? 'text-yellow-605 dark:text-yellow-400' :
                'text-red-600 dark:text-red-400'
              }`}>
                {healthScore}%
              </p>
            </div>
          </div>
          <div className="mt-4 h-1.5 bg-slate-100 dark:bg-slate-800 rounded-full overflow-hidden">
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
        <Card padding="md" className={`rounded-3xl border shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md bg-white/60 dark:bg-slate-955/20 ${
          nextDeadline 
            ? getUrgencyBand(nextDeadline.days_until_audit).border 
            : 'border-slate-200 dark:border-slate-800/40'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
              nextDeadline 
                ? getUrgencyBand(nextDeadline.days_until_audit).bg 
                : 'bg-green-50/30 dark:bg-green-955/10'
            }`}>
              <Timer className={`w-6 h-6 ${
                nextDeadline 
                  ? getUrgencyBand(nextDeadline.days_until_audit).text 
                  : 'text-green-600 dark:text-green-400'
              }`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-slate-500 dark:text-slate-455 font-bold uppercase tracking-wider">
                Next Deadline
              </p>
              {nextDeadline ? (
                <>
                  <p className={`text-2xl font-extrabold mt-0.5 ${getUrgencyBand(nextDeadline.days_until_audit).textM3}`}>
                    {nextDeadline.days_until_audit} days
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400 truncate mt-0.5 font-bold">
                    {nextDeadline.framework}
                  </p>
                </>
              ) : (
                <p className="text-lg font-bold text-green-600 dark:text-green-400 mt-1">No upcoming</p>
              )}
            </div>
          </div>
        </Card>

        {/* Total Audits */}
        <Card padding="md" className="rounded-3xl border border-slate-205 dark:border-slate-805 shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md hover:border-slate-350 dark:hover:border-slate-750 bg-white/60 dark:bg-slate-955/20">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-blue-50/30 dark:bg-blue-955/10 rounded-2xl flex items-center justify-center">
              <Calendar className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-xs text-slate-500 dark:text-slate-455 font-bold uppercase tracking-wider">
                Total Audits
              </p>
              <p className="text-2xl font-extrabold text-slate-900 dark:text-slate-150 mt-1">{entries.length}</p>
            </div>
          </div>
        </Card>

        {/* Likely Risk Area */}
        <Card padding="md" className={`rounded-3xl border shadow-sm transition-all duration-300 hover:scale-[1.005] hover:shadow-md bg-white/60 dark:bg-slate-955/20 ${
          likelyRisk ? 'border-orange-200 dark:border-orange-900/40' : 'border-slate-205 dark:border-slate-805'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${
              likelyRisk ? 'bg-orange-50/30 dark:bg-orange-955/10' : 'bg-slate-50/30 dark:bg-slate-955/10'
            }`}>
              <ShieldAlert className={`w-6 h-6 ${
                likelyRisk ? 'text-orange-600' : 'text-slate-400'
              }`} />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs text-slate-500 dark:text-slate-455 font-bold uppercase tracking-wider">
                Likely Risk Area
              </p>
              {likelyRisk ? (
                <p className="text-sm font-bold text-orange-600 dark:text-orange-400 truncate mt-1">
                  {likelyRisk.recommendation?.split(' ').slice(0, 4).join(' ')}...
                </p>
              ) : (
                <p className="text-sm font-semibold text-slate-400 dark:text-slate-500 mt-1">Run forecasts to identify</p>
              )}
            </div>
          </div>
        </Card>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <Card className="rounded-3xl border border-indigo-200 dark:border-indigo-900/50 bg-white/60 dark:bg-slate-955/20 transition-all duration-300 shadow-md">
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-slate-900 dark:text-slate-150 font-extrabold text-lg">Schedule New Audit</CardTitle>
              <button onClick={() => setShowAddForm(false)} className="p-1 hover:bg-slate-105 dark:hover:bg-slate-800/60 rounded-xl transition-all">
                <X className="w-5 h-5 text-slate-400 hover:text-slate-600" />
              </button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4 pt-2">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-455 uppercase tracking-wider mb-1.5">
                  Framework
                </label>
                <select
                  className="w-full rounded-xl border border-slate-205 dark:border-slate-805 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
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
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-455 uppercase tracking-wider mb-1.5">
                  Audit Date
                </label>
                <input
                  type="date"
                  className="w-full rounded-xl border border-slate-205 dark:border-slate-805 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newEntry.audit_date}
                  onChange={(e) => setNewEntry({ ...newEntry, audit_date: e.target.value })}
                />
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-455 uppercase tracking-wider mb-1.5">
                  Type
                </label>
                <select
                  className="w-full rounded-xl border border-slate-205 dark:border-slate-805 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newEntry.audit_type}
                  onChange={(e) => setNewEntry({ ...newEntry, audit_type: e.target.value as 'external' | 'internal' })}
                >
                  <option value="external">External</option>
                  <option value="internal">Internal</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 dark:text-slate-455 uppercase tracking-wider mb-1.5">
                  Reminder (days before)
                </label>
                <input
                  type="number"
                  min={0}
                  className="w-full rounded-xl border border-slate-205 dark:border-slate-805 px-3.5 py-2.5 text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-150 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 font-semibold"
                  value={newEntry.reminder_days_before ?? ''}
                  onChange={(e) => {
                    const raw = e.target.value;
                    setNewEntry({
                      ...newEntry,
                      reminder_days_before: raw === '' ? undefined : Math.max(0, parseInt(raw, 10) || 0),
                    });
                  }}
                  placeholder="90"
                />
              </div>
            </div>
            <div className="pt-2">
              <Button onClick={handleAdd} disabled={!newEntry.framework || !newEntry.audit_date} className="rounded-xl font-extrabold transition-all duration-205 hover:scale-[1.01]">
                Schedule Audit
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Entries */}
      {loading ? (
        <CardSkeleton />
      ) : entries.length === 0 ? (
        <Card className="rounded-3xl border border-slate-200 dark:border-slate-850/60 shadow-sm bg-white/60 dark:bg-slate-955/20">
          <CardContent className="py-20 text-center">
            <Calendar className="w-16 h-16 text-slate-300 dark:text-slate-700 mx-auto mb-4 opacity-80" />
            <p className="text-slate-505 dark:text-slate-455 font-bold text-lg">
              No audits scheduled. Click &quot;Schedule Audit&quot; to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4">
          {entries.map((entry) => {
            const urgency = getUrgencyBand(entry.days_until_audit);
            const UrgencyIcon = urgency.icon;
            const displayColorClass = urgency.textM3 || urgency.text;
            
            return (
              <Card 
                key={entry.id} 
                className={`${urgency.border} ${urgency.bg} transition-all duration-300 hover:scale-[1.005] hover:shadow-md rounded-3xl border shadow-sm`}
              >
                <CardContent className="p-6">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-3 flex-wrap">
                        {/* Risk band indicator */}
                        <div className={`px-2.5 py-1 rounded-xl text-xs font-bold ${urgency.bg} ${displayColorClass} border ${urgency.border} flex items-center gap-1.5 shadow-sm`}>
                          <UrgencyIcon className="w-3.5 h-3.5" />
                          {urgency.label}
                        </div>
                        <span className="text-lg font-extrabold text-slate-900 dark:text-slate-155">
                          {entry.framework}
                        </span>
                        <Badge variant={entry.audit_type === 'external' ? 'default' : 'warning'} className="font-extrabold text-xs rounded-lg px-2.5 py-0.5">
                          {entry.audit_type}
                        </Badge>
                      </div>

                      {/* Days countdown with prominent display */}
                      <div className="flex items-center gap-4 mb-2.5">
                        <div className={`text-2xl font-extrabold ${displayColorClass}`}>
                          {entry.days_until_audit > 0 
                            ? `${entry.days_until_audit} days` 
                            : entry.days_until_audit === 0 
                              ? 'Today!' 
                              : `${Math.abs(entry.days_until_audit)} days overdue`}
                        </div>
                        <span className="text-sm font-bold text-slate-500 dark:text-slate-400">
                          {new Date(entry.audit_date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short', 
                            day: 'numeric',
                            year: 'numeric'
                          })}
                        </span>
                      </div>

                      {entry.notes && (
                        <p className="text-xs text-slate-500 dark:text-slate-450 mt-1.5 leading-relaxed font-semibold">{entry.notes}</p>
                      )}

                      {/* Forecast */}
                      {forecasts[entry.id] ? (
                        <div className={`mt-3.5 p-4 rounded-2xl border ${getRiskColor(forecasts[entry.id].risk_level)} shadow-sm transition-all duration-200`}>
                          <p className="text-sm font-extrabold">
                            Risk Level: {forecasts[entry.id].risk_level.toUpperCase()}
                          </p>
                          <p className="text-xs mt-1.5 leading-relaxed font-semibold">{forecasts[entry.id].recommendation}</p>
                          <p className="text-[11px] mt-2 font-bold opacity-80">
                            {forecasts[entry.id].related_findings_count} related findings |{' '}
                            {forecasts[entry.id].critical_high_count} critical/high
                          </p>
                        </div>
                      ) : (
                        <button
                          onClick={() => loadForecast(entry.id)}
                          disabled={loadingForecast === entry.id}
                          className="mt-3 text-xs font-bold text-indigo-650 hover:text-indigo-800 dark:text-indigo-400 dark:hover:text-indigo-305 hover:underline flex items-center gap-1 transition-all"
                        >
                          {loadingForecast === entry.id ? 'Loading forecast...' : 'View Risk Forecast'}
                        </button>
                      )}

                      {/* Staging-only: Sync to Google Calendar via ICS */}
                      {isStaging && (
                        <button
                          onClick={() => generateICSFile(entry)}
                          className="mt-3 ml-3 inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-bold rounded-xl bg-blue-50/40 dark:bg-blue-955/20 text-blue-700 dark:text-blue-300 border border-blue-200 dark:border-blue-900/60 hover:bg-blue-100 dark:hover:bg-blue-900/60 transition-all duration-200 hover:scale-[1.01]"
                          title="Download .ics file to add this audit to Google Calendar, Outlook, or Apple Calendar"
                        >
                          <CalendarPlus className="w-3.5 h-3.5 text-blue-600 dark:text-blue-400" />
                          Sync to Google Calendar
                        </button>
                      )}
                    </div>
                    {!isReadOnly && (
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="p-2 text-slate-400 hover:text-red-500 hover:bg-slate-100 dark:hover:bg-slate-800/60 rounded-xl transition-all"
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
    </motion.div>
  );
}
