#!/usr/bin/env python3
"""Run every Phase 1 quality gate in order and print a pass/fail summary.

Usage (repository root):
    backend/.venv/bin/python scripts/verify.py            # macOS / Linux
    backend\\.venv\\Scripts\\python scripts\\verify.py      # Windows
Add --skip-integration to skip the live end-to-end check.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"


def main() -> int:
    npm = shutil.which("npm")
    if npm is None:
        print("npm was not found on PATH", file=sys.stderr)
        return 2
    py = sys.executable
    steps: list[tuple[str, list[str], Path]] = [
        ("Backend: ruff lint", [py, "-m", "ruff", "check", "."], BACKEND),
        ("Backend: ruff format check", [py, "-m", "ruff", "format", "--check", "."], BACKEND),
        ("Backend: mypy (strict)", [py, "-m", "mypy"], BACKEND),
        ("Backend: compile check", [py, "-m", "compileall", "-q", "app"], BACKEND),
        ("Backend: pytest", [py, "-m", "pytest", "-q"], BACKEND),
        ("Frontend: TypeScript (strict)", [npm, "run", "typecheck"], FRONTEND),
        ("Frontend: ESLint", [npm, "run", "lint"], FRONTEND),
        ("Frontend: component tests", [npm, "test"], FRONTEND),
        ("Frontend: production build", [npm, "run", "build"], FRONTEND),
    ]
    if "--skip-integration" not in sys.argv:
        steps.append(("Integration: live backend + frontend", [py, "scripts/integration_test.py"], ROOT))

    results: list[tuple[str, bool]] = []
    for name, command, cwd in steps:
        print(f"\n=== {name} ===", flush=True)
        ok = subprocess.run(command, cwd=cwd).returncode == 0
        results.append((name, ok))

    print("\n=== Summary ===")
    for name, ok in results:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")
    return 0 if all(ok for _, ok in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
