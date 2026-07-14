"""Centralized project paths."""

from __future__ import annotations

from pathlib import Path

# ============================================================================
# Project root
# ============================================================================

ROOT_DIR = Path(__file__).resolve().parents[2]

# ============================================================================
# Application directories
# ============================================================================

ACD_DIR = ROOT_DIR / "acd"
DATA_DIR = ROOT_DIR / "data"
LOG_DIR = ROOT_DIR / "logs"
DOCS_DIR = ROOT_DIR / "docs"
EXPORT_DIR = ROOT_DIR / "exports"
BACKUP_DIR = ROOT_DIR / "backups"
TEMP_DIR = ROOT_DIR / "temp"
CONFIG_DIR = ROOT_DIR / "config"

# ============================================================================
# Database
# ============================================================================

DATABASE_DIR = DATA_DIR / "database"

# ============================================================================
# Reports
# ============================================================================

REPORTS_DIR = EXPORT_DIR / "reports"

# ============================================================================
# Ensure directories exist
# ============================================================================

_DIRECTORIES = (
    DATA_DIR,
    DATABASE_DIR,
    LOG_DIR,
    DOCS_DIR,
    EXPORT_DIR,
    REPORTS_DIR,
    BACKUP_DIR,
    TEMP_DIR,
    CONFIG_DIR,
)

for directory in _DIRECTORIES:
    directory.mkdir(
        parents=True,
        exist_ok=True,
    )