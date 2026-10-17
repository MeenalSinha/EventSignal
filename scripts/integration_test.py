#!/usr/bin/env python3
"""End-to-end integration check (cross-platform).

Starts the real backend on a free port with a throwaway database, verifies the health
endpoint and CORS over real HTTP, runs the real React app against it (and against a
dead port) via Vitest, then verifies that stopping the database path breaks health.
The developer's real database and .env are never touched.

Usage (from the repository root, with the backend virtualenv created):
    backend/.venv/bin/python scripts/integration_test.py          # macOS / Linux
    backend\\.venv\\Scripts\\python scripts\\integration_test.py    # Windows
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
ORIGIN = "http://localhost:5173"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def get(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status, dict(response.headers), response.read()
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers), error.read()


def wait_for(url: str, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            get(url)
            return
        except OSError:
            time.sleep(0.3)
    raise RuntimeError(f"Backend did not start within {timeout}s")


def check(condition: bool, label: str) -> None:
    print(f"  [{'PASS' if condition else 'FAIL'}] {label}")
    if not condition:
        raise SystemExit(f"Integration check failed: {label}")


def main() -> int:
    npm = shutil.which("npm")
    if npm is None:
        print("npm was not found on PATH", file=sys.stderr)
        return 2

    port, dead_port = free_port(), free_port()
    base = f"http://127.0.0.1:{port}"
    tmp = Path(tempfile.mkdtemp(prefix="eventsignal-it-"))
    env = {
        **os.environ,
        "APP_ENV": "test",
        "APP_VERSION": "integration-1.2.3",
        "BACKEND_HOST": "127.0.0.1",
        "BACKEND_PORT": str(port),
        "DATABASE_URL": f"sqlite:///{(tmp / 'it' / 'integration.db').as_posix()}",
        "CORS_ORIGINS": ORIGIN,
        "LOG_LEVEL": "WARNING",
    }
    server = subprocess.Popen([sys.executable, "-m", "app"], cwd=BACKEND, env=env)
    try:
        print("Backend")
        wait_for(f"{base}/api/v1/health")

        status, _, body = get(f"{base}/api/v1/health")
        health = json.loads(body)
        check(status == 200 and health["status"] == "healthy", "health returns 200 healthy")
        check(health["version"] == "integration-1.2.3", "version comes from configuration")
        check(health["components"]["database"]["status"] == "ok", "database component is ok")
        check((tmp / "it" / "integration.db").exists(), "configured SQLite file and directory were created")

        status, _, body = get(f"{base}/api/v1/events")
        check(status == 200 and json.loads(body)["total"] == 0, "event database starts empty")

        _, headers, _ = get(f"{base}/api/v1/health", {"Origin": ORIGIN})
        check(headers.get("access-control-allow-origin") == ORIGIN, "CORS allows the configured origin")
        _, headers, _ = get(f"{base}/api/v1/health", {"Origin": "https://evil.example"})
        check("access-control-allow-origin" not in {k.lower() for k in headers}, "CORS rejects other origins")

        print("Frontend against live backend and a dead port")
        live_env = {**os.environ, "LIVE_API_URL": base, "LIVE_DEAD_URL": f"http://127.0.0.1:{dead_port}"}
        result = subprocess.run([npm, "run", "test:live"], cwd=FRONTEND, env=live_env)
        check(result.returncode == 0, "real React app: connected, empty state, and unreachable-backend state")

        print("Database failure is reported")
        server.terminate()
        server.wait(timeout=15)
        broken_dir = tmp / "broken-db"
        broken_dir.mkdir()
        env["DATABASE_URL"] = f"sqlite:///{broken_dir.as_posix()}"
        server = subprocess.Popen([sys.executable, "-m", "app"], cwd=BACKEND, env=env)
        wait_for(f"{base}/api/v1/health")
        status, _, body = get(f"{base}/api/v1/health")
        parsed = json.loads(body)
        check(status == 503 and parsed["status"] == "unhealthy", "unusable database yields 503 unhealthy")
        check(str(tmp) not in body.decode(), "failure response exposes no filesystem paths")
        check(b"Traceback" not in body, "failure response exposes no stack trace")
    finally:
        server.terminate()
        try:
            server.wait(timeout=15)
        except subprocess.TimeoutExpired:
            server.kill()
        shutil.rmtree(tmp, ignore_errors=True)

    print("All integration checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
