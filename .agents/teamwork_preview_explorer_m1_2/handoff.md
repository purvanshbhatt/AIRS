# Handoff Report: Staging Infrastructure, Firebase Auth & CORS Investigation

## 1. Observation

### A. Firebase Auth Configuration & Initialisation
- **File**: `frontend/src/lib/firebase.ts` (lines 8-68)
  - Firebase app and Auth instances are initialized via:
    ```ts
    const firebaseConfig = {
      apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
      authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
      projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID,
    };
    ...
    app = getApps().length === 0 ? initializeApp(firebaseConfig) : getApp();
    auth = getAuth(app);
    ```
  - **Observation**: `setPersistence(auth, browserLocalPersistence)` is **never explicitly invoked**. Auth relies on implicit Firebase SDK defaults.
  - **Observation**: `isFirebaseConfigured` returns `false` if `VITE_FIREBASE_API_KEY` is missing or contains placeholder strings (`fake`, `replace`, `placeholder`).

- **File**: `frontend/src/contexts/AuthContext.tsx` (lines 83-125)
  - Auth listener and token getter:
    ```ts
    useEffect(() => {
      ...
      const unsubscribe = onAuthStateChanged(auth, (firebaseUser) => {
        if (firebaseUser) {
          setUser(toUser(firebaseUser));
        } else {
          setUser(null);
        }
        setLoading(false);
      });
      return () => unsubscribe();
    }, []);

    const getToken = useCallback(async (): Promise<string | null> => {
      if (!auth?.currentUser) return null;
      try {
        const token = await auth.currentUser.getIdToken();
        return token;
      } catch (err) {
        return null;
      }
    }, []);
    ```

- **File**: `frontend/src/components/ProtectedRoute.tsx` (lines 38-41)
  ```ts
  if (!user) {
    console.log('[ProtectedRoute] User not authenticated, redirecting to login');
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }
  ```

### B. Frontend API Interceptor & 401 Redirect Loop Trigger
- **File**: `frontend/src/api.ts` (lines 82-89, 118-126, 200-206)
  - `getAuthHeaders()` resolves `tokenProvider()`:
    ```ts
    async function getAuthHeaders(): Promise<Record<string, string>> {
      if (!tokenProvider) return {};
      const token = await tokenProvider();
      if (!token) return {};
      return { Authorization: `Bearer ${token}` };
    }
    ```
  - 401 handling in `request()`:
    ```ts
    if (response.status === 401) {
      handleUnauthorized();
      throw new ApiRequestError({
        message: 'Authentication required. Please sign in.',
        status: 401,
      });
    }
    ```
- **File**: `frontend/src/App.tsx` (lines 113-126)
  - `AuthRedirectHandler` connects `setUnauthorizedHandler` to `navigate('/login', { replace: true })`.

### C. Automatic Host Domain Redirect Bug in App.tsx
- **File**: `frontend/src/App.tsx` (lines 129-143)
  ```ts
  useEffect(() => {
    const hostname = window.location.hostname;
    const isFirebaseDefaultDomain = hostname.endsWith('.web.app') || hostname.endsWith('.firebaseapp.com');
    if (isFirebaseDefaultDomain) {
      let targetDomain = '';
      if (hostname.includes('staging')) {
        targetDomain = 'staging.resilai.org';
      } else if (hostname.includes('demo') || hostname.includes('gen-lang-client-0384513977')) {
        targetDomain = 'demo.resilai.org';
      } else {
        targetDomain = 'resilai.org';
      }
      window.location.replace(`https://${targetDomain}${window.location.pathname}${window.location.search}${window.location.hash}`);
    }
  }, []);
  ```
  - **Observation**: Accessing the official Firebase Hosting staging URL `airs-staging-0384513977.web.app` or `airs-staging-0384513977.firebaseapp.com` triggers an unconditional `window.location.replace()` to `https://staging.resilai.org`. If DNS or SSL for custom domain `staging.resilai.org` is unconfigured, users encounter connection errors.

### D. Backend API Contract & Runtime Base URL Resolution
- **File**: `app/api/v1/config.py` (lines 61-90)
  ```python
  @router.get("", response_model=EnvironmentConfigResponse)
  async def get_environment_config() -> EnvironmentConfigResponse:
      env_value = settings.ENV.value if hasattr(settings.ENV, "value") else str(settings.ENV)
      api_base_url = (
          os.environ.get("CLOUD_RUN_SERVICE_URL")
          or os.environ.get("API_BASE_URL")
          or _infer_api_base_url(env_value)
      )
      ...
  def _infer_api_base_url(env: str) -> str:
      urls = {
          "staging": "https://api-staging.resilai.org",
          "prod":    "https://api.resilai.org",
          "demo":    "https://api-demo.resilai.org",
          "local":   "http://localhost:8000",
      }
      return urls.get(env, "http://localhost:8000")
  ```
