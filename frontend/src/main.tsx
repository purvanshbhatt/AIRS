import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ThemeProvider } from './contexts/ThemeContext'
import { fetchRuntimeConfig } from './runtimeConfig'
import './index.css'

// Redirect default Firebase Hosting domains to custom enterprise domains
if (typeof window !== 'undefined') {
  const host = window.location.hostname;
  if (host.endsWith('.web.app') || host.endsWith('.firebaseapp.com')) {
    let targetDomain = '';
    if (host.includes('staging')) {
      targetDomain = 'staging.resilai.org';
    } else if (host.includes('demo')) {
      targetDomain = 'demo.resilai.org';
    } else {
      targetDomain = 'resilai.org';
    }

    if (targetDomain && host !== targetDomain) {
      window.location.replace(`https://${targetDomain}${window.location.pathname}${window.location.search}`);
    }
  }
}

// ── Runtime Environment Discovery ──────────────────────────────────────────
// Fetch the server-authoritative environment config BEFORE React mounts.
// This resolves the correct API base URL from GET /api/v1/config,
// eliminating the build-time static URL vulnerability.
fetchRuntimeConfig().then(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </StrictMode>,
  )
}).catch(() => {
  // Config fetch failed entirely (very rare) — mount anyway with fallback
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <ErrorBoundary>
        <BrowserRouter>
          <ThemeProvider>
            <App />
          </ThemeProvider>
        </BrowserRouter>
      </ErrorBoundary>
    </StrictMode>,
  )
})
