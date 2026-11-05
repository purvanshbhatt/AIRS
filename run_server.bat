@echo off
set PYTHONPATH=P:\projects\AIRS
set ENV=local
set AUTH_REQUIRED=false
rem Generate a local key: py -c "from app.core.security.encryption import generate_encryption_key; print(generate_encryption_key())"
set ENCRYPTION_SECRET=
set PYTHONIOENCODING=utf-8
py -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --log-level warning
