"""Global application settings."""

from __future__ import annotations

from dataclasses import dataclass

from acd.database.local_state import resolve_database_path, sqlite_url
from acd.version import get_version

DATABASE_FILE = resolve_database_path()
DATABASE_URL = sqlite_url(DATABASE_FILE)


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    APP_NAME: str = "Assistente de Candidaturas do Daniel"
    APP_VERSION: str = get_version()

    DATABASE_URL: str = DATABASE_URL

    LOG_LEVEL: str = "INFO"

    DEFAULT_LANGUAGE: str = "pt-BR"

    DEFAULT_THEME: str = "light"

    AUTO_BACKUP: bool = True

    DEBUG: bool = False


settings = Settings()
