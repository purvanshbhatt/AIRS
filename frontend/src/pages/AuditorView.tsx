import { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { getAuditorView, AuditorViewData } from '../api';
import {
  Shield,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Eye,
  Lock,
} from 'lucide-react';

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-600 bg-green-50 border-green-200',
  B: 'text-blue-600 bg-blue-50 border-blue-200',
  C: 'text-yellow-600 bg-yellow-50 border-yellow-200',
  D: 'text-orange-600 bg-orange-50 border-orange-200',
  F: 'text-red-600 bg-red-50 border-red-200',
};

const DIMENSION_LABELS: Record<string, string> = {
  audit: 'Audit Readiness',
  lifecycle: 'Lifecycle Management',
  sla: 'SLA Compliance',
  compliance: 'Regulatory Compliance',
};

export default function AuditorView() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const [data, setData] = useState<AuditorViewData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!token) {
      setError('No auditor token provided. Please use the link shared with you.');
      setLoading(false);
      return;
    }
    getAuditorView(token)
      .then(setData)
      .catch((err) => setError(err.message || 'Failed to load auditor view'))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Shield className="w-12 h-12 text-blue-600 mx-auto animate-pulse" />
          <p className="mt-4 text-gray-600">Validating auditor access...</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-xl shadow-lg p-8 max-w-md text-center">
          <Lock className="w-12 h-12 text-red-500 mx-auto" />
          <h2 className="mt-4 text-xl font-bold text-gray-900">Access Denied</h2>
          <p className="mt-2 text-gray-600">{error || 'Unable to load auditor view.'}</p>
          <p className="mt-4 text-sm text-gray-400">
            If you believe this is an error, contact the organization that shared this link.
          </p>
        </div>
      </div>
    );
  }

  const ghi = data.health_index;
  const gradeColor = GRADE_COLORS[ghi.grade] || GRADE_COLORS['F'];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Shield className="w-8 h-8 text-blue-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">AIRS — Auditor View</h1>
              <p className="text-sm text-gray-500">Read-only governance snapshot</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-500">
            <Eye className="w-4 h-4" />
            <span>View #{data.access_count}</span>
            <span className="mx-2">·</span>
            <Clock className="w-4 h-4" />
            <span>Expires {new Date(data.access_expires).toLocaleDateString()}</span>
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-8 space-y-8">
        {/* Org Header */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{data.org_name}</h2>
              <p className="text-sm text-gray-500 mt-1">Organization ID: {data.org_id}</p>
            </div>
            <div className={`px-6 py-4 rounded-xl border-2 text-center ${gradeColor}`}>
              <div className="text-4xl font-black">{ghi.grade}</div>
              <div className="text-sm font-medium mt-1">GHI {(ghi.ghi * 100).toFixed(0)}%</div>
            </div>
          </div>
        </div>

        {/* GHI Dimensions */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Governance Health Index Breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(ghi.dimensions).map(([key, value]) => (
              <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
                <div className="text-2xl font-bold text-gray-900">{(value * 100).toFixed(0)}%</div>
                <div className="text-sm text-gray-500 mt-1">{DIMENSION_LABELS[key] || key}</div>
                <div className="text-xs text-gray-400 mt-1">Weight: {((ghi.weights[key] || 0) * 100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </div>

        {/* Compliance Status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Overall Compliance Status</h3>
          <div className="flex items-center gap-3">
            {data.passed ? (
              <>
                <CheckCircle className="w-6 h-6 text-green-500" />
                <span className="text-green-700 font-medium">All governance checks passed</span>
              </>
            ) : (
              <>
                <AlertTriangle className="w-6 h-6 text-amber-500" />
                <span className="text-amber-700 font-medium">{data.issues.length} issue(s) detected</span>
              </>
            )}
          </div>
          {data.issues.length > 0 && (
            <ul className="mt-4 space-y-2">
              {data.issues.map((issue, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <XCircle className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
                  {issue}
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Applicable Frameworks */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Applicable Compliance Frameworks</h3>
          {data.applicable_frameworks.length === 0 ? (
            <p className="text-gray-500">No frameworks determined. Governance profile may be incomplete.</p>
          ) : (
            <div className="space-y-3">
              {data.applicable_frameworks.map((f, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div>
                    <span className="font-medium text-gray-900">{f.framework}</span>
                    <p className="text-sm text-gray-500 mt-0.5">{f.reason}</p>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${
                    f.priority === 'high' ? 'bg-red-100 text-red-700' :
                    f.priority === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                    'bg-gray-100 text-gray-600'
                  }`}>
                    {f.priority}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Governance Profile Summary */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Governance Profile</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
            {Object.entries(data.governance_profile).map(([key, value]) => (
              <div key={key} className="p-3 bg-gray-50 rounded-lg">
                <div className="text-gray-500 capitalize">{key.replace(/_/g, ' ')}</div>
                <div className="font-medium text-gray-900 mt-1">
                  {typeof value === 'boolean' ? (value ? 'Yes' : 'No') :
                   Array.isArray(value) ? value.join(', ') || '—' :
                   value?.toString() || '—'}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-gray-400 py-8 border-t border-gray-200">
          <Lock className="w-4 h-4 inline mr-1" />
          Read-only view — generated by AIRS Governance Platform
          <br />
          This snapshot is for auditor review only. No data can be modified through this view.
        </div>
      </div>
    </div>
  );
}
