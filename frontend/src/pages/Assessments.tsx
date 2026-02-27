import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Card,
  CardContent,
  Button,
  EmptyState,
  ListSkeleton,
} from '../components/ui';
import {
  ClipboardList,
  Plus,
  Search,
  Filter,
  FileCheck,
  Clock,
  ChevronRight,
} from 'lucide-react';
import { getAssessments, ApiRequestError } from '../api';
import { useIsReadOnly } from '../contexts';
import type { Assessment } from '../types';

type StatusFilter = 'all' | 'completed' | 'draft';

export default function Assessments() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [assessments, setAssessments] = useState<Assessment[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const isReadOnly = useIsReadOnly();

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      try {
        const data = await getAssessments();
        // Sort by most recent
        data.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
        setAssessments(data);
      } catch (err) {
        setError(
          err instanceof ApiRequestError
            ? err.toDisplayMessage()
            : 'Failed to load assessments'
        );
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, []);

  // Filter assessments
  const filteredAssessments = assessments.filter((a) => {
    // Status filter
    if (statusFilter === 'completed' && a.status !== 'completed') return false;
    if (statusFilter === 'draft' && a.status === 'completed') return false;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        a.title.toLowerCase().includes(query) ||
        a.organization_name?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const completedCount = assessments.filter((a) => a.status === 'completed').length;
  const draftCount = assessments.filter((a) => a.status !== 'completed').length;

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gray-100 dark:bg-slate-800 rounded-lg flex items-center justify-center">
            <ClipboardList className="w-5 h-5 text-gray-600 dark:text-slate-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Assessments</h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">Manage your security assessments</p>
          </div>
        </div>
        <ListSkeleton count={5} />
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
          <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
            <ClipboardList className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-slate-100">Assessments</h1>
            <p className="text-gray-500 dark:text-slate-400 text-sm">
              {assessments.length} assessment{assessments.length !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
        {!isReadOnly && (
          <Link to="/dashboard/assessment/new">
            <Button className="gap-2">
              <Plus className="w-4 h-4" />
              New Assessment
            </Button>
          </Link>
        )}
      </div>

      {assessments.length === 0 ? (
        <Card>
          <EmptyState
            icon={ClipboardList}
            title="No assessments yet"
            description={isReadOnly 
              ? "This demo environment contains synthetic example data."
              : "Run your first assessment to generate a readiness score."
            }
            action={isReadOnly ? undefined : {
              label: 'Start Assessment',
              href: '/dashboard/assessment/new',
            }}
          />
        </Card>
      ) : (
        <>
          {/* Filters */}
          <div className="flex flex-col md:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search by title or organization..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-slate-700 rounded-lg text-sm bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-gray-400" />
              <div className="flex bg-gray-100 dark:bg-slate-800 rounded-lg p-1">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                    statusFilter === 'all'
                      ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 shadow-sm'
                      : 'text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-slate-100'
                  }`}
                >
                  All ({assessments.length})
                </button>
                <button
                  onClick={() => setStatusFilter('completed')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1.5 ${
                    statusFilter === 'completed'
                      ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 shadow-sm'
                      : 'text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-slate-100'
                  }`}
                >
                  <FileCheck className="w-3.5 h-3.5" />
                  Completed ({completedCount})
                </button>
                <button
                  onClick={() => setStatusFilter('draft')}
                  className={`px-3 py-1.5 text-sm rounded-md transition-colors flex items-center gap-1.5 ${
                    statusFilter === 'draft'
                      ? 'bg-white dark:bg-slate-900 text-gray-900 dark:text-slate-100 shadow-sm'
                      : 'text-gray-600 dark:text-slate-300 hover:text-gray-900 dark:hover:text-slate-100'
                  }`}
                >
                  <Clock className="w-3.5 h-3.5" />
                  Drafts ({draftCount})
                </button>
              </div>
            </div>
          </div>

          {/* Assessment List */}
          <div className="space-y-3">
            {filteredAssessments.length === 0 ? (
              <Card>
                <CardContent className="py-8 text-center">
                  <p className="text-gray-500 dark:text-slate-400">No assessments match your filters</p>
                </CardContent>
              </Card>
            ) : (
              filteredAssessments.map((assessment) => (
                <Link
                  key={assessment.id}
                  to={
                    assessment.status === 'completed'
                      ? `/dashboard/results/${assessment.id}`
                      : `/dashboard/assessment/new?resume=${assessment.id}`
                  }
                  className="block"
                >
                  <Card className="hover:shadow-md transition-shadow">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                            className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                              assessment.status === 'completed'
                                ? 'bg-green-100'
                                : 'bg-yellow-100'
                            }`}
                          >
                            {assessment.status === 'completed' ? (
                              <FileCheck className="w-5 h-5 text-green-600" />
                            ) : (
                              <Clock className="w-5 h-5 text-yellow-600" />
                            )}
                          </div>
                          <div>
                            <p className="font-medium text-gray-900 dark:text-slate-100">{assessment.title}</p>
                            <p className="text-sm text-gray-500 dark:text-slate-400">
                              {assessment.organization_name || 'Unknown organization'} •{' '}
                              {new Date(assessment.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          {assessment.status === 'completed' && assessment.overall_score != null && (
                            <div className="text-right">
                              <p className="text-lg font-bold text-gray-900 dark:text-slate-100">
                                {Math.round(assessment.overall_score)}%
                              </p>
                              <p className="text-xs text-gray-500 dark:text-slate-400">Score</p>
                            </div>
                          )}

                          <span
                            className={`text-xs px-3 py-1.5 rounded-full font-medium ${
                              assessment.status === 'completed'
                                ? 'bg-green-100 text-green-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {assessment.status === 'completed' ? 'Completed' : 'Resume Draft'}
                          </span>

                          <ChevronRight className="w-5 h-5 text-gray-400 dark:text-slate-500" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))
            )}
          </div>
        </>
      )}
    </div>
  );
}
