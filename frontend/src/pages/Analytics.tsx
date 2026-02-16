import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { BarChart3, TrendingUp, AlertTriangle, ArrowRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, Button, ListSkeleton } from '../components/ui';
import { getAssessments, ApiRequestError } from '../api';
import type { Assessment } from '../types';

function getReadinessLevel(score: number): string {
  if (score <= 40) return 'Critical';
  if (score <= 60) return 'At Risk';
  if (score <= 80) return 'Managed';
  return 'Resilient';
}

export default function AnalyticsPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);

  useEffect(() => {
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAssessments();
        setAssessments(data);
      } catch (err) {
        setError(err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to load analytics');
      } finally {
        setLoading(false);
      }
    };

    run();
  }, []);

  const completed = useMemo(
    () => assessments
      .filter((assessment) => assessment.status === 'completed' && assessment.overall_score != null)
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()),
    [assessments]
  );

  const latest = completed[0] || null;
  const previous = completed[1] || null;
  const averageScore = completed.length > 0
    ? completed.reduce((sum, assessment) => sum + (assessment.overall_score || 0), 0) / completed.length
    : null;
  const scoreDelta = latest && previous
    ? (latest.overall_score || 0) - (previous.overall_score || 0)
    : null;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <BarChart3 className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
            <p className="text-gray-500 dark:text-gray-400 text-sm">Portfolio risk trend and readiness summary</p>
          </div>
        </div>
        <ListSkeleton count={4} />
      </div>
    );
  }

  if (error) {
    return (
      <Card className="max-w-lg mx-auto mt-12">
        <CardContent className="py-8 text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Analytics</h1>
          <p className="text-gray-500 dark:text-gray-400 text-sm">Decision-focused readiness and risk movement</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Assessments Completed</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">{completed.length}</p>
        </Card>

        <Card padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Portfolio Readiness</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
            {averageScore == null ? 'N/A' : `${Math.round(averageScore)}%`}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {averageScore == null ? 'No completed assessments yet' : getReadinessLevel(Math.round(averageScore))}
          </p>
        </Card>

        <Card padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Latest Score</p>
          <p className="mt-1 text-2xl font-bold text-gray-900 dark:text-gray-100">
            {latest?.overall_score == null ? 'N/A' : `${Math.round(latest.overall_score)}%`}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {latest?.overall_score == null ? 'No recent run' : getReadinessLevel(Math.round(latest.overall_score))}
          </p>
        </Card>

        <Card padding="md">
          <p className="text-sm text-gray-500 dark:text-gray-400">Risk Trend</p>
          <p className={`mt-1 text-2xl font-bold ${scoreDelta != null && scoreDelta >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {scoreDelta == null ? 'N/A' : `${scoreDelta >= 0 ? '+' : '-'}${Math.abs(Math.round(scoreDelta))}`}
          </p>
          <p className="text-sm text-gray-600 dark:text-gray-300">
            {scoreDelta == null ? 'Need at least two runs' : scoreDelta >= 0 ? 'Improving posture' : 'Deteriorating posture'}
          </p>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Latest Assessment Results
          </CardTitle>
        </CardHeader>
        <CardContent>
          {completed.length === 0 ? (
            <div className="text-center py-8">
              <AlertTriangle className="w-10 h-10 text-gray-400 mx-auto mb-3" />
              <p className="text-gray-600 dark:text-gray-300 mb-4">Run your first assessment to populate analytics insights.</p>
              <Link to="/dashboard/assessment/new">
                <Button>Start Assessment</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-3">
              {completed.slice(0, 6).map((assessment) => (
                <Link
                  key={assessment.id}
                  to={`/dashboard/results/${assessment.id}`}
                  className="flex items-center justify-between p-3 rounded-lg border border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
                >
                  <div>
                    <p className="font-medium text-gray-900 dark:text-gray-100">{assessment.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {assessment.organization_name || 'Organization'} | {new Date(assessment.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">{Math.round(assessment.overall_score || 0)}%</p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">{getReadinessLevel(Math.round(assessment.overall_score || 0))}</p>
                    </div>
                    <ArrowRight className="w-4 h-4 text-gray-400" />
                  </div>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
