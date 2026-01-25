import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks - split large dependencies
          'vendor-react': ['react', 'react-dom', 'react-router-dom'],
          'vendor-firebase': ['firebase/app', 'firebase/auth'],
          'vendor-icons': ['lucide-react'],
          // ResultsTabs is heavy - ensure it's in its own chunk
          'results-tabs': ['./src/components/ResultsTabs.tsx'],
        },
      },
    },
    // Increase chunk size warning limit (optional, but helps with lucide)
    chunkSizeWarningLimit: 600,
  },
})
