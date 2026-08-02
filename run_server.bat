@echo off
set PYTHONPATH=P:\projects\AIRS
set ENV=local
set AUTH_REQUIRED=false
set ENCRYPTION_SECRET=test-secret-32-chars-aaaaaaaaaaaa
set PYTHONIOENCODING=utf-8
py -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level warning
