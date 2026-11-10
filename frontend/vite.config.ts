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
              // Graph libraries (network map) stay out of the shared vendor
              // chunks: react-force-graph pulls d3-* and "react" in its name,
              // which used to create a vendor-react <-> vendor-charts cycle
              // and a blank page ("reading 'forwardRef'" of undefined).
              if (/[\\/]node_modules[\\/](react-force-graph[^\\/]*|force-graph|3d-force-graph|three[^\\/]*|d3-force-3d|kapsule|react-kapsule|ngraph[^\\/]*|accessor-fn|float-tooltip|canvas-color-tracker|bezier-js|index-array-by|data-bind-mapper|polished|tinycolor2|lodash-es|@tweenjs)[\\/]/.test(id)) {
                return undefined;
              }
              if (/[\\/]node_modules[\\/](react|react-dom|react-router|react-router-dom|scheduler)[\\/]/.test(id)) {
                return 'vendor-react';
              }
              if (id.includes('recharts') || /[\\/]node_modules[\\/]d3-[^\\/]+[\\/]/.test(id)) {
                return 'vendor-charts';
              }
              if (id.includes('firebase')) {
                return 'vendor-firebase';
              }
              if (id.includes('lucide-react')) {
                return 'vendor-icons';
              }
            }
          },
        },
      },
    },
  };
});

