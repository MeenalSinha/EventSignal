"""Run the API with host, port and reload taken from settings: ``python -m app``."""

from __future__ import annotations

import sys

import uvicorn

from app.core.config import ConfigurationError, get_settings


def main() -> int:
    try:
        settings = get_settings()
    except ConfigurationError as exc:
        print(exc, file=sys.stderr)
        return 2
    uvicorn.run(
        "app.main:create_app",
        factory=True,
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.backend_reload,
        log_level=settings.log_level.lower(),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
