import json
import subprocess
import sys

from sqlalchemy import create_engine, inspect, text

from acd.database.database_bootstrap import DatabaseBootstrap
from acd.database.model_registry import EXPECTED_ORM_TABLES


def test_bootstrap_creates_the_complete_schema_in_memory() -> None:
    engine = create_engine("sqlite:///:memory:")
    try:
        first = DatabaseBootstrap().initialize(engine)
        second = DatabaseBootstrap().initialize(engine)
        assert set(first.physical_tables) == EXPECTED_ORM_TABLES
        assert first == second
    finally:
        engine.dispose()


def test_bootstrap_is_idempotent_for_a_new_sqlite_file(tmp_path) -> None:
    path = tmp_path / "clean.db"
    engine = create_engine(f"sqlite:///{path}")
    try:
        DatabaseBootstrap().initialize(engine)
        DatabaseBootstrap().initialize(engine)
        assert path.exists()
        assert set(inspect(engine).get_table_names()) == EXPECTED_ORM_TABLES
    finally:
        engine.dispose()


def test_bootstrap_preserves_existing_data(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'existing.db'}")
    try:
        DatabaseBootstrap().initialize(engine)
        with engine.begin() as connection:
            connection.execute(text("INSERT INTO companies (name, segment, city, state, country, company_size, created_at, updated_at) VALUES ('Preserved', '', '', '', '', '', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"))
        DatabaseBootstrap().initialize(engine)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT count(*) FROM companies")) == 1
    finally:
        engine.dispose()


def test_clean_python_process_requires_explicit_registration_and_bootstraps(tmp_path) -> None:
    database_path = tmp_path / "clean-process.db"
    script = (
        "import json; from sqlalchemy import create_engine, inspect; "
        "from acd.models.base import Base; import acd.database.model_registry as registry; "
        "before=len(Base.metadata.tables); "
        f"engine=create_engine('sqlite:///{database_path.as_posix()}'); "
        "result=__import__('acd.database.database_bootstrap', fromlist=['DatabaseBootstrap']).DatabaseBootstrap().initialize(engine); "
        "print(json.dumps({'before': before, 'count': len(result.physical_tables), 'tables': list(result.physical_tables)})); engine.dispose()"
    )
    completed = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["before"] == 0
    assert payload["count"] == 92
    assert set(payload["tables"]) == EXPECTED_ORM_TABLES
