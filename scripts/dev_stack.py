#!/usr/bin/env python
"""Run the full local AIRS development stack."""

from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT / "frontend"


def _require_binary(name: str) -> None:
    if shutil.which(name):
        return
    print(f"ERROR: '{name}' was not found in PATH.", file=sys.stderr)
    raise SystemExit(1)


def _spawn(name: str, command: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    print(f"[dev] starting {name}: {' '.join(command)}")
    return subprocess.Popen(
        command,
        cwd=str(cwd),
        env=os.environ.copy(),
    )


def _terminate(proc: subprocess.Popen[bytes]) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


def main() -> int:
    _require_binary("npm")
    _require_binary("firebase")

    processes = [
        _spawn(
            "backend",
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            ROOT,
        ),
        _spawn(
            "frontend",
            ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "5173"],
            FRONTEND_DIR,
        ),
        _spawn(
            "auth-emulator",
            ["firebase", "emulators:start", "--only", "auth", "--project", "demo-airs"],
            ROOT,
        ),
    ]

    def shutdown(signum: int | None = None, frame: object | None = None) -> None:
        for proc in reversed(processes):
            _terminate(proc)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            for proc in processes:
                code = proc.poll()
                if code is None:
                    continue
                shutdown()
                return code
            time.sleep(0.5)
    except KeyboardInterrupt:
        shutdown()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
