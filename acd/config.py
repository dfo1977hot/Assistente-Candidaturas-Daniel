"""
Configurações globais do sistema
"""
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATABASE_DIR = DATA_DIR / "database"
DATABASE_FILE = DATABASE_DIR / "acd.db"
LOG_DIR = DATA_DIR / "logs"
CURRICULOS_DIR = DATA_DIR / "curriculos"
CARTAS_DIR = DATA_DIR / "cartas"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)
CURRICULOS_DIR.mkdir(parents=True, exist_ok=True)
CARTAS_DIR.mkdir(parents=True, exist_ok=True)