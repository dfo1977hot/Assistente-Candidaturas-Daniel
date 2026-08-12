from sqlalchemy import create_engine, inspect

from acd.database.create_database import create_database


def test_follow_up_schema_evolution_is_additive_and_idempotent(tmp_path):
    target = create_engine(f"sqlite:///{tmp_path / 'follow-up.db'}")
    create_database(target)
    create_database(target)

    inspector = inspect(target)
    application_columns = {item["name"] for item in inspector.get_columns("applications")}
    timeline_columns = {item["name"] for item in inspector.get_columns("timeline_events")}

    assert {
        "next_action",
        "follow_up_time",
        "follow_up_priority",
        "follow_up_note",
    } <= application_columns
    assert {"origin", "reference_type", "reference_id"} <= timeline_columns