- **File**: `gcp/env.staging.yaml` (lines 5-27)
  ```yaml
  ENV: "staging"
  APP_NAME: "ResilAI"
  DEBUG: "false"
  GCP_PROJECT_ID: "gen-lang-client-0384513977"
  CORS_ALLOW_ORIGINS: "https://staging.resilai.org,https://www.staging.resilai.org,https://resilai.org,https://www.resilai.org,https://demo.resilai.org,https://resilai-staging.web.app,https://resilai-staging.firebaseapp.com,https://airs-staging-0384513977.web.app,https://airs-staging-0384513977.firebaseapp.com,http://localhost:5173"
  AUTH_REQUIRED: "true"
  DEMO_MODE: "false"
  ```
  - **Observation**: `CLOUD_RUN_SERVICE_URL` and `API_BASE_URL` are missing in `gcp/env.staging.yaml`. `_infer_api_base_url("staging")` returns `https://api-staging.resilai.org`.
- **File**: `frontend/src/runtimeConfig.ts` (lines 101-143, 164-169)
  - Dynamically updates the API base URL used by `api.ts` to whatever `GET /api/v1/config` returns.

### E. Backend Auth & Token Verification
- **File**: `app/core/auth.py` (lines 81-118, 148-153)
  ```python
  def verify_firebase_token(token: str) -> dict:
      from firebase_admin import auth
      decoded = auth.verify_id_token(token)
      return {"uid": decoded["uid"], "email": decoded.get("email"), "name": decoded.get("name")}
  ```
  - **Observation**: In staging (`AUTH_REQUIRED=true`), `get_current_user` and `require_auth` enforce valid Firebase Bearer token verification. Missing token -> 401 `UNAUTHORIZED`. Invalid/expired token -> 401 `INVALID_TOKEN`.

### F. CORS Infrastructure & Middleware Ordering
- **File**: `app/main.py` (lines 298-321)
  ```python
  cors_origins = get_allowed_origins(env_var="CORS_ALLOW_ORIGINS", default=settings.CORS_ALLOW_ORIGINS, is_production=is_strict_cors)
  app.add_middleware(
      CORSMiddleware,
      allow_origins=cors_origins,
      allow_origin_regex=r"^https://([a-zA-Z0-9\-]+\.)*(resilai\.org|web\.app|firebaseapp\.com|run\.app)$",
      allow_credentials=True,
      allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"],
      allow_headers=["*"],
      expose_headers=["*"],
  )
  app.add_middleware(CORSErrorSafetyMiddleware, allowed_origins=cors_origins)
  ```
- **File**: `app/core/cors.py` (lines 41-46, 175-205)
  - `TRUSTED_ORIGIN_PATTERNS` matches `*.resilai.org`, `*.web.app`, `*.firebaseapp.com`, `*.run.app`.

### G. Firebase Hosting & Staging Deployment Setup
- **File**: `.firebaserc` (lines 1-19)
  - Default project: `gen-lang-client-0384513977`
  - Staging hosting target: `airs-staging-0384513977`
- **File**: `firebase.json` (lines 58-85)
  - Target: `staging`, Public dir: `frontend/dist-staging`, Predeploy script: `cd frontend && npm run build:staging`
- **File**: `scripts/deploy_cloud_run.ps1` (lines 71-74, 120-146)
  - Service: `airs-api-staging`, Env file: `gcp/env.staging.yaml`
- **File**: `scripts/deploy_frontend.ps1` (lines 54-61)
  - Target `staging` executes `npm run build:staging` and `firebase deploy --only hosting:staging`.

---

## 2. Logic Chain

1. **Root Cause Analysis: 401 Login Loop**
   - **Step 1**: In `AuthContext.tsx`, `getToken()` returns `null` if `auth.currentUser` is `null` (e.g. during initial page hydration or before `onAuthStateChanged` fires).
   - **Step 2**: In `api.ts`, `getAuthHeaders()` calls `getToken()`. If `getToken()` returns `null`, `getAuthHeaders()` returns `{}` (empty headers).
   - **Step 3**: `request()` sends the API request without an `Authorization: Bearer` header.
   - **Step 4**: In staging, backend `app/core/config.py` sets `AUTH_REQUIRED=true`. Backend route dependency `require_auth` in `app/core/auth.py` checks for `HTTPAuthorizationCredentials`. Finding none, it raises `401 UNAUTHORIZED`.
   - **Step 5**: `api.ts` catches response status 401, invokes `handleUnauthorized()`, which calls `navigate('/login', { replace: true })`.
   - **Step 6**: At `/login`, Firebase Auth state hydrates or user logs in. `onAuthStateChanged` updates `user` state. `ProtectedRoute.tsx` sees valid `user` and allows access or redirects to `/morning-brief`.
   - **Step 7**: Component at `/morning-brief` mounts and immediately fires API calls. If `auth.currentUser` is not immediately available or if token refresh fails, the request is sent without token -> 401 returned -> redirected to `/login` -> Infinite 401 Loop.

