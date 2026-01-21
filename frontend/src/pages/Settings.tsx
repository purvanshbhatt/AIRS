import { useState, useEffect } from 'react';
import { checkHealth, getApiBaseUrl, ApiRequestError } from '../api';
import { clearAllLocalData, getLocalDataSummary } from '../lib/userData';
import { useAuth } from '../contexts/AuthContext';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  Button,
} from '../components/ui';
import { Settings as SettingsIcon, Server, CheckCircle, XCircle, RefreshCw, Trash2, Database, User, Mail, Shield } from 'lucide-react';

interface HealthStatus {
  status: 'checking' | 'ok' | 'error';
  message?: string;
  lastChecked?: Date;
}

export default function Settings() {
  const [health, setHealth] = useState<HealthStatus>({ status: 'checking' });
  const [localDataSummary, setLocalDataSummary] = useState<{ key: string; size: number }[]>([]);
  const [clearingData, setClearingData] = useState(false);
  const apiBaseUrl = getApiBaseUrl();
  const { user } = useAuth();

  const refreshLocalDataSummary = () => {
    setLocalDataSummary(getLocalDataSummary());
  };

  const handleClearLocalData = () => {
    setClearingData(true);
    clearAllLocalData();
    refreshLocalDataSummary();
    setTimeout(() => setClearingData(false), 500);
  };

  const checkApiHealth = async () => {
    setHealth({ status: 'checking' });
    try {
      const result = await checkHealth();
      setHealth({
        status: result.status === 'ok' ? 'ok' : 'error',
        message: result.status === 'ok' ? 'API is responding' : `Unexpected status: ${result.status}`,
        lastChecked: new Date(),
      });
    } catch (err) {
      setHealth({
        status: 'error',
        message: err instanceof ApiRequestError ? err.toDisplayMessage() : (err instanceof Error ? err.message : 'Unknown error'),
        lastChecked: new Date(),
      });
    }
  };

  useEffect(() => {
    checkApiHealth();
    refreshLocalDataSummary();
  }, []);

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
          <SettingsIcon className="w-5 h-5 text-gray-600" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-500 text-sm">Profile, environment, and system configuration</p>
        </div>
      </div>

      {/* Profile Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <User className="h-5 w-5 text-gray-500" />
            <CardTitle className="text-lg">Profile</CardTitle>
          </div>
          <CardDescription>Your account information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
              {user?.photoURL ? (
                <img
                  src={user.photoURL}
                  alt="Profile"
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <span className="text-2xl font-semibold text-primary-700">
                  {user?.displayName?.charAt(0).toUpperCase() ||
                    user?.email?.charAt(0).toUpperCase() ||
                    'U'}
                </span>
              )}
            </div>
            <div>
              <p className="text-lg font-semibold text-gray-900">
                {user?.displayName || 'User'}
              </p>
              <p className="text-sm text-gray-500 flex items-center gap-1">
                <Mail className="w-3.5 h-3.5" />
                {user?.email || 'Not signed in'}
              </p>
            </div>
          </div>

          <div className="pt-3 border-t border-gray-100 space-y-2">
            <div className="flex justify-between items-center text-sm">
              <span className="text-gray-500 flex items-center gap-1">
                <Shield className="w-3.5 h-3.5" />
                User ID
              </span>
              <code className="bg-gray-100 px-2 py-0.5 rounded font-mono text-xs text-gray-700">
                {user?.uid ? `${user.uid.slice(0, 8)}...` : 'N/A'}
              </code>
            </div>

          </div>
        </CardContent>
      </Card>

      {/* API Status Widget */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Server className="h-5 w-5 text-gray-500" />
              <CardTitle className="text-lg">API Status</CardTitle>
            </div>
            <button
              onClick={checkApiHealth}
              disabled={health.status === 'checking'}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
              title="Refresh status"
            >
              <RefreshCw className={`h-4 w-4 text-gray-500 ${health.status === 'checking' ? 'animate-spin' : ''}`} />
            </button>
          </div>
          <CardDescription>Backend API connection status</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Status indicator */}
          <div className="flex items-center gap-3">
            {health.status === 'checking' && (
              <>
                <div className="w-3 h-3 bg-yellow-400 rounded-full animate-pulse" />
                <span className="text-yellow-600 font-medium">Checking...</span>
              </>
            )}
            {health.status === 'ok' && (
              <>
                <CheckCircle className="w-5 h-5 text-green-500" />
                <span className="text-green-600 font-medium">OK</span>
              </>
            )}
            {health.status === 'error' && (
              <>
                <XCircle className="w-5 h-5 text-red-500" />
                <span className="text-red-600 font-medium">FAIL</span>
              </>
            )}
          </div>

          {/* Error message if any */}
          {health.status === 'error' && health.message && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {health.message}
            </div>
          )}

          {/* API URL */}
          <div className="pt-3 border-t border-gray-100">
            <p className="text-xs text-gray-500 mb-1">API Base URL (VITE_API_BASE_URL)</p>
            <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono text-gray-700 block overflow-x-auto">
              {apiBaseUrl}
            </code>
          </div>

          {/* Last checked */}
          {health.lastChecked && (
            <p className="text-xs text-gray-400">
              Last checked: {health.lastChecked.toLocaleTimeString()}
            </p>
          )}
        </CardContent>
      </Card>

      {/* Debug Info */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Debug Information</CardTitle>
          <CardDescription>Useful for troubleshooting connection issues</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="text-xs text-gray-500 mb-1">Environment</p>
            <code className="text-sm bg-gray-100 px-2 py-1 rounded font-mono text-gray-700">
              {import.meta.env.MODE}
            </code>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Health Endpoint</p>
            <a
              href={`${apiBaseUrl}/health`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:underline font-mono"
            >
              {apiBaseUrl}/health
            </a>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">LLM Status Endpoint</p>
            <a
              href={`${apiBaseUrl}/health/llm`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-primary-600 hover:underline font-mono"
            >
              {apiBaseUrl}/health/llm
            </a>
          </div>
        </CardContent>
      </Card>

      {/* Local Data Management */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-gray-500" />
            <CardTitle className="text-lg">Local Data</CardTitle>
          </div>
          <CardDescription>
            Manage locally stored data like draft assessments and cached information
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {localDataSummary.length > 0 ? (
            <div className="space-y-2">
              <p className="text-sm text-gray-600 mb-2">Stored items:</p>
              {localDataSummary.map((item) => (
                <div key={item.key} className="flex justify-between items-center text-sm bg-gray-50 px-3 py-2 rounded">
                  <code className="font-mono text-gray-700">{item.key}</code>
                  <span className="text-gray-500 text-xs">
                    {item.size < 1024
                      ? `${item.size} bytes`
                      : `${(item.size / 1024).toFixed(1)} KB`}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-gray-500 italic">No local data stored</p>
          )}

          <div className="pt-3 border-t border-gray-100">
            <Button
              variant="outline"
              onClick={handleClearLocalData}
              disabled={clearingData || localDataSummary.length === 0}
              className="flex items-center gap-2"
            >
              <Trash2 className={`h-4 w-4 ${clearingData ? 'animate-pulse' : ''}`} />
              {clearingData ? 'Clearing...' : 'Clear Local Data'}
            </Button>
            <p className="text-xs text-gray-400 mt-2">
              This will remove any draft assessments and cached data. Your saved assessments in the cloud are not affected.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
