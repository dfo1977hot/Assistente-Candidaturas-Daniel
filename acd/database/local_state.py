"""Resolution policy for the application's local SQLite state."""

from __future__ import annotations

import os
from pathlib import Path

DATABASE_PATH_ENV = "ACD_DATABASE_PATH"
APPLICATION_DIRECTORY_NAME = "ACD"
DATABASE_FILENAME = "acd.db"
PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_DATABASE_PATH = PROJECT_ROOT / "data" / "database" / DATABASE_FILENAME


def user_data_directory(*, environ: dict[str, str] | None = None) -> Path:
    """Return the per-user data directory without creating it."""
    values = os.environ if environ is None else environ
    base = values.get("LOCALAPPDATA")
    if base:
        return Path(base).expanduser().resolve() / APPLICATION_DIRECTORY_NAME
    return Path.home().resolve() / ".local" / "share" / APPLICATION_DIRECTORY_NAME


def official_database_path(*, environ: dict[str, str] | None = None) -> Path:
    """Return the canonical user-data database path without touching the filesystem."""
    return (user_data_directory(environ=environ) / "data" / DATABASE_FILENAME).resolve()


def resolve_database_path(
    override: str | os.PathLike[str] | None = None,
    *,
    environ: dict[str, str] | None = None,
    legacy_path: Path = LEGACY_DATABASE_PATH,
) -> Path:
    """Resolve an absolute database path without filesystem side effects."""
    values = os.environ if environ is None else environ
    configured = override or values.get(DATABASE_PATH_ENV)
    if configured:
        return Path(configured).expanduser().resolve()
    if legacy_path.is_file():
        return legacy_path.resolve()
    return official_database_path(environ=values)


def is_productive_database_path(
    candidate: str | os.PathLike[str] | Path,
    *,
    environ: dict[str, str] | None = None,
    legacy_path: Path = LEGACY_DATABASE_PATH,
) -> bool:
    """Return True when a path targets the legacy or official productive database."""
    values = os.environ if environ is None else environ
    resolved = Path(candidate).expanduser().resolve()
    productive_paths = {
        legacy_path.resolve(),
        official_database_path(environ=values),
    }
    return resolved in productive_paths


def ensure_non_productive_database_path(
    candidate: str | os.PathLike[str] | Path,
    *,
    environ: dict[str, str] | None = None,
    legacy_path: Path = LEGACY_DATABASE_PATH,
) -> Path:
    """Reject productive database paths and return the resolved safe path."""
    resolved = Path(candidate).expanduser().resolve()
    if is_productive_database_path(resolved, environ=environ, legacy_path=legacy_path):
        raise ValueError(f"Refusing to use productive database path: {resolved}")
    return resolved


def sqlite_url(database_path: Path) -> str:
    """Create a SQLAlchemy SQLite URL from an absolute path."""
    return f"sqlite:///{database_path.as_posix()}"


def prepare_database_directory(database_path: Path) -> None:
    """Create the parent only for an explicit runtime operation."""
    database_path.parent.mkdir(parents=True, exist_ok=True)
