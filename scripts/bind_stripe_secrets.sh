#!/usr/bin/env bash
# Bind Stripe secrets to the ResilAI API on Cloud Run via Secret Manager.
#
# Prompts for each value with hidden input (nothing is echoed or logged),
# stores it as a Secret Manager secret version, grants the service account
# access, redeploys the service with --set-secrets and routes traffic to the
# new revision. Run it yourself; never paste live keys into chat or files.
#
# Usage:
#   ./scripts/bind_stripe_secrets.sh                 # production (airs-api)
#   ./scripts/bind_stripe_secrets.sh --target staging
set -euo pipefail

PROJECT_ID="${PROJECT_ID:-gen-lang-client-0384513977}"
REGION="${REGION:-us-central1}"
TARGET="production"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --target) TARGET="${2:-production}"; shift 2 ;;
    *) echo "Unknown flag: $1"; exit 1 ;;
  esac
done

case "$TARGET" in
  production) SERVICE="airs-api";         SUFFIX="";          EXPECT_KEY="sk_live_" ;;
  staging)    SERVICE="airs-api-staging"; SUFFIX="_STAGING";  EXPECT_KEY="sk_test_" ;;
  *) echo "target must be production or staging"; exit 1 ;;
esac

cd "$(dirname "$0")/.."

SA="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" \
      --format='value(spec.template.spec.serviceAccountName)')"
SA="${SA:-$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')-compute@developer.gserviceaccount.com}"
echo "Target: $TARGET  service: $SERVICE  project: $PROJECT_ID  runtime SA: $SA"
echo

# name | prompt | required prefix (empty = any)
SPECS=(
  "STRIPE_SECRET_KEY|Stripe secret key (${EXPECT_KEY}...)|${EXPECT_KEY}"
  "STRIPE_WEBHOOK_SECRET|Stripe webhook signing secret (whsec_...)|whsec_"
  "STRIPE_PRICE_DESIGN_PARTNER|Price ID for founding/design-partner \$149 monthly (price_...)|price_"
  "STRIPE_PRICE_GROWTH|Price ID for Growth \$399 monthly (price_...)|price_"
  "STRIPE_PRICE_ENTERPRISE|Price ID for Enterprise (price_...), Enter to skip|price_"
)

BINDINGS=()
for spec in "${SPECS[@]}"; do
  IFS='|' read -r NAME PROMPT PREFIX <<<"$spec"
  SECRET_NAME="${NAME}${SUFFIX}"
  exists="false"
  if gcloud secrets describe "$SECRET_NAME" --project "$PROJECT_ID" >/dev/null 2>&1; then exists="true"; fi

  printf '%s' "$PROMPT"
  if [[ "$exists" == "true" ]]; then printf ' [exists; Enter keeps current]'; fi
  printf ': '
  IFS= read -rs VALUE; echo
  VALUE="${VALUE//[[:space:]]/}"

  if [[ -z "$VALUE" ]]; then
    if [[ "$exists" == "true" ]]; then
      echo "  keeping existing $SECRET_NAME"
      BINDINGS+=("${NAME}=${SECRET_NAME}:latest")
    else
      echo "  skipped $NAME (no value, no existing secret)"
    fi
    continue
  fi
  if [[ -n "$PREFIX" && "$VALUE" != "$PREFIX"* ]]; then
    echo "  ERROR: $NAME must start with '$PREFIX'. Aborting before anything is stored."; exit 1
  fi

  if [[ "$exists" != "true" ]]; then
    gcloud secrets create "$SECRET_NAME" --project "$PROJECT_ID" --replication-policy=automatic >/dev/null
    echo "  created secret $SECRET_NAME"
  fi
  printf '%s' "$VALUE" | gcloud secrets versions add "$SECRET_NAME" --project "$PROJECT_ID" --data-file=- >/dev/null
  echo "  stored new version of $SECRET_NAME"
  gcloud secrets add-iam-policy-binding "$SECRET_NAME" --project "$PROJECT_ID" \
    --member="serviceAccount:${SA}" --role="roles/secretmanager.secretAccessor" >/dev/null
  BINDINGS+=("${NAME}=${SECRET_NAME}:latest")
  unset VALUE
done

if [[ "$TARGET" == "production" ]]; then
  BINDINGS+=("ENCRYPTION_SECRET=ENCRYPTION_SECRET:latest")
fi
if [[ ${#BINDINGS[@]} -eq 0 ]]; then echo "Nothing to bind."; exit 0; fi

SET_SECRETS="$(IFS=,; echo "${BINDINGS[*]}")"
echo
echo "Deploying $SERVICE with secret bindings: ${SET_SECRETS//:latest/}"
if [[ "$TARGET" == "production" ]]; then
  bash scripts/deploy_cloud_run.sh --target production --region "$REGION" --project "$PROJECT_ID" --set-secrets "$SET_SECRETS"
else
  bash scripts/deploy_cloud_run.sh --target staging --region "$REGION" --project "$PROJECT_ID" --set-secrets "$SET_SECRETS"
fi
gcloud run services update-traffic "$SERVICE" --to-latest --project "$PROJECT_ID" --region "$REGION" >/dev/null
echo "Traffic routed to latest revision."

URL="$(gcloud run services describe "$SERVICE" --project "$PROJECT_ID" --region "$REGION" --format='value(status.url)')"
echo
echo "Verify: $(curl -s --max-time 30 "$URL/api/billing/public-config" | head -c 160)"
echo
echo "Remaining Stripe dashboard steps:"
echo "  1. Webhook endpoint: https://api.resilai.org/api/billing/webhook (events: checkout.session.completed,"
echo "     customer.subscription.created/updated/deleted, invoice.payment_failed) using the whsec you just stored."
echo "  2. Customer Portal: enable invoice history, payment-method update, cancellation, and plan switching."
echo "  3. Optional: Stripe Tax registrations, then set STRIPE_AUTOMATIC_TAX=true in gcp/env.prod.yaml."
