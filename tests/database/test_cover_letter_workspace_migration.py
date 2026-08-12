from pathlib import Path


def test_cover_letter_workspace_schema_is_evolved_at_bootstrap() -> None:
    source = Path("acd/database/create_database.py").read_text(encoding="utf-8")
    assert "_ensure_cover_letter_columns(selected_engine)" in source
    for column in (
        "job_id",
        "application_id",
        "letter_type",
        "language",
        "tone",
        "length",
        "subject",
        "status",
        "notes",
        "updated_at",
    ):
        assert f'"{column}"' in source
