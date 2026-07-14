"""Global application settings."""

from __future__ import annotations

from dataclasses import dataclass

from acd.config.paths import DATABASE_DIR

DATABASE_FILE = DATABASE_DIR / "acd.db"
DATABASE_URL = f"sqlite:///{DATABASE_FILE}"


@dataclass(frozen=True)
class Settings:
    """Application settings."""

    APP_NAME: str = "Assistente de Candidaturas do Daniel"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = DATABASE_URL

    LOG_LEVEL: str = "INFO"

    DEFAULT_LANGUAGE: str = "pt-BR"

    DEFAULT_THEME: str = "light"

    AUTO_BACKUP: bool = True

    DEBUG: bool = False


settings = Settings()