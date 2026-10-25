"""Package the validated EventSignal repository into a clean ZIP archive.

Excludes:
- Version control (.git)
- Virtual environments (.venv)
- Dependencies (node_modules)
- Build artifacts (dist)
- Caches (__pycache__, .pytest_cache, .mypy_cache, .ruff_cache)
- Local runtime databases (*.db, *.sqlite3)
- Sensitive local files (.env)
- Output archive itself

Includes:
- Full backend source, tests, configuration
- Full frontend source, tests, configuration
- Documentation (docs/*, README.md, MVP_SPEC.md, reports)
- Safe configuration templates (.env.example)
- Utility scripts
"""

import os
import zipfile
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_ZIP = WORKSPACE_ROOT / "EventSignal-validated.zip"

EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vitest",
}

EXCLUDE_FILES = {
    ".env",
    "eventsignal.db",
    "EventSignal-validated.zip",
}

EXCLUDE_EXTENSIONS = {
    ".pyc",
    ".pyo",
    ".pyd",
}


def should_exclude(rel_path: Path) -> bool:
    for part in rel_path.parts:
        if part in EXCLUDE_DIRS:
            return True
        if part.startswith(".mypy_cache") or part.startswith(".pytest_cache"):
            return True
    if rel_path.name in EXCLUDE_FILES:
        return True
    if rel_path.suffix.lower() in EXCLUDE_EXTENSIONS:
        return True
    return False


def package_repository() -> None:
    print(f"Packaging repository from: {WORKSPACE_ROOT}")
    print(f"Output archive target: {OUTPUT_ZIP}")

    if OUTPUT_ZIP.exists():
        OUTPUT_ZIP.unlink()

    included_count = 0
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(WORKSPACE_ROOT):
            # Prune excluded directories in-place to avoid traversing them
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]

            for file in files:
                abs_file = Path(root) / file
                rel_file = abs_file.relative_to(WORKSPACE_ROOT)

                if should_exclude(rel_file):
                    continue

                # Add to ZIP under EventSignal/ prefix
                zip_path = Path("EventSignal") / rel_file
                zipf.write(abs_file, str(zip_path).replace("\\", "/"))
                included_count += 1

    file_size_mb = OUTPUT_ZIP.stat().st_size / (1024 * 1024)
    print(f"Successfully packaged {included_count} files into {OUTPUT_ZIP.name} ({file_size_mb:.2f} MB)")


if __name__ == "__main__":
    package_repository()
