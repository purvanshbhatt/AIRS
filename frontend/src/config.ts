/**
 * Application configuration - SINGLE SOURCE OF TRUTH
 *
 * All API configuration flows through this file.
 * Reads from Vite environment variables at build time.
 */

interface Config {
  apiBaseUrl: string;
  appName: string;
  isDevelopment: boolean;
  isProduction: boolean;
  isApiConfigured: boolean;
}

// =============================================================================
// API BASE URL - SINGLE SOURCE OF TRUTH
// =============================================================================
//
// Set VITE_API_BASE_URL in your environment:
//   - Development: VITE_API_BASE_URL=http://localhost:8000
//   - Production:  VITE_API_BASE_URL=https://airs-api-227825933697.us-central1.run.app
//
// If not set, falls back to localhost in development and demo API in production.
// =============================================================================

const configuredApiUrl = import.meta.env.VITE_API_BASE_URL;
const _isApiConfigured = Boolean(configuredApiUrl && configuredApiUrl.trim());
const _isDevelopment = import.meta.env.DEV;
const _isProduction = import.meta.env.PROD;

const fallbackApiUrl = _isProduction
  ? 'https://airs-api-227825933697.us-central1.run.app'
  : 'http://localhost:8000';

const resolvedApiUrl = (configuredApiUrl || fallbackApiUrl).replace(/\/+$/, '');

const config: Config = {
  apiBaseUrl: resolvedApiUrl,
  appName: import.meta.env.VITE_APP_NAME || 'ResilAI',
  isDevelopment: _isDevelopment,
  isProduction: _isProduction,
  isApiConfigured: _isApiConfigured,
};

if (_isDevelopment) {
  const bannerStyle = 'background: #1e40af; color: white; padding: 4px 8px; border-radius: 4px;';
  const infoStyle = 'color: #3b82f6;';
  const warnStyle = 'color: #f59e0b;';

  console.log('%c ResilAI Frontend Configuration ', bannerStyle);
  console.log('%c API Base URL:   %s', infoStyle, config.apiBaseUrl);
  console.log('%c Origin:         %s', infoStyle, typeof window !== 'undefined' ? window.location.origin : 'N/A');
  console.log('%c API Configured: %s', infoStyle, _isApiConfigured ? 'Yes' : 'No (using fallback)');
  console.log('%c Environment:    %s', infoStyle, _isDevelopment ? 'development' : 'production');

  if (!_isApiConfigured) {
    console.log('%c WARNING: VITE_API_BASE_URL not set. Using fallback: %s', warnStyle, config.apiBaseUrl);
    console.log('%c Set this in .env.development/.env.production for reliable API connectivity.', warnStyle);
  }
}

export default config;

// Export individual values for convenience
export const API_BASE_URL = config.apiBaseUrl;
export const { apiBaseUrl, appName, isDevelopment, isProduction, isApiConfigured } = config;
