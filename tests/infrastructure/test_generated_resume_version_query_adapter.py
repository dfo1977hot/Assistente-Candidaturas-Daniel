"""Tests for read-only generated resume version queries."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from acd.application.structured_resume_snapshot import StructuredResumeContentStatus
from acd.infrastructure.query_adapters.generated_resume_version_query_adapter import (
    GeneratedResumeVersionQueryAdapter,
)


def test_adapter_preserves_content_and_isolates_the_requested_curriculum(monkeypatch) -> None:
    records = [
        SimpleNamespace(id=1, curriculum_id=10, version="v2.0", content="first", explanation="one", created_at=datetime(2026, 1, 1, tzinfo=UTC)),
        SimpleNamespace(id=2, curriculum_id=10, version="v3.0", content="second", explanation="two", created_at=datetime(2026, 1, 2, tzinfo=UTC)),
    ]

    class _Session:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def scalars(self, _): return SimpleNamespace(all=lambda: records)

    monkeypatch.setattr(
        "acd.infrastructure.query_adapters.generated_resume_version_query_adapter.database_module.SessionLocal",
        _Session,
    )

    versions = GeneratedResumeVersionQueryAdapter().list_by_curriculum_id(10)

    assert [version.version_id for version in versions] == [1, 2]
    assert versions[0].content == "first"
    assert versions[1].explanation == "two"
    assert versions[0].structured_content_status is StructuredResumeContentStatus.UNAVAILABLE


def test_adapter_keeps_text_and_reports_invalid_structured_content(monkeypatch) -> None:
    records = [
        SimpleNamespace(
            id=1,
            curriculum_id=10,
            version="v2.0",
            content="text remains available",
            explanation="",
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
            structured_content_json="{",
        )
    ]

    class _Session:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def scalars(self, _): return SimpleNamespace(all=lambda: records)

    monkeypatch.setattr(
        "acd.infrastructure.query_adapters.generated_resume_version_query_adapter.database_module.SessionLocal",
        _Session,
    )

    version = GeneratedResumeVersionQueryAdapter().list_by_curriculum_id(10)[0]

    assert version.content == "text remains available"
    assert version.structured_resume is None
    assert version.structured_content_status is StructuredResumeContentStatus.INVALID
