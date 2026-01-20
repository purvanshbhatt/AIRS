# Cloud SQL PostgreSQL Setup for AIRS

This guide covers setting up Cloud SQL PostgreSQL for AIRS on Cloud Run.

## Prerequisites

- Google Cloud project with billing enabled
- `gcloud` CLI installed and authenticated
- Cloud Run API enabled

## Quick Start

### 1. Create Cloud SQL Instance

```bash
# Set variables
export PROJECT_ID="gen-lang-client-0384513977"
export REGION="us-central1"
export INSTANCE_NAME="airs-db"
export DB_NAME="airs"
export DB_USER="airs_user"

# Create PostgreSQL instance
gcloud sql instances create $INSTANCE_NAME \
    --database-version=POSTGRES_15 \
    --tier=db-f1-micro \
    --region=$REGION \
    --storage-type=SSD \
    --storage-size=10GB \
    --availability-type=zonal

# Create database
gcloud sql databases create $DB_NAME --instance=$INSTANCE_NAME

# Create user (you'll be prompted for password)
gcloud sql users create $DB_USER \
    --instance=$INSTANCE_NAME \
    --password=YOUR_SECURE_PASSWORD
```

### 2. Get Instance Connection Name

```bash
gcloud sql instances describe $INSTANCE_NAME --format="value(connectionName)"
# Output: gen-lang-client-0384513977:us-central1:airs-db
```

### 3. Configure DATABASE_URL

Add to `gcp/env.prod`:

```bash
# Unix socket connection (recommended for Cloud Run)
DATABASE_URL=postgresql://airs_user:YOUR_PASSWORD@/airs?host=/cloudsql/gen-lang-client-0384513977:us-central1:airs-db
```

### 4. Deploy with Cloud SQL

```powershell
# PowerShell
$env:CLOUDSQL_INSTANCE = "gen-lang-client-0384513977:us-central1:airs-db"
.\scripts\deploy_cloud_run.ps1
```

```bash
# Bash
export CLOUDSQL_INSTANCE="gen-lang-client-0384513977:us-central1:airs-db"
./scripts/deploy_cloud_run.sh
```

Or specify directly:

```powershell
.\scripts\deploy_cloud_run.ps1 -CloudSqlInstance "gen-lang-client-0384513977:us-central1:airs-db"
```

## DATABASE_URL Formats

### Unix Socket (Recommended for Cloud Run)

Best performance, automatic SSL, no additional configuration:

```
postgresql://USER:PASSWORD@/DATABASE?host=/cloudsql/PROJECT:REGION:INSTANCE
```

**Example:**
```
postgresql://airs_user:secret123@/airs?host=/cloudsql/gen-lang-client-0384513977:us-central1:airs-db
```

### TCP Connection (Private IP)

For Cloud Run with VPC connector or external access:

```
postgresql://USER:PASSWORD@PRIVATE_IP:5432/DATABASE
```

**Example:**
```
postgresql://airs_user:secret123@10.10.10.5:5432/airs
```

### TCP via Cloud SQL Auth Proxy

For local development connecting to Cloud SQL:

```bash
# Start proxy
cloud-sql-proxy gen-lang-client-0384513977:us-central1:airs-db --port=5432

# DATABASE_URL
postgresql://airs_user:secret123@127.0.0.1:5432/airs
```

## Cloud Run Service Account Permissions

The Cloud Run service account needs the `Cloud SQL Client` role:

```bash
# Get default compute service account
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Grant Cloud SQL Client role
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SERVICE_ACCOUNT" \
    --role="roles/cloudsql.client"
```

## Production Recommendations

### Instance Sizing

| Workload | Tier | vCPUs | Memory |
|----------|------|-------|--------|
| Development | `db-f1-micro` | Shared | 614 MB |
| Light Production | `db-g1-small` | Shared | 1.7 GB |
| Production | `db-custom-2-4096` | 2 | 4 GB |
| High Traffic | `db-custom-4-8192` | 4 | 8 GB |

