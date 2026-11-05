# Security & Compliance Audit Report — ResilAI (AIRS)

**Version**: 1.3.0  
**Compliance Standards**: HIPAA, SOC 2 Type II, NIST CSF  

---

## 1. Authentication & Session Persistence
- **Provider**: Firebase Authentication.
- **Persistence Model**: Explicitly configured `setPersistence(auth, browserLocalPersistence)` in `src/lib/firebase.ts`.
- **Token Verification**: Handled server-side by `app/core/auth.py` verifying Firebase ID Tokens (`verify_id_token()`).
- **Race Condition Prevention**: `getToken()` and `AuthContext` await `auth.authStateReady()`, eliminating token-less API requests during initial page hydration and preventing 401 redirect loops.

---

## 2. CORS Policy & Network Defense
- **Single Source of Truth**: Configured via `CORS_ALLOW_ORIGINS` in environment YAML files.
- **Allowed Staging Origins**: `https://airs-staging-0384513977.web.app`, `https://airs-staging-0384513977.firebaseapp.com`, `http://localhost:5173`.
- **Middleware Safety Net**: `CORSErrorSafetyMiddleware` wraps Starlette response handling, ensuring CORS headers are appended even on 5xx internal server errors and preflight OPTIONS checks.

---

## 3. Interactive Sales Demo Mutation Guard
- **Read-Only Interceptor**: In demo mode (`?env=demo` or host matching `demo.resilai.org`), `api.ts` traps all mutation requests (POST, PUT, DELETE, PATCH).
- **Behavior**: Returns HTTP 403 Forbidden with payload `{"detail": {"message": "Read-Only Demo: Saving changes is disabled in the interactive demo."}}` and triggers toast notification. Server state remains strictly immutable.
