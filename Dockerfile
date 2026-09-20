# =============================================================================
# ResilAI Multi-Cloud Backend Container (GCP Cloud Run & AWS App Runner/ECS)
#
# Non-negotiable: Single portable Docker image for both primary (GCP)
# and standby (AWS) environments. Runtime configuration controls provider mode.
# =============================================================================

# --- Stage 1: Build & Dependencies ---
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt


# --- Stage 2: Production Runtime ---
FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    ENV=prod \
    CLOUD_PROVIDER=gcp \
    PYTHONPATH=/app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install pre-built wheels
COPY --from=builder /build/wheels /wheels
COPY requirements.txt .
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Create non-root system user for least-privilege security
RUN groupadd -g 10001 resilai && \
    useradd -u 10001 -g resilai -s /bin/bash -m resilai && \
    chown -R resilai:resilai /app

# Copy application code with non-root ownership
COPY --chown=resilai:resilai . /app

USER resilai

EXPOSE 8000

# Health check probe for container orchestrators (App Runner, ECS, Kubernetes)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Production WSGI/ASGI entrypoint
CMD exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
