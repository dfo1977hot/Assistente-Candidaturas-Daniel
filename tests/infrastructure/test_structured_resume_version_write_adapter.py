"""Integration tests for atomic structured resume version persistence."""

from __future__ import annotations

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from acd.application.structured_resume_snapshot import (
    StructuredResumeSnapshotCodec,
    StructuredResumeValidationError,
)
from acd.application.structured_resume_version_generation import (
    CreateStructuredResumeVersionRequest,
)
import acd.database.database as database_module
from acd.database.database import enable_sqlite_foreign_keys
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.resume_version import ResumeVersion
from acd.infrastructure.repositories.structured_resume_version_write_adapter import (
    StructuredResumeVersionWriteAdapter,
)
from acd.models.base import Base


@pytest.fixture(autouse=True)
def temporary_database(tmp_path, monkeypatch):
    """Run adapter checks against a real file-backed SQLite transaction."""
    engine = create_engine(f"sqlite:///{tmp_path / 'structured_versions.db'}", future=True)
    enable_sqlite_foreign_keys(engine)
    session_local = sessionmaker(bind=engine, future=True)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "SessionLocal", session_local)
    Base.metadata.create_all(engine)
    try:
        yield session_local
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


def _snapshot():
    return StructuredResumeSnapshotCodec().from_payload(
        {
            "schema_version": 1,
            "identity": {"full_name": "Daniel", "professional_title": None, "location": None},
            "contact": {"email": None, "phone": None, "linkedin": None, "portfolio": None, "website": None},
            "summary": None, "skills": [], "experiences": [], "education": [],
            "certifications": [], "courses": [], "languages": [], "projects": [], "additional_sections": [],
        }
    )


def _curriculum(session_local) -> Curriculum:
    with session_local() as session:
        curriculum = Curriculum(name="Daniel", description="Base")
        session.add(curriculum)
        session.commit()
        session.refresh(curriculum)
        return curriculum


def test_adapter_persists_complete_canonical_version_and_increments_sequence(temporary_database) -> None:
    curriculum = _curriculum(temporary_database)
    adapter = StructuredResumeVersionWriteAdapter()
    request = CreateStructuredResumeVersionRequest(curriculum.id, "Daniel", _snapshot(), "Explanation")

    first = adapter.create_structured_resume_version(request)
    second = adapter.create_structured_resume_version(request)

    with temporary_database() as session:
        versions = list(session.scalars(select(ResumeVersion).order_by(ResumeVersion.id)))
        assert [item.version for item in versions] == ["v2.0", "v3.0"]
        assert versions[0].content == "Daniel"
        assert versions[0].explanation == "Explanation"
        assert StructuredResumeSnapshotCodec().loads(versions[0].structured_content_json) == _snapshot()
        assert versions[0].created_at is not None
        assert first.resume_version_id == versions[0].id
        assert second.resume_version_id == versions[1].id


def test_adapter_rolls_back_when_codec_rejects_snapshot(temporary_database) -> None:
    curriculum = _curriculum(temporary_database)
    adapter = StructuredResumeVersionWriteAdapter()
    invalid = object()

    with pytest.raises(StructuredResumeValidationError):
        adapter.create_structured_resume_version(
            CreateStructuredResumeVersionRequest(curriculum.id, "Daniel", invalid, "Explanation")
        )

    with temporary_database() as session:
        assert list(session.scalars(select(ResumeVersion))) == []
