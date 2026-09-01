# Staging Deployment Proof

1. **Firebase project:** `gen-lang-client-0384513977`
2. **Firebase site:** `resilai-staging`
3. **Firebase target:** `resilai-staging`
4. **Custom domain:** `https://resilai-staging.web.app` (default staging domain)
5. **Deployed timestamp:** 2026-08-09T16:29:17-04:00
6. **Generated bundle filename/hash:** `index-4hAH3ul0.js` / SHA-256: `756CB0761D4BD232937E0D11FA9A6AE02DDE064E5799D2861AF93FDBDEC3EC29`
7. **Live bundle filename/hash:** `/assets/index-4hAH3ul0.js` / SHA-256: `756CB0761D4BD232937E0D11FA9A6AE02DDE064E5799D2861AF93FDBDEC3EC29`
8. **Proof that the live bundle contains V2 content:** Verified presence of `morning-brief`, `Documents`, and new components in the AST/strings of the live JS bundle.
9. **Proof that the live bundle does NOT contain Acme Health:** **FAILED.** The live bundle **DOES** still contain `Acme Health` and `default-org`. The bundle must be purged in Phase 3 before continuing.

**Conclusion:** The local environment and live staging environment are 100% perfectly synchronized, which means we can confidently proceed to Phase 3 to purge Acme Health from the UI and backend logic without deployment sync risks.

### E2E Test Results (Phase K)
```
=================================================================
Starting Live Staging E2E Integration Validation Suite
Frontend URL: https://airs-staging-0384513977.web.app
Backend URL:  https://airs-api-staging-knu3wsxymq-uc.a.run.app
=================================================================

[PASS] 1. Frontend Staging Accessibility: Status=200, Latency=1236.76ms, Robots=noindex, nofollow, RootDiv=True
[PASS] 2. Backend Health Check (/health): Status=200, Latency=10408.88ms, Body={'status': 'ok', 'product': {'name': 'ResilAI', 'version': None}}
[PASS] 3. Environment Config Endpoint (/api/v1/config): Status=200, Latency=288.33ms, Env=staging, ApiBase=https://airs-api-staging-knu3wsxymq-uc.a.run.app, AuthProvider=firebase
[PASS] 4. CORS Preflight Check (OPTIONS): Status=204, Latency=211.47ms, AllowOrigin=https://airs-staging-0384513977.web.app, AllowCreds=true
[PASS] 5. Auth Guard & 401 Handling: Received expected HTTP 401 Unauthorized.
[PASS] 6. System Status Endpoint (/health/system): Status=200, Latency=265.51ms, Env=staging, DemoMode=False, IsReadOnly=False

=================================================================
Validation Summary: 6/6 tests passed (100.0%)
=================================================================
```
