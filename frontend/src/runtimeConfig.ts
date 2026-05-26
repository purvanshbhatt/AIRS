/**
 * Runtime Environment Configuration — Dynamic Discovery Client.
 *
 * Fetches environment config from `GET /api/v1/config` at startup,
 * eliminating build-time URL injection from static .env files.
 *
 * Design:
 *   1. On first call, fetches `/api/v1/config` using the VITE_API_BASE_URL
 *      hint (if set) or a set of environment-inferred candidate URLs.
 *   2. Caches the resolved config in module scope — no repeated fetches.
 *   3. Falls back gracefully to build-time env vars if the config endpoint
 *      is unreachable (e.g., local dev without a running backend).
 *
 * This satisfies the Deployment Moat requirement: the API base URL is
 * never baked into the client bundle. It is resolved at runtime from the
 * server's own authoritative configuration.
 */

export interface RuntimeConfig {
  environment: string;
  api_base_url: string;
  analytics_enabled: boolean;
  auth_provider: string;
  app_name: string;
  app_version?: string;
}

// ─── Module-level cache ────────────────────────────────────────────────────

let _resolvedConfig: RuntimeConfig | null = null;
let _fetchPromise: Promise<RuntimeConfig> | null = null;

// ─── Candidate URL resolution ──────────────────────────────────────────────

/**
 * Build an ordered list of candidate API base URLs to attempt.
 * Priority:
 *   1. VITE_API_BASE_URL (set explicitly at build time for that env)
 *   2. Hostname inference (staging.resilai.org → api-staging.resilai.org)
 *   3. Local dev fallback
 */
function _getCandidateUrls(): string[] {
  const candidates: string[] = [];

  // Explicit build-time hint (highest priority — already set per-env)
  const buildTimeUrl = import.meta.env.VITE_API_BASE_URL;
  if (buildTimeUrl?.trim()) {
    candidates.push(buildTimeUrl.trim().replace(/\/+$/, ''));
  }

  // Hostname-based inference (works even without build-time vars)
  if (typeof window !== 'undefined') {
    const host = window.location.hostname;
    if (host === 'staging.resilai.org' || host === 'www.staging.resilai.org') {
      candidates.push('https://api-staging.resilai.org');
    } else if (host === 'resilai.org' || host === 'www.resilai.org') {
      candidates.push('https://api.resilai.org');
    } else if (host === 'demo.resilai.org') {
      candidates.push('https://api-demo.resilai.org');
    }
  }

  // Local dev fallback
  if (import.meta.env.DEV) {
    candidates.push('http://localhost:8000');
  }

  return [...new Set(candidates)]; // deduplicate
}

/**
 * Attempt to fetch `/api/v1/config` from a single base URL.
 * Returns null on any network or parse failure.
 */
async function _tryFetch(baseUrl: string): Promise<RuntimeConfig | null> {
  try {
    const res = await fetch(`${baseUrl}/api/v1/config`, {
      method: 'GET',
      headers: { Accept: 'application/json' },
      // Short timeout — config endpoint must be fast
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    // Validate minimum shape
    if (!data?.api_base_url || !data?.environment) return null;
    return data as RuntimeConfig;
  } catch {
    return null;
  }
}

// ─── Public API ────────────────────────────────────────────────────────────

/**
 * Fetch and cache the runtime environment configuration.
 *
 * Safe to call multiple times — the network request is made exactly once.
 * Resolves immediately on subsequent calls using the cached value.
 */
export async function fetchRuntimeConfig(): Promise<RuntimeConfig> {
  if (_resolvedConfig) return _resolvedConfig;

  // Deduplicate concurrent callers — only one fetch in flight
  if (_fetchPromise) return _fetchPromise;

  _fetchPromise = (async (): Promise<RuntimeConfig> => {
    const candidates = _getCandidateUrls();

    for (const baseUrl of candidates) {
      const cfg = await _tryFetch(baseUrl);
      if (cfg) {
        // Normalise: strip trailing slash from api_base_url
        cfg.api_base_url = cfg.api_base_url.replace(/\/+$/, '');
        _resolvedConfig = cfg;
        if (import.meta.env.DEV) {
          console.info(
            '%c[RuntimeConfig] Resolved from %s',
            'color:#10b981;font-weight:bold',
            baseUrl,
            cfg,
          );
        }
        return cfg;
      }
    }

    // All candidates failed — build a safe local fallback
    const fallbackUrl = (candidates[0] ?? 'http://localhost:8000').replace(/\/+$/, '');
    const fallback: RuntimeConfig = {
      environment: import.meta.env.MODE ?? 'local',
      api_base_url: fallbackUrl,
      analytics_enabled: false,
      auth_provider: 'firebase',
      app_name: import.meta.env.VITE_APP_NAME ?? 'ResilAI',
    };
    console.warn(
      '[RuntimeConfig] Could not reach any candidate API endpoint. Using fallback:',
      fallback,
    );
    _resolvedConfig = fallback;
    return fallback;
  })();

  return _fetchPromise;
}

/**
 * Get the cached runtime config synchronously.
 *
 * Returns `null` if `fetchRuntimeConfig()` has not resolved yet.
 * Use this inside components after the app bootstrap has completed.
 */
export function getRuntimeConfig(): RuntimeConfig | null {
  return _resolvedConfig;
}

/**
 * Get the resolved API base URL synchronously.
 *
 * Falls back to build-time env var if runtime config has not loaded yet,
 * ensuring no blank URLs during the brief bootstrap window.
 */
export function getApiBaseUrl(): string {
  return (
    _resolvedConfig?.api_base_url ??
    (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(/\/+$/, '')
  );
}

/**
 * Reset the cached config. Intended for testing only.
 * @internal
 */
export function _resetRuntimeConfig(): void {
  _resolvedConfig = null;
  _fetchPromise = null;
}