### High Availability

For production, enable high availability:

```bash
gcloud sql instances patch $INSTANCE_NAME \
    --availability-type=REGIONAL
```

### Automated Backups

```bash
gcloud sql instances patch $INSTANCE_NAME \
    --backup-start-time=03:00 \
    --enable-bin-log
```

### Connection Limits

Configure in `app/db/database.py` (already set):

```python
# Pool settings for Cloud Run
pool_size=5           # Base connections per instance
max_overflow=10       # Max additional connections
pool_recycle=1800     # Recycle every 30 min
pool_pre_ping=True    # Verify before use
```

**Note:** Cloud Run scales horizontally. With max 10 instances and 15 connections each,
you need at least 150 max connections on Cloud SQL (default is 100 for micro).

Check and update:
```bash
# Check current setting
gcloud sql instances describe $INSTANCE_NAME \
    --format="value(settings.databaseFlags)"

# Increase max connections
gcloud sql instances patch $INSTANCE_NAME \
    --database-flags=max_connections=200
```

## Running Migrations

### From Local (via Cloud SQL Proxy)

```bash
# Start proxy
cloud-sql-proxy gen-lang-client-0384513977:us-central1:airs-db --port=5432

# In another terminal, set DATABASE_URL and run migrations
export DATABASE_URL="postgresql://airs_user:password@127.0.0.1:5432/airs"
alembic upgrade head
```

### From Cloud Build

Add to `cloudbuild.yaml`:

```yaml
steps:
  - name: 'gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.8.0'
    entrypoint: /bin/sh
    args:
      - '-c'
      - |
        /cloud-sql-proxy ${PROJECT_ID}:${_REGION}:${_INSTANCE} &
        sleep 5
        pip install -r requirements.txt
        alembic upgrade head
    env:
      - 'DATABASE_URL=postgresql://airs_user:${_DB_PASSWORD}@127.0.0.1:5432/airs'
```

## Troubleshooting

### Connection Refused

1. Verify Cloud SQL instance is running:
   ```bash
   gcloud sql instances describe $INSTANCE_NAME --format="value(state)"
   ```

2. Check service account has `cloudsql.client` role

3. Verify `--add-cloudsql-instances` was set during deploy

### Authentication Failed

1. Check password doesn't contain special characters that need escaping
2. Verify user exists:
   ```bash
   gcloud sql users list --instance=$INSTANCE_NAME
   ```

### Connection Pool Exhausted

1. Check Cloud SQL connection limits
2. Reduce `pool_size` in database.py
3. Ensure connections are properly closed

### View Logs

```bash
# Cloud Run logs
gcloud run logs read airs-api --region=$REGION

# Cloud SQL logs
gcloud sql operations list --instance=$INSTANCE_NAME
```

## Cost Optimization

### Stop Instance When Not in Use

```bash
# Stop (for dev/test)
gcloud sql instances patch $INSTANCE_NAME --activation-policy=NEVER

# Start
gcloud sql instances patch $INSTANCE_NAME --activation-policy=ALWAYS
```

### Use Shared CPU for Dev

The `db-f1-micro` tier is ~$10/month, suitable for development.

## Security Best Practices

1. **Use strong passwords** - Generate with:
   ```bash
   openssl rand -base64 24
   ```

2. **Rotate passwords periodically**:
   ```bash
   gcloud sql users set-password $DB_USER \
       --instance=$INSTANCE_NAME \
       --password=NEW_PASSWORD
   ```

3. **Use Secret Manager for credentials**:
   ```bash
   echo -n "postgresql://user:pass@/db?host=/cloudsql/..." | \
       gcloud secrets create airs-database-url --data-file=-
   ```

4. **Enable SSL** for TCP connections (automatic for Unix socket)

5. **Use private IP** with VPC connector for additional security
