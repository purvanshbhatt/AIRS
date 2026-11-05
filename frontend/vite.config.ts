import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import { execSync } from 'child_process'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  let commitHash = 'unknown';
  try {
    commitHash = execSync('git rev-parse --short HEAD').toString().trim();
  } catch (e) {
    console.warn('Failed to fetch git commit hash');
  }
  const buildTime = new Date().toISOString();

  return {
    plugins: [react()],
    define: {
      'window.__RESILAI_BUILD__': JSON.stringify({
        commit: commitHash,
        buildTime: buildTime,
        environment: mode,
        api: env.VITE_API_BASE_URL || 'unknown',
        version: process.env.npm_package_version || '0.0.0'
      })
    },
    build: {
      outDir: `dist-${mode}`,
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules')) {
              if (id.includes('recharts') || id.includes('d3-')) {
                return 'vendor-charts';
              }
              if (id.includes('firebase')) {
                return 'vendor-firebase';
              }
              if (id.includes('lucide-react')) {
                return 'vendor-icons';
              }
              if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) {
                return 'vendor-react';
              }
            }
          },
        },
      },
    },
  };
});

