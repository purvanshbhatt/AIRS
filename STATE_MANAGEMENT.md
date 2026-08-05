# State Management Audit & Architecture — ResilAI (AIRS)

**Version**: 1.3.0  
**Scope**: React Context topology, API cache layer, and state boundaries  

---

## 1. Context Topology

The frontend application uses a single, hierarchical React Context tree in `src/App.tsx`:

1. **AuthProvider (`AuthContext.tsx`)**:
   - Manages Firebase Auth state (`user`, `loading`).
   - Explicitly configures `setPersistence(auth, browserLocalPersistence)`.
   - Awaits `auth.authStateReady()` before resolving loading state and before fetching ID tokens in `getToken()`.
   - Prevents race conditions and 401 redirect loops.

2. **DemoModeProvider (`DemoModeContext.tsx`)**:
   - Manages Sales Demo state (`isDemoMode`, `isReadOnly`, `organizationName="Acme Health Systems"`).
   - Intercepts write requests in demo mode and dispatches `resilai-readonly-action`.

3. **PersonaProvider (`PersonaContext.tsx`)**:
   - Manages active persona selection (`Executive` vs `Technical Operations`).

4. **ToastProvider (`ToastContext.tsx`)**:
   - Manages application notification alerts and read-only warnings.

---

## 2. API Cache & Data Fetching

- **Single Source of Truth (`src/cache.ts` & `src/api.ts`)**:
  - `getDailyReadinessReport(orgId)` caches responses to minimize redundant HTTP roundtrips.
  - Runtime base URL is dynamically updated via `fetchRuntimeConfig()` calling `GET /api/v1/config`.
  - Zero duplicate state computations on the frontend (R13 compliance).
