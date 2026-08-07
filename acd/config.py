"""
Configurações globais do sistema
"""

from acd.config.paths import DATA_DIR, LOG_DIR, ROOT_DIR as BASE_DIR
from acd.database.local_state import resolve_database_path

__all__ = [
    "BASE_DIR",
    "CARTAS_DIR",
    "CURRICULOS_DIR",
    "DATABASE_DIR",
    "DATABASE_FILE",
    "DATA_DIR",
    "LOG_DIR",
]

DATABASE_FILE = resolve_database_path()
DATABASE_DIR = DATABASE_FILE.parent
CURRICULOS_DIR = DATA_DIR / "curriculos"
CARTAS_DIR = DATA_DIR / "cartas"