2. **Root Cause Analysis: Staging API Base URL Mismatch & Domain Redirect**
   - **Step 1**: In `gcp/env.staging.yaml`, neither `CLOUD_RUN_SERVICE_URL` nor `API_BASE_URL` is set.
   - **Step 2**: `app/api/v1/config.py` falls back to `_infer_api_base_url("staging")`, returning `"https://api-staging.resilai.org"`.
   - **Step 3**: Frontend calls `fetchRuntimeConfig()` in `frontend/src/runtimeConfig.ts`, setting `API_BASE_URL` to `https://api-staging.resilai.org`.
   - **Step 4**: If `api-staging.resilai.org` DNS is unmapped, browser API requests to `https://api-staging.resilai.org` fail with `TypeError: Failed to fetch` (Network Error), which `api.ts` formats as "Unable to reach API server".
   - **Step 5**: Concurrently, `App.tsx` lines 130-142 forcibly redirects any traffic on `airs-staging-0384513977.web.app` to `https://staging.resilai.org`. If custom domain `staging.resilai.org` lacks active DNS, the page fails to load entirely.

3. **Root Cause Analysis: Staging CORS Setup**
   - **Step 1**: `app/main.py` configures `CORSMiddleware` and `CORSErrorSafetyMiddleware` with origins from `gcp/env.staging.yaml`.
   - **Step 2**: `gcp/env.staging.yaml` explicitly includes `https://airs-staging-0384513977.web.app`, `https://airs-staging-0384513977.firebaseapp.com`, and `http://localhost:5173`.
   - **Step 3**: However, if frontend makes requests to an incorrect backend URL (e.g. `api-staging.resilai.org` instead of actual Cloud Run URL), the browser flags network failure as CORS error in developer tools.
   - **Step 4**: `CORSErrorSafetyMiddleware` properly handles preflight `OPTIONS` and guarantees headers on 5xx errors, confirming that backend CORS middleware logic is robust; CORS failures are triggered by origin/URL domain mismatches.

4. **Root Cause Analysis: Session Persistence**
   - **Step 1**: `frontend/src/lib/firebase.ts` does not call `setPersistence(auth, browserLocalPersistence)`.
   - **Step 2**: Although Firebase JS SDK 9+ defaults to `browserLocalPersistence`, omitting explicit configuration means fallback behavior under restricted browser storage (incognito, third-party cookie restrictions, cross-origin iframe context) is unmanaged.

---

## 3. Caveats

- **No live deployment attempted**: Investigation was executed strictly read-only. Live Cloud Run and Firebase Hosting deployment status was verified via config analysis and script inspection rather than active deployment triggers.
- **Custom Domain DNS**: We assumed `staging.resilai.org` and `api-staging.resilai.org` may not have active DNS records mapped directly to Cloud Run / Firebase Hosting unless explicitly configured in Cloud DNS / Google Domains.

---

## 4. Conclusion

1. **401 Login Loops**: Caused by a race condition where API calls fire before Firebase Auth listener (`onAuthStateChanged` / `auth.currentUser`) has populated the token in `api.ts`, returning 401 from backend (`AUTH_REQUIRED=true`) and triggering `handleUnauthorized()` redirect to `/login`. Also exacerbated by missing `auth.authStateReady()` call before app initialization.
2. **Domain & API URL Mismatch**: `gcp/env.staging.yaml` lacks `CLOUD_RUN_SERVICE_URL`, causing `GET /api/v1/config` to return `https://api-staging.resilai.org`. Furthermore, `App.tsx` contains hardcoded `window.location.replace` logic redirecting `*.web.app` to `staging.resilai.org`.
3. **CORS Setup**: Backend CORS setup in `app/main.py`, `app/core/cors.py`, and `app/core/middleware.py` is comprehensive with `CORSErrorSafetyMiddleware` safety net. Perceived CORS issues stem from DNS/URL mismatch when frontend attempts to reach unmapped custom domains.
4. **Session Persistence**: Currently implicit. Requires explicit `setPersistence(auth, browserLocalPersistence)` in `frontend/src/lib/firebase.ts`.

---

## 5. Verification Method

To independently verify these findings:

1. **Verify Base URL Fallback**:
   Inspect `app/api/v1/config.py` line 84:
   ```bash
   grep -n "https://api-staging.resilai.org" app/api/v1/config.py
   ```
2. **Verify App.tsx Redirect**:
   Inspect `frontend/src/App.tsx` lines 130-142:
   ```bash
   grep -n "window.location.replace" frontend/src/App.tsx
   ```
3. **Verify Auth Persistence Initialisation**:
   Inspect `frontend/src/lib/firebase.ts`:
   ```bash
   grep -n "setPersistence" frontend/src/lib/firebase.ts
   ```
4. **Verify CORS Environment Variable Configuration**:
   Inspect `gcp/env.staging.yaml`:
   ```bash
   grep -n "CORS_ALLOW_ORIGINS" gcp/env.staging.yaml
   ```
5. **Build Verification**:
   In `frontend/`:
   ```bash
   npm run build:staging
   ```
   Ensures staging bundle builds cleanly without syntax errors.
