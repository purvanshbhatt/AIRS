#!/usr/bin/env bash
# Rotate the staging ENCRYPTION_SECRET out of the repo and into Secret Manager.
#
# What it does (no values are printed):
#   1. reads the current key from gcp/env.staging.yaml (the value that was committed)
#   2. generates a fresh 32-byte key
#   3. stores NEW -> secret ENCRYPTION_SECRET_STAGING, OLD -> ENCRYPTION_SECRET_STAGING_PREVIOUS
#   4. grants the Cloud Run runtime service account access to both
#   5. removes the plaintext line from gcp/env.staging.yaml
#   6. redeploys airs-api-staging binding both secrets (ENCRYPTION_SECRET_PREVIOUS lets
#      documents written under the old key keep decrypting; new writes use the new key)
#
# Usage: ./scripts/rotate_staging_encryption_secret.sh
set -euo pipefail
PROJECT_ID="${PROJECT_ID:-gen-lang-client-0384513977}"
REGION="${REGION:-us-central1}"
SERVICE="airs-api-staging"
cd "$(dirname "$0")/.."

OLD="$(python3 -c "import re;print(re.search(r'ENCRYPTION_SECRET: \"([^\"]+)\"', open('gcp/env.staging.yaml').read()).group(1))")"
NEW="$(python3 -c "from app.core.security.encryption import generate_encryption_key; print(generate_encryption_key())" | tail -1)"
[[ ${#NEW} -ge 40 ]] || { echo "key generation failed"; exit 1; }

SA="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(spec.template.spec.serviceAccountName)')"
SA="${SA:-$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')-compute@developer.gserviceaccount.com}"

for name in ENCRYPTION_SECRET_STAGING ENCRYPTION_SECRET_STAGING_PREVIOUS; do
  gcloud secrets describe "$name" --project "$PROJECT_ID" >/dev/null 2>&1 \
    || gcloud secrets create "$name" --project "$PROJECT_ID" --replication-policy=automatic >/dev/null
done
printf '%s' "$NEW" | gcloud secrets versions add ENCRYPTION_SECRET_STAGING --project "$PROJECT_ID" --data-file=- >/dev/null
printf '%s' "$OLD" | gcloud secrets versions add ENCRYPTION_SECRET_STAGING_PREVIOUS --project "$PROJECT_ID" --data-file=- >/dev/null
for name in ENCRYPTION_SECRET_STAGING ENCRYPTION_SECRET_STAGING_PREVIOUS; do
  gcloud secrets add-iam-policy-binding "$name" --project "$PROJECT_ID" \
    --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
done
unset OLD NEW
echo "Secrets stored: ENCRYPTION_SECRET_STAGING (new), ENCRYPTION_SECRET_STAGING_PREVIOUS (retired)."

python3 - <<'PY'
from pathlib import Path
import re
p = Path('gcp/env.staging.yaml'); s = p.read_text()
s2 = re.sub(r'ENCRYPTION_SECRET: "[^"]+"\n',
    '# ENCRYPTION_SECRET is bound from Secret Manager at deploy time:\n'
    '#   --set-secrets ENCRYPTION_SECRET=ENCRYPTION_SECRET_STAGING:latest,ENCRYPTION_SECRET_PREVIOUS=ENCRYPTION_SECRET_STAGING_PREVIOUS:latest\n'
    '# Never put the key value in this file again (the previous value was committed and has been rotated).\n', s)
p.write_text(s2)
print('gcp/env.staging.yaml scrubbed')
PY

bash scripts/deploy_cloud_run.sh --target staging --region "$REGION" --project "$PROJECT_ID" \
  --set-secrets "ENCRYPTION_SECRET=ENCRYPTION_SECRET_STAGING:latest,ENCRYPTION_SECRET_PREVIOUS=ENCRYPTION_SECRET_STAGING_PREVIOUS:latest"
gcloud run services update-traffic "$SERVICE" --to-latest --project "$PROJECT_ID" --region "$REGION" >/dev/null
echo "Done. Commit gcp/env.staging.yaml, and update the GitHub secret GCP_STAGING_SECRET_BINDINGS to:"
echo "  ENCRYPTION_SECRET=ENCRYPTION_SECRET_STAGING:latest,ENCRYPTION_SECRET_PREVIOUS=ENCRYPTION_SECRET_STAGING_PREVIOUS:latest"
