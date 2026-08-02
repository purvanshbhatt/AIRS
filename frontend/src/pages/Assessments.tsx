import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
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
  PlugZap,
  Archive,
} from 'lucide-react';
import { getAssessments, deleteAssessment, ApiRequestError } from '../api';
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

  // Handle Archive
  const handleArchive = async (e: React.MouseEvent, id: string) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await deleteAssessment(id);
      setAssessments(assessments.filter((a) => a.id !== id));
    } catch (err) {
      console.error('Failed to archive assessment:', err);
    }
  };

  // Filter assessments
  const filteredAssessments = assessments.filter((a) => {
    // Status filter
    if (statusFilter === 'completed' && a.status !== 'completed') return false;
    if (statusFilter === 'draft' && a.status === 'completed') return false;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        (a.title?.toLowerCase().includes(query) ?? false) ||
        (a.organization_name?.toLowerCase().includes(query) ?? false)
      );
    }
    return true;
  });

  const completedCount = assessments.filter((a) => a.status === 'completed').length;
  const draftCount = assessments.filter((a) => a.status !== 'completed').length;

  if (loading) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl flex items-center justify-center border border-slate-200 dark:border-slate-700">
            <ClipboardList className="w-5 h-5 text-slate-600 dark:text-slate-300" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Assessments</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm">Manage your security assessments</p>
          </div>
        </div>
        <ListSkeleton count={5} />
      </motion.div>
    );
  }

  if (error) {
    return (
      <Card className="max-w-lg mx-auto mt-12 rounded-3xl border border-red-200/50 dark:border-red-900/30 bg-red-50/20 dark:bg-red-950/10 shadow-sm">
        <CardContent className="py-8 text-center">
          <p className="text-red-600 dark:text-red-400 font-medium mb-4">{error}</p>
          <Button onClick={() => window.location.reload()}>Retry</Button>
        </CardContent>
      </Card>
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
          <div className="w-10 h-10 bg-purple-50 dark:bg-purple-950/30 rounded-xl flex items-center justify-center border border-purple-200 dark:border-purple-800/40 shadow-sm">
            <ClipboardList className="w-5 h-5 text-purple-600 dark:text-purple-400" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100">Assessments</h1>
            <p className="text-slate-500 dark:text-slate-400 text-sm font-medium">
              How is our compliance posture trending? ({assessments.length} assessment{assessments.length !== 1 ? 's' : ''})
            </p>
          </div>
        </div>
        {!isReadOnly && (
          <Link to="/dashboard/assessment/new">
            <Button className="gap-2 rounded-xl font-bold hover:scale-[1.01] transition-all bg-[#00C853] hover:bg-[#00C853]/90 text-white border-transparent">
              <PlugZap className="w-4.5 h-4.5" />
              Connect Security Data Sources
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
              label: 'Connect Security Data Sources',
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
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 dark:text-slate-500" />
              <input
                type="text"
                placeholder="Search by title or organization..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2.5 border border-slate-200 dark:border-slate-800 rounded-xl text-sm bg-white dark:bg-slate-950 text-slate-900 dark:text-slate-100 focus:outline-none focus:ring-2 focus:ring-primary-500/40 transition-all duration-200"
              />
            </div>

            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4 text-slate-400 dark:text-slate-500" />
              <div className="flex bg-slate-100 dark:bg-slate-950/60 rounded-xl p-1 border border-slate-200 dark:border-slate-800">
                <button
                  onClick={() => setStatusFilter('all')}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-all ${
                    statusFilter === 'all'
                      ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-medium'
                  }`}
                >
                  All ({assessments.length})
                </button>
                <button
                  onClick={() => setStatusFilter('completed')}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-all flex items-center gap-1.5 ${
                    statusFilter === 'completed'
                      ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-medium'
                  }`}
                >
                  <FileCheck className="w-3.5 h-3.5" />
                  Completed ({completedCount})
                </button>
                <button
                  onClick={() => setStatusFilter('draft')}
                  className={`px-3 py-1.5 text-sm rounded-lg transition-all flex items-center gap-1.5 ${
                    statusFilter === 'draft'
                      ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm font-semibold'
                      : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-100 font-medium'
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
                  <p className="text-slate-500 dark:text-slate-400 font-medium">No assessments match your filters</p>
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
                  <Card className="shadow-sm hover:shadow-md transition-all duration-300 hover:scale-[1.005] hover:border-slate-300 dark:hover:border-slate-700 bg-white/60 dark:bg-slate-950/20">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                            className={`w-10 h-10 rounded-xl flex items-center justify-center border transition-colors ${
                              assessment.status === 'completed'
                                ? 'bg-green-50 dark:bg-green-950/30 border-green-200 dark:border-green-900/40 text-green-600 dark:text-green-400'
                                : 'bg-amber-50 dark:bg-amber-950/30 border-amber-200 dark:border-amber-900/40 text-amber-600 dark:text-amber-400'
                            }`}
                          >
                            {assessment.status === 'completed' ? (
                              <FileCheck className="w-5 h-5" />
                            ) : (
                              <Clock className="w-5 h-5" />
                            )}
                          </div>
                          <div>
                            <p className="font-semibold text-slate-900 dark:text-slate-100">{assessment.title}</p>
                            <p className="text-sm text-slate-500 dark:text-slate-400 font-medium mt-0.5">
                              {assessment.organization_name || 'Unknown organization'} •{' '}
                              {new Date(assessment.created_at).toLocaleDateString()}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-center gap-4">
                          {assessment.status === 'completed' && assessment.overall_score != null && (
                            <div className="text-right mr-2">
                              <p className="text-lg font-extrabold text-slate-900 dark:text-slate-100">
                                {Math.round(assessment.overall_score)}%
                              </p>
                              <p className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wider">Score</p>
                            </div>
                          )}

                          <span
                            className={`text-xs px-2.5 py-0.5 rounded-lg font-bold transition-all ${
                              assessment.status === 'completed'
                                ? 'bg-green-50 dark:bg-green-950/30 text-green-700 dark:text-green-400 border border-green-200 dark:border-green-900/40'
                                : 'bg-amber-50 dark:bg-amber-950/30 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-900/40'
                            }`}
                          >
                            {assessment.status === 'completed' ? 'Completed' : 'Resume Draft'}
                          </span>

                          <button
                            onClick={(e) => handleArchive(e, assessment.id)}
                            className="p-1.5 ml-2 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 rounded-lg transition-colors"
                            title="Archive Assessment"
                          >
                            <Archive className="w-5 h-5" />
                          </button>

                          <ChevronRight className="w-5 h-5 text-slate-400 dark:text-slate-500 ml-2" />
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
    </motion.div>
  );
}
