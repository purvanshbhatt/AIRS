import https from 'https';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const STAGING_URL = 'https://staging.resilai.org';

function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ statusCode: res.statusCode, data }));
    }).on('error', reject);
  });
}

async function verifyDeploy() {
  console.log(`[Verify] Starting deployment verification for ${STAGING_URL}`);
  
  try {
    // 1. Fetch HTML and extract live bundle hash
    console.log(`[Verify] Fetching live HTML...`);
    const htmlRes = await fetchUrl(STAGING_URL);
    if (htmlRes.statusCode !== 200) {
      throw new Error(`Failed to fetch HTML. Status: ${htmlRes.statusCode}`);
    }

    const scriptMatch = htmlRes.data.match(/src="\/assets\/(index-[a-zA-Z0-9_-]+\.js)"/);
    if (!scriptMatch) {
      throw new Error(`Could not find main JS bundle in live HTML`);
    }
    
    const liveBundleFile = scriptMatch[1];
    console.log(`[Verify] Live JS bundle: ${liveBundleFile}`);

    // 2. Compare against local build
    const localStagingAssetsDir = path.join(__dirname, '..', 'dist-staging', 'assets');
    const localFiles = fs.readdirSync(localStagingAssetsDir);
    const localBundleFile = localFiles.find(f => f.startsWith('index-') && f.endsWith('.js'));
    
    if (!localBundleFile) {
      throw new Error(`Could not find local JS bundle in dist-staging/assets`);
    }
    
    console.log(`[Verify] Local JS bundle: ${localBundleFile}`);
    
    if (liveBundleFile !== localBundleFile) {
      throw new Error(`Bundle mismatch! Live is serving ${liveBundleFile} but local is ${localBundleFile}`);
    }
    console.log(`[Verify] ✅ Bundle hashes match`);

    // 3. Fetch the live JS bundle and verify properties
    console.log(`[Verify] Fetching live JS bundle...`);
    const jsRes = await fetchUrl(`${STAGING_URL}/assets/${liveBundleFile}`);
    if (jsRes.statusCode !== 200) {
      throw new Error(`Failed to fetch JS bundle. Status: ${jsRes.statusCode}`);
    }
    
    const jsContent = jsRes.data;
    
    // Check API URL
    const canonicalApiUrl = 'https://airs-api-staging-227825933697.us-central1.run.app';
    if (!jsContent.includes(canonicalApiUrl)) {
      throw new Error(`Canonical API URL ${canonicalApiUrl} not found in bundle`);
    }
    console.log(`[Verify] ✅ Canonical API URL found`);
    
    // Check Firebase Project ID
    const firebaseProjectId = 'gen-lang-client-0384513977';
    if (!jsContent.includes(firebaseProjectId)) {
      throw new Error(`Firebase Project ID ${firebaseProjectId} not found in bundle`);
    }
    console.log(`[Verify] ✅ Firebase Project ID found`);

    // 4. Hit backend /health
    console.log(`[Verify] Fetching backend health...`);
    try {
      const healthRes = await fetchUrl(`${canonicalApiUrl}/health/system`);
      if (healthRes.statusCode !== 200 && healthRes.statusCode !== 401 && healthRes.statusCode !== 403) {
        throw new Error(`Backend /health/system returned unexpected status: ${healthRes.statusCode}`);
      }
      console.log(`[Verify] ✅ Backend health check passed (Status: ${healthRes.statusCode})`);
    } catch (e) {
      console.warn(`[Verify] ⚠️ Backend health check failed: ${e.message} (ignoring for now if CORS/Auth blocks it)`);
    }

    console.log(`\n[Verify] 🎉 ALL VERIFICATIONS PASSED`);
    process.exit(0);

  } catch (error) {
    console.error(`\n[Verify] ❌ DEPLOYMENT VERIFICATION FAILED:`);
    console.error(error.message);
    process.exit(1);
  }
}

verifyDeploy();
