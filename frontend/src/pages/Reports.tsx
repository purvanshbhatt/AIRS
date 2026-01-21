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
  FileText,
  Download,
  Share2,
  ClipboardList,
  Calendar,
  Building2,
  ExternalLink,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { getReports, downloadReportById, deleteReport, ApiRequestError } from '../api';
import type { Report } from '../types';

export default function Reports() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [totalReports, setTotalReports] = useState(0);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  const loadReports = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await getReports();
      setReports(response.reports);
      setTotalReports(response.total);
    } catch (err) {
      setError(
        err instanceof ApiRequestError
          ? err.toDisplayMessage()
          : 'Failed to load reports'
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReports();
  }, []);

  const handleDownload = async (report: Report) => {
    setDownloading(report.id);
    try {
      const blob = await downloadReportById(report.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const safeTitle = report.title.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '');
      a.download = `AIRS_Report_${safeTitle}_${new Date(report.created_at).toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Download failed:', err);
    } finally {
      setDownloading(null);
    }
  };

  const handleDelete = async (report: Report) => {
    if (!confirm(`Are you sure you want to delete "${report.title}"? This action cannot be undone.`)) {
      return;
    }
    setDeleting(report.id);
    try {
      await deleteReport(report.id);
      // Remove from local state
      setReports((prev) => prev.filter((r) => r.id !== report.id));
      setTotalReports((prev) => prev - 1);
    } catch (err) {
      console.error('Delete failed:', err);
    } finally {
      setDeleting(null);
    }
  };

  const handleShare = async (report: Report) => {
    const url = `${window.location.origin}/dashboard/results/${report.assessment_id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopied(report.id);
      setTimeout(() => setCopied(null), 2000);
    } catch {
      // Fallback for older browsers
      const input = document.createElement('input');
      input.value = url;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setCopied(report.id);
      setTimeout(() => setCopied(null), 2000);
    }
  };

  const getMaturityColor = (level: number) => {
    const colors = ['bg-red-100 text-red-800', 'bg-orange-100 text-orange-800', 'bg-yellow-100 text-yellow-800', 'bg-blue-100 text-blue-800', 'bg-green-100 text-green-800'];
    return colors[Math.min(level - 1, 4)] || colors[0];
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-gray-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
            <p className="text-gray-500 text-sm">Download and share assessment reports</p>
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
          <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
            <FileText className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
            <p className="text-gray-500 text-sm">
              {totalReports} saved report{totalReports !== 1 ? 's' : ''}
            </p>
          </div>
        </div>
      </div>

      {reports.length === 0 ? (
        <Card>
          <EmptyState
            icon={FileText}
            title="No saved reports yet"
            description="Complete an assessment and save the report to see it here. Saved reports preserve a point-in-time snapshot of your findings."
            action={{
              label: 'Start Assessment',
              href: '/dashboard/assessment/new',
            }}
          />
        </Card>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <Card key={report.id} className="hover:shadow-md transition-shadow">
              <CardContent className="py-5">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center shrink-0">
                      <FileText className="w-6 h-6 text-gray-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900">{report.title}</h3>
                      <div className="flex flex-wrap items-center gap-3 mt-1 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Building2 className="w-3.5 h-3.5" />
                          {report.organization_name || 'Unknown org'}
                        </span>
                        <span className="flex items-center gap-1">
                          <Calendar className="w-3.5 h-3.5" />
                          {new Date(report.created_at).toLocaleDateString()}
                        </span>
                        {report.overall_score != null && (
                          <span className="flex items-center gap-1 font-medium text-gray-700">
                            Score: {Math.round(report.overall_score)}%
                          </span>
                        )}
                        {report.maturity_level != null && report.maturity_name && (
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getMaturityColor(report.maturity_level)}`}>
                            L{report.maturity_level}: {report.maturity_name}
                          </span>
                        )}
                        {report.findings_count != null && report.findings_count > 0 && (
                          <span className="flex items-center gap-1 text-amber-600">
                            <AlertCircle className="w-3.5 h-3.5" />
                            {report.findings_count} finding{report.findings_count !== 1 ? 's' : ''}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        From assessment: {report.assessment_title || 'Unknown'}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 ml-16 md:ml-0">
                    <Link to={`/dashboard/results/${report.assessment_id}`}>
                      <Button variant="ghost" size="sm" className="gap-1.5">
                        <ExternalLink className="w-4 h-4" />
                        View
                      </Button>
                    </Link>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleShare(report)}
                      className="gap-1.5"
                    >
                      <Share2 className="w-4 h-4" />
                      {copied === report.id ? 'Copied!' : 'Share'}
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDownload(report)}
                      disabled={downloading === report.id}
                      className="gap-1.5"
                    >
                      <Download
                        className={`w-4 h-4 ${downloading === report.id ? 'animate-bounce' : ''}`}
                      />
                      {downloading === report.id ? 'Downloading...' : 'Download'}
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleDelete(report)}
                      disabled={deleting === report.id}
                      className="gap-1.5 text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className={`w-4 h-4 ${deleting === report.id ? 'animate-pulse' : ''}`} />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Quick start hint */}
      {reports.length > 0 && (
        <Card className="bg-gray-50 border-dashed">
          <CardContent className="py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <ClipboardList className="w-5 h-5 text-gray-400" />
                <p className="text-sm text-gray-600">
                  Need to run another assessment?
                </p>
              </div>
              <Link to="/dashboard/assessment/new">
                <Button variant="ghost" size="sm">
                  Start New Assessment
                </Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
