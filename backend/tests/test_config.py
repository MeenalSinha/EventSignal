from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from app.core.config import PROJECT_ROOT, ConfigurationError, Settings, load_settings


def test_defaults_load_without_env_file(make_settings: Callable[..., Settings]) -> None:
    s = load_settings(_env_file=None)
    assert s.app_env == "development"
    assert s.backend_port == 8000
    assert s.app_version
    assert s.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]
    assert make_settings().app_env == "test"


def test_environment_variables_override_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_PORT", "9123")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("CORS_ORIGINS", "https://a.example.org, http://localhost:3000/")
    s = load_settings(_env_file=None)
    assert s.backend_port == 9123
    assert s.app_version == "9.9.9"
    assert s.cors_origins == ["https://a.example.org", "http://localhost:3000"]


def test_env_file_is_read(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("APP_VERSION=7.7.7\nVITE_API_BASE_URL=http://x\n", encoding="utf-8")
    s = load_settings(_env_file=env_file)
    assert s.app_version == "7.7.7"  # VITE_* entries are ignored, not rejected


@pytest.mark.parametrize(
    ("variable", "value", "expected_name"),
    [
        ("BACKEND_PORT", "not-a-number", "BACKEND_PORT"),
        ("BACKEND_PORT", "70000", "BACKEND_PORT"),
        ("APP_ENV", "staging", "APP_ENV"),
        ("LOG_LEVEL", "LOUD", "LOG_LEVEL"),
        ("CORS_ORIGINS", "*", "CORS_ORIGINS"),
        ("CORS_ORIGINS", "http://ok.example,ftp://bad.example", "CORS_ORIGINS"),
        ("CORS_ORIGINS", "http://localhost:5173/some/path", "CORS_ORIGINS"),
        ("DATABASE_URL", "this is not a url", "DATABASE_URL"),
        ("APP_VERSION", "", "APP_VERSION"),
    ],
)
def test_invalid_configuration_is_rejected_with_readable_message(
    monkeypatch: pytest.MonkeyPatch, variable: str, value: str, expected_name: str
) -> None:
    monkeypatch.setenv(variable, value)
    with pytest.raises(ConfigurationError) as excinfo:
        load_settings(_env_file=None)
    message = str(excinfo.value)
    assert expected_name in message
    assert ".env.example" in message


def test_relative_sqlite_path_resolves_against_repo_root() -> None:
    s = load_settings(_env_file=None, database_url="sqlite:///./data/x.db")
    assert s.sqlite_file_path == (PROJECT_ROOT / "data" / "x.db").resolve()
    assert s.resolved_database_url.startswith("sqlite:///")


def test_absolute_and_memory_sqlite_urls(tmp_path: Path) -> None:
    absolute = tmp_path / "a.db"
    s = load_settings(_env_file=None, database_url=f"sqlite:///{absolute.as_posix()}")
    assert s.sqlite_file_path == absolute
    memory = load_settings(_env_file=None, database_url="sqlite://")
    assert memory.sqlite_file_path is None


def test_non_sqlite_url_has_no_file_path() -> None:
    s = load_settings(_env_file=None, database_url="postgresql://user:pw@db.example/app")
    assert not s.is_sqlite
    assert s.sqlite_file_path is None
