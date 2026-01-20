"""
Gunicorn configuration for production deployment.

Usage:
    gunicorn -c gunicorn.conf.py app.main:app

Or with command line (Cloud Run):
    gunicorn -k uvicorn.workers.UvicornWorker app.main:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
"""

import os

# Bind to 0.0.0.0 and use PORT from environment (Cloud Run sets this)
bind = f"0.0.0.0:{os.environ.get('PORT', '8000')}"

# Worker configuration
# UvicornWorker provides async support for FastAPI
worker_class = "uvicorn.workers.UvicornWorker"

# Number of workers
# Cloud Run: Use 2 workers for better concurrency
# Formula: (2 x CPU cores) + 1, but Cloud Run typically has 1-2 vCPUs
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))

# Threads per worker (for sync workers, not used with UvicornWorker)
threads = 1

# Timeout for worker processes (seconds)
# Cloud Run has a default request timeout of 300s
timeout = 120

# Keep-alive timeout
keepalive = 5

# Graceful timeout for worker restart
graceful_timeout = 30

# Maximum requests per worker before restart (prevents memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "-"  # stdout
errorlog = "-"   # stderr
loglevel = os.environ.get("LOG_LEVEL", "info")

# Access log format
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Preload app for faster worker startup (shares app code between workers)
preload_app = True

# Forward proxy headers (Cloud Run uses a proxy)
forwarded_allow_ips = "*"
