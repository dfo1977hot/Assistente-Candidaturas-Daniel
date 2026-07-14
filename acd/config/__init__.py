"""Public configuration API."""

from __future__ import annotations

from acd.config.environment import (
    CURRENT_ENVIRONMENT,
    Environment,
)
from acd.config.feature_flags import (
    ENABLE_AI,
    ENABLE_ANALYTICS,
    ENABLE_API,
    ENABLE_LEARNING,
    ENABLE_PLANNER,
    ENABLE_PLUGINS,
    ENABLE_SUPERVISOR,
)
from acd.config.paths import (
    ACD_DIR,
    BACKUP_DIR,
    CONFIG_DIR,
    DATA_DIR,
    DATABASE_DIR,
    DOCS_DIR,
    EXPORT_DIR,
    LOG_DIR,
    REPORTS_DIR,
    ROOT_DIR,
    TEMP_DIR,
)
from acd.config.settings import (
    DATABASE_FILE,
    DATABASE_URL,
    Settings,
    settings,
)

__all__ = [
    "ACD_DIR",
    "BACKUP_DIR",
    "CONFIG_DIR",
    "CURRENT_ENVIRONMENT",
    "DATA_DIR",
    "DATABASE_DIR",
    "DOCS_DIR",
    "ENABLE_AI",
    "ENABLE_ANALYTICS",
    "ENABLE_API",
    "ENABLE_LEARNING",
    "ENABLE_PLANNER",
    "ENABLE_PLUGINS",
    "ENABLE_SUPERVISOR",
    "Environment",
    "EXPORT_DIR",
    "LOG_DIR",
    "REPORTS_DIR",
    "ROOT_DIR",
    "Settings",
    "TEMP_DIR",
    "DATABASE_FILE",
    "DATABASE_URL",
    "settings",
]