/**
 * Application configuration
 * Reads from Vite environment variables
 */

interface Config {
  apiBaseUrl: string;
  appName: string;
  isDevelopment: boolean;
}

const config: Config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'AIRS',
  isDevelopment: import.meta.env.DEV,
};

export default config;

// Export individual values for convenience
export const { apiBaseUrl, appName, isDevelopment } = config;
