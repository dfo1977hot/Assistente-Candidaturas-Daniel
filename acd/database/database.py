from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import sessionmaker

from acd.database.local_state import resolve_database_path, sqlite_url

DATABASE_FILE = resolve_database_path()
DATABASE_URL = sqlite_url(DATABASE_FILE)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)


def enable_sqlite_foreign_keys(target_engine: Engine) -> None:
    """Enable SQLite foreign-key enforcement for every new engine connection."""
    if event.contains(target_engine, "connect", _enable_foreign_keys):
        return
    event.listen(target_engine, "connect", _enable_foreign_keys)


def _enable_foreign_keys(dbapi_connection: object, _connection_record: object) -> None:
    """Apply the SQLite pragma at DBAPI connection creation time."""
    cursor = dbapi_connection.cursor()  # type: ignore[attr-defined]
    try:
        cursor.execute("PRAGMA foreign_keys = ON")
    finally:
        cursor.close()


enable_sqlite_foreign_keys(engine)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)
