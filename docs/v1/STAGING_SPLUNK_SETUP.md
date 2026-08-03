# Cloud Run Staging: Splunk Setup Guide

This guide details how to configure the Splunk Native integration for the ResilAI Sentinel staging environment.

## 1. Secret Manager Configuration

All Splunk credentials must be stored securely in Google Cloud Secret Manager. Do NOT hardcode tokens in the codebase.

Create the following secrets in your GCP project:
- `SENTINEL_SPLUNK_TOKEN` (or `SENTINEL_SPLUNK_USERNAME` and `SENTINEL_SPLUNK_PASSWORD` for basic auth)

## 2. Cloud Run Environment Variables

When deploying to Cloud Run Staging, bind the secrets and provide the routing environment variables:

```bash
gcloud run deploy airs-staging \
  --image=gcr.io/$PROJECT_ID/airs-staging:latest \
  --set-env-vars=SENTINEL_SPLUNK_HOST=splunk.staging.internal \
  --set-env-vars=SENTINEL_SPLUNK_HEC_PORT=8088 \
  --set-env-vars=SENTINEL_SPLUNK_MGMT_PORT=8089 \
  --set-env-vars=SENTINEL_SPLUNK_VERIFY_SSL=false \
  --set-secrets=SENTINEL_SPLUNK_TOKEN=projects/$PROJECT_ID/secrets/SENTINEL_SPLUNK_TOKEN:latest
```

## 3. Firewall and Networking Requirements

If connecting to an internal Splunk Enterprise instance:
- **Serverless VPC Access**: Cloud Run must be attached to a VPC connector.
- **Firewall Rules**: Allow TCP/8088 (HEC) and TCP/8089 (Management) inbound from the Serverless VPC Connector IP range to the Splunk Search Head.

## 4. Splunk Cloud Setup

If connecting to Splunk Cloud:
- Hostname will look like `https://<stack>.splunkcloud.com`.
- Port for Management API is typically 8089.
- Ensure the Cloud Run NAT IPs are allowlisted in the Splunk Cloud control panel under IP Allow Lists for the API.

