import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ThemeProvider } from './contexts/ThemeContext'
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
