"""Typed, environment-driven application settings.

All environment-dependent values (database URL, CORS origins, host, port,
version, ...) are declared here and nowhere else. The rest of the codebase
receives a ``Settings`` instance instead of reading ``os.environ``.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import urlparse

from pydantic import Field, ValidationError, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict
from sqlalchemy.engine import make_url

# Repository root, derived from this file's location (never a machine-specific path).
PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"

SQLITE_MEMORY_MARKERS = {None, "", ":memory:"}


class ConfigurationError(RuntimeError):
    """Raised when required configuration is missing or invalid."""


class Settings(BaseSettings):
    """Application settings loaded from the environment and the root ``.env`` file."""

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        # The root .env is shared with the frontend (VITE_* variables).
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="EventSignal", min_length=1)
    app_version: str = Field(default="0.1.0", min_length=1)
    app_env: Literal["development", "test", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    backend_host: str = Field(default="127.0.0.1", min_length=1)
    backend_port: int = Field(default=8000, ge=1, le=65535)
    backend_reload: bool = False

    # Relative SQLite paths are resolved against the repository root.
    database_url: str = "sqlite:///./data/eventsignal.db"

    # Comma-separated list in the environment, parsed into a list here.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    # Web retrieval & opportunity intake settings
    ingest_request_timeout_seconds: float = Field(default=10.0, ge=1.0, le=60.0)
    ingest_max_content_length_bytes: int = Field(default=5_000_000, ge=10_000, le=50_000_000)
    ingest_max_redirects: int = Field(default=5, ge=0, le=10)
    ingest_user_agent: str = Field(
        default="EventSignal-Bot/1.0 (+https://github.com/MeenalSinha/EventSignal)"
    )
    ingest_allowed_content_types: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["text/html", "application/xhtml+xml"]
    )
    ingest_allowed_ports: Annotated[list[int], NoDecode] = Field(default_factory=lambda: [80, 443])

    # Assessment policy path (configurable outside calculation functions)
    assessment_policy_path: str = Field(default="app/core/default_assessment_policy.json")

    @field_validator("ingest_allowed_content_types", mode="before")
    @classmethod
    def _split_content_types(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip().lower() for item in value.split(",") if item.strip()]
        return value

    @field_validator("ingest_allowed_ports", mode="before")
    @classmethod
    def _split_ports(cls, value: object) -> object:
        if isinstance(value, str):
            return [int(item.strip()) for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("cors_origins")
    @classmethod
    def _validate_origins(cls, origins: list[str]) -> list[str]:
        cleaned: list[str] = []
        for origin in origins:
            parsed = urlparse(origin)
            if parsed.scheme not in {"http", "https"} or not parsed.netloc:
                raise ValueError(
                    f"'{origin}' is not a valid origin; expected a value such as "
                    "http://localhost:5173 (wildcards are not accepted)"
                )
            if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
                raise ValueError(f"'{origin}' must not include a path, query or fragment")
            cleaned.append(f"{parsed.scheme}://{parsed.netloc}")
        return cleaned

    @field_validator("database_url")
    @classmethod
    def _validate_database_url(cls, value: str) -> str:
        try:
            make_url(value)
        except Exception as exc:  # sqlalchemy raises ArgumentError for malformed URLs
            raise ValueError("DATABASE_URL is not a valid SQLAlchemy URL") from exc
        return value

    @property
    def is_sqlite(self) -> bool:
        return make_url(self.database_url).get_backend_name() == "sqlite"

    @property
    def resolved_database_url(self) -> str:
        """Database URL with relative SQLite file paths anchored to the repo root."""
        url = make_url(self.database_url)
        if url.get_backend_name() != "sqlite" or url.database in SQLITE_MEMORY_MARKERS:
            return url.render_as_string(hide_password=False)
        path = Path(url.database or "")
        if not path.is_absolute():
            path = (PROJECT_ROOT / path).resolve()
        return url.set(database=path.as_posix()).render_as_string(hide_password=False)

    @property
    def sqlite_file_path(self) -> Path | None:
        """Filesystem path of the SQLite database file, or None for other backends."""
        url = make_url(self.resolved_database_url)
        if url.get_backend_name() != "sqlite" or url.database in SQLITE_MEMORY_MARKERS:
            return None
        return Path(url.database or "")


def _format_validation_error(error: ValidationError) -> str:
    lines = ["Invalid application configuration:"]
    for item in error.errors(include_input=False):
        name = ".".join(str(part) for part in item["loc"]).upper()
        lines.append(f"  - {name}: {item['msg']}")
    lines.append("Check your .env file against .env.example.")
    return "\n".join(lines)


def load_settings(**overrides: object) -> Settings:
    """Build settings, converting validation failures into a readable error."""
    try:
        return Settings(**overrides)  # type: ignore[arg-type]
    except ValidationError as exc:
        raise ConfigurationError(_format_validation_error(exc)) from exc


@lru_cache
def get_settings() -> Settings:
    """Process-wide settings instance used by the production entry point."""
    return load_settings()
