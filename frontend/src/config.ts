/**
 * Application configuration - single source of truth.
 */

interface Config {
  apiBaseUrl: string;
  appName: string;
  isDevelopment: boolean;
  isProduction: boolean;
  isApiConfigured: boolean;
}

const configuredApiUrl = import.meta.env.VITE_API_BASE_URL;
const isApiConfiguredInternal = Boolean(configuredApiUrl && configuredApiUrl.trim());
const isDevelopmentInternal = import.meta.env.DEV;
const isProductionInternal = import.meta.env.PROD;

const resolvedApiUrl = (configuredApiUrl || 'http://localhost:8000').replace(/\/+$/, '');

const config: Config = {
  apiBaseUrl: resolvedApiUrl,
  appName: import.meta.env.VITE_APP_NAME || 'ResilAI',
  isDevelopment: isDevelopmentInternal,
  isProduction: isProductionInternal,
  isApiConfigured: isApiConfiguredInternal,
};

if (isDevelopmentInternal) {
  const bannerStyle = 'background: #1e40af; color: white; padding: 4px 8px; border-radius: 4px;';
  const infoStyle = 'color: #3b82f6;';
  const warnStyle = 'color: #f59e0b;';

  console.log(`%c ${config.appName} Frontend Configuration `, bannerStyle);
  console.log('%cAPI Base URL: %s', infoStyle, config.apiBaseUrl);
  console.log('%cOrigin: %s', infoStyle, typeof window !== 'undefined' ? window.location.origin : 'N/A');
  console.log('%cAPI Configured: %s', infoStyle, isApiConfiguredInternal ? 'Yes' : 'No (fallback)');
  console.log('%cMode: %s', infoStyle, import.meta.env.MODE);

  if (!isApiConfiguredInternal) {
    console.log('%cVITE_API_BASE_URL not set. Using fallback: %s', warnStyle, config.apiBaseUrl);
  }
}

export default config;

export const API_BASE_URL = config.apiBaseUrl;
export const { apiBaseUrl, appName, isDevelopment, isProduction, isApiConfigured } = config;

