import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  Button,
  EmptyState,
  StatCardSkeleton,
  CardSkeleton,
} from '../components/ui';
import {
  LayoutDashboard,
  Building2,
  ClipboardList,
  FileCheck,
  Plus,
  ArrowRight,
  TrendingUp,
  Clock,
} from 'lucide-react';
import { getOrganizations, getAssessments, ApiRequestError } from '../api';
import type { Organization, Assessment } from '../types';

interface DashboardStats {
  totalOrgs: number;
  totalAssessments: number;
  completedAssessments: number;
  draftAssessments: number;
  averageScore: number | null;
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<DashboardStats>({
    totalOrgs: 0,
    totalAssessments: 0,
    completedAssessments: 0,
    draftAssessments: 0,
    averageScore: null,
  });
  const [recentAssessments, setRecentAssessments] = useState<Assessment[]>([]);
  const [recentOrgs, setRecentOrgs] = useState<Organization[]>([]);

  useEffect(() => {
    async function loadDashboardData() {
      setLoading(true);
      setError(null);
      try {
        const [orgs, assessments] = await Promise.all([
          getOrganizations(),
          getAssessments(),
        ]);

        // Calculate stats
        const completed = assessments.filter((a) => a.status === 'completed');
        const drafts = assessments.filter((a) => a.status !== 'completed');
        const scoresWithValues = completed.filter((a) => a.overall_score != null);
        const avgScore =
          scoresWithValues.length > 0
            ? scoresWithValues.reduce((sum, a) => sum + (a.overall_score ?? 0), 0) /
              scoresWithValues.length
            : null;

        setStats({
          totalOrgs: orgs.length,
          totalAssessments: assessments.length,
          completedAssessments: completed.length,
          draftAssessments: drafts.length,
          averageScore: avgScore,
        });

        // Get recent items (last 5)
        setRecentAssessments(
          assessments
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, 5)
        );
        setRecentOrgs(
          orgs
            .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
            .slice(0, 3)
        );
      } catch (err) {
        setError(
          err instanceof ApiRequestError
            ? err.toDisplayMessage()
            : 'Failed to load dashboard data'
        );
      } finally {
        setLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-gray-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 text-sm">Overview of your security assessments</p>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <StatCardSkeleton key={i} />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <CardSkeleton />
          <CardSkeleton />
        </div>
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

  const hasNoData = stats.totalOrgs === 0 && stats.totalAssessments === 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
            <LayoutDashboard className="w-5 h-5 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
            <p className="text-gray-500 text-sm">Overview of your security assessments</p>
          </div>
        </div>
        <div className="flex gap-3">
          <Link to="/dashboard/org/new">
            <Button variant="outline" className="gap-2">
              <Plus className="w-4 h-4" />
              New Organization
            </Button>
          </Link>
          <Link to="/dashboard/assessment/new">
            <Button className="gap-2">
              <ClipboardList className="w-4 h-4" />
              New Assessment
            </Button>
          </Link>
        </div>
      </div>

      {hasNoData ? (
        <Card>
          <EmptyState
            icon={ClipboardList}
            title="Welcome to ResilAI"
            description="Get started by creating your first organization, then run a security assessment to evaluate your incident readiness."
            action={{
              label: 'Create Organization',
              href: '/dashboard/org/new',
            }}
          />
        </Card>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Building2 className="w-5 h-5 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Organizations</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalOrgs}</p>
                </div>
              </div>
            </Card>

            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                  <ClipboardList className="w-5 h-5 text-purple-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Total Assessments</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalAssessments}</p>
                </div>
              </div>
            </Card>

            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <FileCheck className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Completed</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.completedAssessments}</p>
                </div>
              </div>
            </Card>

            <Card padding="md">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-orange-600" />
                </div>
                <div>
                  <p className="text-sm text-gray-500">Avg. Score</p>
                  <p className="text-2xl font-bold text-gray-900">
                    {stats.averageScore != null ? `${Math.round(stats.averageScore)}%` : '—'}
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Recent Activity */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Recent Assessments */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Clock className="w-5 h-5 text-gray-400" />
                    Recent Assessments
                  </CardTitle>
                  <Link
                    to="/dashboard/assessments"
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    View all <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recentAssessments.length === 0 ? (
                  <p className="text-sm text-gray-500 italic py-4">No assessments yet</p>
                ) : (
                  <div className="space-y-3">
                    {recentAssessments.map((assessment) => (
                      <Link
                        key={assessment.id}
                        to={
                          assessment.status === 'completed'
                            ? `/dashboard/results/${assessment.id}`
                            : `/dashboard/assessment/new?resume=${assessment.id}`
                        }
                        className="block p-3 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="font-medium text-gray-900">{assessment.title}</p>
                            <p className="text-xs text-gray-500">
                              {assessment.organization_name || 'Unknown org'} •{' '}
                              {new Date(assessment.created_at).toLocaleDateString()}
                            </p>
                          </div>
                          <span
                            className={`text-xs px-2 py-1 rounded-full ${
                              assessment.status === 'completed'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {assessment.status === 'completed' ? 'Completed' : 'Draft'}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Organizations */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-gray-400" />
                    Recent Organizations
                  </CardTitle>
                  <Link
                    to="/dashboard/organizations"
                    className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1"
                  >
                    View all <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                {recentOrgs.length === 0 ? (
                  <p className="text-sm text-gray-500 italic py-4">No organizations yet</p>
                ) : (
                  <div className="space-y-3">
                    {recentOrgs.map((org) => (
                      <div
                        key={org.id}
                        className="p-3 rounded-lg border border-gray-100 hover:border-gray-200 hover:bg-gray-50 transition-colors"
                      >
                        <p className="font-medium text-gray-900">{org.name}</p>
                        <p className="text-xs text-gray-500">
                          {org.industry || 'No industry'} •{' '}
                          {new Date(org.created_at).toLocaleDateString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}

