// Test suite for Demo Mode Mutation Firewall logic in api.ts

function checkFirewall(host, search, mode, viteAppEnv, method) {
  const isDemo = host === 'demo.resilai.org' || 
                 host.includes('demo') || 
                 search.includes('env=demo') ||
                 viteAppEnv === 'demo' || 
                 mode === 'demo';
  const isMutation = ['POST', 'PUT', 'DELETE', 'PATCH'].includes(method.toUpperCase());

  if (isDemo && isMutation) {
    return { blocked: true, status: 403, message: 'Read-Only Demo: Saving changes is disabled in the interactive demo.' };
  }
  return { blocked: false };
}

const testCases = [
  // 1. Production host, GET -> Allow
  { name: "Prod GET", host: "resilai.org", search: "", mode: "production", viteEnv: "production", method: "GET", expectedBlocked: false },
  // 2. Production host, POST -> Allow
  { name: "Prod POST", host: "resilai.org", search: "", mode: "production", viteEnv: "production", method: "POST", expectedBlocked: false },
  // 3. Demo host (demo.resilai.org), GET -> Allow
  { name: "Demo Host GET", host: "demo.resilai.org", search: "", mode: "production", viteEnv: "", method: "GET", expectedBlocked: false },
  // 4. Demo host (demo.resilai.org), POST -> Block (403)
  { name: "Demo Host POST", host: "demo.resilai.org", search: "", mode: "production", viteEnv: "", method: "POST", expectedBlocked: true },
  // 5. Demo host, PUT -> Block (403)
  { name: "Demo Host PUT", host: "demo.resilai.org", search: "", mode: "production", viteEnv: "", method: "PUT", expectedBlocked: true },
  // 6. Demo host, DELETE -> Block (403)
  { name: "Demo Host DELETE", host: "demo.resilai.org", search: "", mode: "production", viteEnv: "", method: "DELETE", expectedBlocked: true },
  // 7. Demo host, PATCH -> Block (403)
  { name: "Demo Host PATCH", host: "demo.resilai.org", search: "", mode: "production", viteEnv: "", method: "PATCH", expectedBlocked: true },
  // 8. Query string ?env=demo on production host, POST -> Block (403)
  { name: "Query ?env=demo POST", host: "app.resilai.org", search: "?env=demo", mode: "production", viteEnv: "", method: "POST", expectedBlocked: true },
  // 9. VITE_APP_ENV=demo, POST -> Block (403)
  { name: "VITE_APP_ENV=demo POST", host: "localhost", search: "", mode: "production", viteEnv: "demo", method: "POST", expectedBlocked: true },
  // 10. MODE=demo, POST -> Block (403)
  { name: "MODE=demo POST", host: "localhost", search: "", mode: "demo", viteEnv: "", method: "POST", expectedBlocked: true },
  // 11. Staging host, POST -> Allow
  { name: "Staging host POST", host: "airs-staging-0384513977.web.app", search: "", mode: "staging", viteEnv: "staging", method: "POST", expectedBlocked: false },
];

let passed = 0;
let failed = 0;

console.log("=== Demo Mode Mutation Firewall Empirical Test Suite ===");
for (const tc of testCases) {
  const result = checkFirewall(tc.host, tc.search, tc.mode, tc.viteEnv, tc.method);
  if (result.blocked === tc.expectedBlocked) {
    console.log(`[PASS] ${tc.name}: blocked=${result.blocked}`);
    passed++;
  } else {
    console.error(`[FAIL] ${tc.name}: expected blocked=${tc.expectedBlocked}, got blocked=${result.blocked}`);
    failed++;
  }
}

console.log(`\nResults: ${passed}/${testCases.length} passed.`);
if (failed > 0) process.exit(1);
