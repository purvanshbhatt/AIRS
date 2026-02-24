import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
  EmptyState,
  ListSkeleton,
} from '../components/ui';
import {
  Building2,
  Plus,
  Search,
  ClipboardList,
  ChevronRight,
} from 'lucide-react';
import { getOrganizations, getAssessments, ApiRequestError } from '../api';
import type { Organization, Assessment } from '../types';

export default function Organizations() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [assessmentsByOrg, setAssessmentsByOrg] = useState<Record<string, Assessment[]>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const [orgs, assessments] = await Promise.all([
          getOrganizations(),
          getAssessments(),
        ]);

        // Sort by most recent
        orgs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setOrganizations(orgs);

        // Group assessments by organization
        const byOrg: Record<string, Assessment[]> = {};
        for (const assessment of assessments) {
          if (!byOrg[assessment.organization_id]) {
            byOrg[assessment.organization_id] = [];
          }
          byOrg[assessment.organization_id].push(assessment);
        }
        setAssessmentsByOrg(byOrg);
      } catch (err) {
        setError(
          err instanceof ApiRequestError
            ? err.toDisplayMessage()
            : 'Failed to load organizations'
        );
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  const filteredOrgs = organizations.filter(
    (org) =>
      org.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      org.industry?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gray-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
            <Building2 className="w-5 h-5 text-gray-600 dark:text-slate-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Organizations</h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">Manage your organizations</p>
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
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
            <Building2 className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Organizations</h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">
              {organizations.length} organization{organizations.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        <Link to="/dashboard/org/new">
          <Button className="gap-2">
            <Plus className="w-4 h-4" />
            New Organization
          </Button>
        </Link>
      </div>

      {organizations.length === 0 ? (
        <Card>
          <EmptyState
            icon={Building2}
            title="No organizations yet"
            description="Create your first organization to start running security assessments."
            action={{
              label: 'Create Organization',
              href: '/dashboard/org/new',
            }}
          />
        </Card>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Organization List */}
          <div className="lg:col-span-1 space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search organizations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Org cards */}
            <div className="space-y-2">
              {filteredOrgs.map((org) => {
                const orgAssessments = assessmentsByOrg[org.id] || [];
                const isSelected = selectedOrg?.id === org.id;
                return (
                  <button
                    key={org.id}
                    onClick={() => setSelectedOrg(org)}
                    className={`w-full text-left p-4 rounded-lg border transition-colors ${
                      isSelected
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                        : 'border-gray-200 dark:border-slate-700 hover:border-gray-300 dark:hover:border-slate-600 bg-white dark:bg-slate-900'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-gray-900 dark:text-slate-100">{org.name}</p>
                        <p className="text-xs text-gray-500 dark:text-slate-400">
                          {org.industry || 'No industry'} • {org.size || 'Size not set'}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-gray-100 dark:bg-slate-800 text-gray-600 dark:text-slate-300 px-2 py-1 rounded">
                          {orgAssessments.length} assessment{orgAssessments.length !== 1 ? 's' : ''}
                        </span>
                        <ChevronRight className="w-4 h-4 text-gray-400 dark:text-slate-500" />
                      </div>
                    </div>
                  </button>
                );
              })}

              {filteredOrgs.length === 0 && (
                <p className="text-sm text-gray-500 dark:text-slate-400 text-center py-4">
                  No organizations match your search
                </p>
              )}
            </div>
          </div>

          {/* Organization Detail Panel */}
          <div className="lg:col-span-2">
            {selectedOrg ? (
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-xl">{selectedOrg.name}</CardTitle>
                      <CardDescription>
                        {selectedOrg.industry || 'No industry'} •{' '}
                        {selectedOrg.size || 'Size not set'} • Created{' '}
                        {new Date(selectedOrg.created_at).toLocaleDateString()}
                      </CardDescription>
                    </div>
                    <Link to={`/dashboard/assessment/new?org=${selectedOrg.id}`}>
                      <Button size="sm" className="gap-2">
                        <ClipboardList className="w-4 h-4" />
                        New Assessment
                      </Button>
                    </Link>
                  </div>
                </CardHeader>
                <CardContent>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-slate-300 mb-3">Assessment History</h4>
                  {(assessmentsByOrg[selectedOrg.id] || []).length === 0 ? (
                    <p className="text-sm text-gray-500 dark:text-slate-400 italic py-4">
                      No assessments yet for this organization
                    </p>
                  ) : (
                    <div className="space-y-2">
                      {(assessmentsByOrg[selectedOrg.id] || [])
                        .sort(
                          (a, b) =>
                            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
                        )
                        .map((assessment) => (
                          <Link
                            key={assessment.id}
                            to={
                              assessment.status === 'completed'
                                ? `/dashboard/results/${assessment.id}`
                                : `/dashboard/assessment/new?resume=${assessment.id}`
                            }
                            className="block p-3 rounded-lg border border-gray-100 dark:border-slate-800 hover:border-gray-200 dark:hover:border-slate-700 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <p className="font-medium text-gray-900 dark:text-slate-100">{assessment.title}</p>
                                <p className="text-xs text-gray-500 dark:text-slate-400">
                                  {new Date(assessment.created_at).toLocaleDateString()}
                                  {assessment.overall_score != null && (
                                    <> • Score: {Math.round(assessment.overall_score)}%</>
                                  )}
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
            ) : (
              <Card className="h-full flex items-center justify-center">
                <EmptyState
                  icon={Building2}
                  title="Select an organization"
                  description="Click on an organization to view its details and assessment history"
                />
              </Card>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
