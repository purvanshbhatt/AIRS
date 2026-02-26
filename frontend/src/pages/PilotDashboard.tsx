import { useEffect, useState, useMemo } from 'react';
import {
  getOrganizations,
  activatePilot,
  getPilotStatus,
  completePilotMilestone,
  resetPilotMilestone,
  getPilotConfidence,
} from '../api';
import type { PilotProgram, PilotMilestone, ConfidenceBreakdown } from '../api';
import type { Organization } from '../types';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  Badge,
  Select,
} from '../components/ui';
import {
  Rocket,
  CheckCircle2,
  Circle,
  Timer,
  ShieldCheck,
  BarChart3,
  Target,
} from 'lucide-react';

const CATEGORY_LABELS: Record<string, string> = {
  foundation: 'Foundation',
  assessment: 'Assessment',
  integration: 'Integration',
  remediation: 'Remediation',
  reporting: 'Reporting',
  audit: 'Audit',
  team: 'Team',
};

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-600 dark:text-green-400',
  B: 'text-blue-600 dark:text-blue-400',
  C: 'text-amber-600 dark:text-amber-400',
  D: 'text-orange-600 dark:text-orange-400',
  F: 'text-red-600 dark:text-red-400',
};

export default function PilotDashboard() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrgId, setSelectedOrgId] = useState('');
  const [pilot, setPilot] = useState<PilotProgram | null>(null);
  const [confidence, setConfidence] = useState<ConfidenceBreakdown | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const selectedOrgName = useMemo(
    () => organizations.find((o) => o.id === selectedOrgId)?.name || 'Organization',
    [organizations, selectedOrgId]
  );

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        const orgs = await getOrganizations();
        setOrganizations(orgs);
        if (orgs.length > 0) setSelectedOrgId(orgs[0].id);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load organizations');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  useEffect(() => {
    if (!selectedOrgId) return;
    const run = async () => {
      try {
        const [status, conf] = await Promise.all([
          getPilotStatus(selectedOrgId),
          getPilotConfidence(selectedOrgId),
        ]);
        setPilot(status);
        setConfidence(conf);
      } catch {
        setPilot(null);
        setConfidence(null);
      }
    };
    run();
  }, [selectedOrgId]);

  const handleActivate = async () => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const result = await activatePilot(selectedOrgId);
      setPilot(result);
      setNotice('30-day Readiness Sprint activated!');
      const conf = await getPilotConfidence(selectedOrgId);
      setConfidence(conf);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to activate pilot');
    } finally {
      setBusy(false);
    }
  };

  const handleToggleMilestone = async (milestone: PilotMilestone) => {
    if (!selectedOrgId) return;
    setBusy(true);
    setError('');
    try {
      let result: PilotProgram;
      if (milestone.status === 'completed') {
        result = await resetPilotMilestone(selectedOrgId, milestone.id);
      } else {
        result = await completePilotMilestone(selectedOrgId, milestone.id);
      }
      setPilot(result);
      const conf = await getPilotConfidence(selectedOrgId);
      setConfidence(conf);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update milestone');
    } finally {
      setBusy(false);
    }
  };

  if (loading) {
    return <div className="text-sm text-gray-500 dark:text-slate-400">Loading...</div>;
  }

  const completedCount = pilot?.milestones?.filter((m) => m.status === 'completed').length ?? 0;
  const totalCount = pilot?.milestones?.length ?? 0;
  const progressPercent = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-purple-50 dark:bg-purple-900/30 flex items-center justify-center">
          <Rocket className="h-5 w-5 text-purple-600 dark:text-purple-300" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Pilot Program</h1>
          <p className="text-sm text-gray-500 dark:text-slate-400">
            30-Day Readiness Sprint — Pre-Audit Confidence Score
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Organization</CardTitle>
          <CardDescription>Select the organization for this pilot sprint.</CardDescription>
        </CardHeader>
        <CardContent>
          <Select
            label="Organization"
            value={selectedOrgId}
            onChange={(e) => setSelectedOrgId(e.target.value)}
            options={organizations.map((o) => ({ value: o.id, label: o.name }))}
          />
        </CardContent>
      </Card>

      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded text-sm text-red-700 dark:text-red-300">{error}</div>
      )}
      {notice && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded text-sm text-green-700 dark:text-green-300">{notice}</div>
      )}

      {(!pilot || pilot.status === 'not_started') && (
        <Card className="border-purple-200 dark:border-purple-800">
          <CardContent className="py-8 text-center space-y-4">
            <Target className="h-12 w-12 mx-auto text-purple-500" />
            <h2 className="text-xl font-bold text-gray-900 dark:text-slate-100">Start Your 30-Day Readiness Sprint</h2>
            <p className="text-sm text-gray-600 dark:text-slate-300 max-w-lg mx-auto">
              Activate a guided 30-day program that prepares <strong>{selectedOrgName}</strong> for audit readiness.
              Track milestones, measure progress, and generate a Pre-Audit Confidence Score.
            </p>
            <Button onClick={handleActivate} disabled={busy || !selectedOrgId}>
              <Rocket className="w-4 h-4 mr-2" />
              Activate Readiness Sprint
            </Button>
          </CardContent>
        </Card>
      )}

      {pilot && pilot.status !== 'not_started' && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="py-4 text-center">
                <div className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">Confidence Score</div>
                <div className={`text-3xl font-bold mt-1 ${GRADE_COLORS[pilot.confidence_grade] || ''}`}>
                  {pilot.confidence_score}%
                </div>
                <div className={`text-lg font-semibold ${GRADE_COLORS[pilot.confidence_grade] || ''}`}>
                  Grade {pilot.confidence_grade}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-4 text-center">
                <div className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">Progress</div>
                <div className="text-3xl font-bold mt-1 text-gray-900 dark:text-slate-100">
                  {completedCount}/{totalCount}
                </div>
                <div className="text-sm text-gray-500 dark:text-slate-400">Milestones</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-4 text-center">
                <div className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">Days Remaining</div>
                <div className="text-3xl font-bold mt-1 text-gray-900 dark:text-slate-100">
                  {pilot.days_remaining}
                </div>
                <div className="text-sm text-gray-500 dark:text-slate-400">of 30 days</div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="py-4 text-center">
                <div className="text-xs text-gray-500 dark:text-slate-400 uppercase tracking-wide">Status</div>
                <div className="mt-2">
                  <Badge variant={pilot.status === 'active' ? 'default' : 'outline'}>
                    {pilot.status === 'active' ? 'Active' : pilot.status === 'completed' ? 'Completed' : 'Cancelled'}
                  </Badge>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Progress Bar */}
          <Card>
            <CardContent className="py-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium text-gray-700 dark:text-slate-300">Sprint Progress</span>
                <span className="text-sm text-gray-500 dark:text-slate-400">{progressPercent}%</span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3">
                <div
                  className="bg-purple-600 dark:bg-purple-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </CardContent>
          </Card>

          {/* Milestones */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-gray-500" />
                Readiness Milestones
              </CardTitle>
              <CardDescription>Complete each milestone to increase your Pre-Audit Confidence Score.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-2">
              {pilot.milestones.map((milestone) => (
                <div
                  key={milestone.id}
                  className={`flex items-start gap-3 p-3 rounded-lg border transition-colors ${
                    milestone.status === 'completed'
                      ? 'border-green-200 dark:border-green-800 bg-green-50 dark:bg-green-900/20'
                      : 'border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900'
                  }`}
                >
                  <button
                    onClick={() => handleToggleMilestone(milestone)}
                    disabled={busy}
                    className="mt-0.5 flex-shrink-0"
                  >
                    {milestone.status === 'completed' ? (
                      <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400" />
                    ) : (
                      <Circle className="w-5 h-5 text-gray-300 dark:text-slate-600" />
                    )}
                  </button>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className={`text-sm font-medium ${
                        milestone.status === 'completed'
                          ? 'text-green-800 dark:text-green-200 line-through'
                          : 'text-gray-900 dark:text-slate-100'
                      }`}>
                        {milestone.title}
                      </span>
                      <Badge variant="outline" className="text-xs">
                        {CATEGORY_LABELS[milestone.category] || milestone.category}
                      </Badge>
                      <span className="text-xs text-gray-400 dark:text-slate-500">Day {milestone.day_target}</span>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-slate-400 mt-0.5">{milestone.description}</p>
                    {milestone.completed_at && (
                      <p className="text-xs text-green-600 dark:text-green-400 mt-0.5">
                        Completed {new Date(milestone.completed_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                  <div className="text-xs text-gray-400 dark:text-slate-500 flex-shrink-0">
                    +{milestone.weight}%
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Confidence Breakdown by Category */}
          {confidence && confidence.categories && Object.keys(confidence.categories).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <ShieldCheck className="h-5 w-5 text-gray-500" />
                  Confidence Breakdown
                </CardTitle>
                <CardDescription>Pre-Audit Confidence Score by governance category.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {Object.entries(confidence.categories).map(([cat, data]) => (
                    <div key={cat} className="p-3 border border-gray-200 dark:border-slate-700 rounded-lg">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-900 dark:text-slate-100">
                          {CATEGORY_LABELS[cat] || cat}
                        </span>
                        <span className={`text-sm font-bold ${
                          data.score >= 75 ? 'text-green-600 dark:text-green-400' :
                          data.score >= 50 ? 'text-amber-600 dark:text-amber-400' :
                          'text-red-600 dark:text-red-400'
                        }`}>
                          {data.score}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-1.5 mt-2">
                        <div
                          className={`h-1.5 rounded-full ${
                            data.score >= 75 ? 'bg-green-500' :
                            data.score >= 50 ? 'bg-amber-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${data.score}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  );
}
