/**
 * API Diagnostics Panel
 * 
 * Shows when API errors occur to help debug connectivity issues.
 * Displays:
 *   - VITE_API_BASE_URL
 *   - /health status
 *   - /health/cors origin_allowed result
 */

import { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, XCircle, RefreshCw, ChevronDown, ChevronUp, Server, Globe } from 'lucide-react';
import { getApiBaseUrl, checkHealth, checkCors, ApiRequestError } from '../../api';

interface DiagnosticsState {
  loading: boolean;
  apiBaseUrl: string;
  health: {
    status: 'ok' | 'error' | 'pending';
    message?: string;
  };
  cors: {
    status: 'ok' | 'error' | 'pending';
    originAllowed?: boolean;
    requestOrigin?: string;
    allowedOrigins?: string[];
    message?: string;
  };
}

interface ApiDiagnosticsPanelProps {
  /** The error that triggered the diagnostics panel */
  error?: ApiRequestError | Error | string;
  /** Whether to auto-run diagnostics on mount */
  autoRun?: boolean;
  /** Compact mode - only show essential info */
  compact?: boolean;
}

export function ApiDiagnosticsPanel({ error, autoRun = true, compact = false }: ApiDiagnosticsPanelProps) {
  const [expanded, setExpanded] = useState(!compact);
  const [diagnostics, setDiagnostics] = useState<DiagnosticsState>({
    loading: false,
    apiBaseUrl: getApiBaseUrl(),
    health: { status: 'pending' },
    cors: { status: 'pending' },
  });

  const runDiagnostics = async () => {
    setDiagnostics(prev => ({ ...prev, loading: true }));
    
    // Check health
    let healthStatus: DiagnosticsState['health'] = { status: 'pending' };
    try {
      const result = await checkHealth();
      healthStatus = { status: result.status === 'ok' ? 'ok' : 'error', message: result.status };
    } catch (err) {
      healthStatus = { 
        status: 'error', 
        message: err instanceof ApiRequestError ? err.toDisplayMessage() : 'Failed to reach API'
      };
    }

    // Check CORS
    let corsStatus: DiagnosticsState['cors'] = { status: 'pending' };
    try {
      const result = await checkCors();
      corsStatus = {
        status: result.origin_allowed ? 'ok' : 'error',
        originAllowed: result.origin_allowed,
        requestOrigin: result.request_origin || window.location.origin,
        allowedOrigins: result.allowed_origins,
        message: result.origin_allowed ? 'Origin is allowed' : 'Origin NOT in allowed list',
      };
    } catch (err) {
      corsStatus = { 
        status: 'error', 
        message: err instanceof ApiRequestError ? err.toDisplayMessage() : 'CORS check failed'
      };
    }

    setDiagnostics({
      loading: false,
      apiBaseUrl: getApiBaseUrl(),
      health: healthStatus,
      cors: corsStatus,
    });
  };

  useEffect(() => {
    if (autoRun) {
      runDiagnostics();
    }
  }, [autoRun]);

  const getErrorSummary = () => {
    if (!error) return null;
    if (typeof error === 'string') return error;
    if (error instanceof ApiRequestError) {
      return error.toDisplayMessage();
    }
    return error.message;
  };

  const StatusIcon = ({ status }: { status: 'ok' | 'error' | 'pending' }) => {
    if (status === 'ok') return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (status === 'error') return <XCircle className="w-4 h-4 text-red-500" />;
    return <RefreshCw className="w-4 h-4 text-gray-400 animate-spin" />;
  };

  return (
    <div className="mt-4 bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between p-3 hover:bg-amber-100 dark:hover:bg-amber-900/30 transition-colors"
      >
        <div className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
          <span className="text-sm font-medium text-amber-800 dark:text-amber-200">
            API Diagnostics
          </span>
          {diagnostics.loading && (
            <RefreshCw className="w-3 h-3 text-amber-600 animate-spin" />
          )}
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-amber-600" />
        ) : (
          <ChevronDown className="w-4 h-4 text-amber-600" />
        )}
      </button>

      {/* Content */}
      {expanded && (
        <div className="p-3 pt-0 space-y-3 text-sm">
          {/* Error Summary */}
          {error && (
            <div className="p-2 bg-red-100 dark:bg-red-900/30 rounded text-red-800 dark:text-red-200">
              <span className="font-medium">Error: </span>
              {getErrorSummary()}
            </div>
          )}

          {/* API Base URL */}
          <div className="flex items-center gap-2">
            <Server className="w-4 h-4 text-gray-500" />
            <span className="text-gray-600 dark:text-gray-400">API URL:</span>
            <code className="px-2 py-0.5 bg-gray-100 dark:bg-gray-800 rounded text-xs font-mono">
              {diagnostics.apiBaseUrl}
            </code>
          </div>

          {/* Health Check */}
          <div className="flex items-center gap-2">
            <StatusIcon status={diagnostics.health.status} />
            <span className="text-gray-600 dark:text-gray-400">/health:</span>
            <span className={diagnostics.health.status === 'ok' ? 'text-green-600' : 'text-red-600'}>
              {diagnostics.health.message || (diagnostics.health.status === 'pending' ? 'Checking...' : 'Unknown')}
            </span>
          </div>

          {/* CORS Check */}
          <div className="flex items-start gap-2">
            <StatusIcon status={diagnostics.cors.status} />
            <div>
              <div className="flex items-center gap-2">
                <span className="text-gray-600 dark:text-gray-400">/health/cors:</span>
                <span className={diagnostics.cors.originAllowed ? 'text-green-600' : 'text-red-600'}>
                  {diagnostics.cors.message || (diagnostics.cors.status === 'pending' ? 'Checking...' : 'Unknown')}
                </span>
              </div>
              {diagnostics.cors.requestOrigin && (
                <div className="mt-1 text-xs text-gray-500">
                  <Globe className="w-3 h-3 inline mr-1" />
                  Your origin: <code className="px-1 bg-gray-100 dark:bg-gray-800 rounded">{diagnostics.cors.requestOrigin}</code>
                </div>
              )}
            </div>
          </div>

          {/* Refresh Button */}
          <button
            onClick={runDiagnostics}
            disabled={diagnostics.loading}
            className="flex items-center gap-2 px-3 py-1.5 text-xs bg-amber-100 dark:bg-amber-800 hover:bg-amber-200 dark:hover:bg-amber-700 text-amber-800 dark:text-amber-200 rounded transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`w-3 h-3 ${diagnostics.loading ? 'animate-spin' : ''}`} />
            Re-run Diagnostics
          </button>
        </div>
      )}
    </div>
  );
}

export default ApiDiagnosticsPanel;
