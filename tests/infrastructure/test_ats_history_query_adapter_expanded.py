"""Tests for expanded persisted ATS history projections."""

from __future__ import annotations

from dataclasses import asdict
import json
import tempfile

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import acd.database.database as database_module
from acd.domain.entities.ats_score import ATSScore
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job import Job
from acd.domain.entities.job_profile import JobProfile
from acd.domain.entities.recommendation import Recommendation
from acd.domain.entities.score_detail import ScoreDetail
from acd.domain.entities.skill_gap import SkillGap
from acd.infrastructure.query_adapters.ats_history_query_adapter import ATSHistoryQueryAdapter
from acd.infrastructure.repositories.ats_repository import ATSRepository
from acd.models.base import Base


@pytest.fixture
def ats_adapter_database(monkeypatch):
    """Provide an isolated database for persisted ATS read projections."""
    temp_dir = tempfile.mkdtemp(prefix="acd-ats-adapter-", dir=".")
    engine = create_engine(f"sqlite:///{temp_dir}/ats_adapter.db", future=True)
    session_local = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "SessionLocal", session_local)
    Base.metadata.create_all(bind=engine)

    try:
        yield session_local
    finally:
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_adapter_projects_complete_persisted_ats_analysis(ats_adapter_database) -> None:
    """All persisted ATS records are represented without executing analysis."""
    with ats_adapter_database() as session:
        curriculum = Curriculum(name="Daniel", version="v2", description="Python")
        job = Job(title="Backend Engineer", company_id=1, notes="Remote")
        session.add_all((curriculum, job))
        session.flush()
        curriculum_id = curriculum.id
        job_id = job.id
        profile = JobProfile(
            job_id=job.id,
            raw_description="Python and Docker",
            keywords="Python,Docker",
        )
        session.add(profile)
        session.flush()
        score = ATSScore(curriculum_id=curriculum.id, job_profile_id=profile.id, total_score=82.0)
        session.add(score)
        session.flush()
        session.add_all(
            (
                ScoreDetail(score_id=score.id, criterion="technical", score=32.0, max_score=40.0, weight=0.4),
                SkillGap(score_id=score.id, skill_name="Docker", gap_type="missing"),
                SkillGap(score_id=score.id, skill_name="Kubernetes", gap_type="desired"),
                Recommendation(score_id=score.id, message="Add Docker", recommendation_type="rule"),
            )
        )
        session.commit()

    result = ATSHistoryQueryAdapter(ATSRepository()).get_latest_for_curriculum(curriculum_id)

    assert result is not None
    assert result.curriculum_version == "v2"
    assert result.job_id == job_id
    assert result.job_title == "Backend Engineer"
    assert result.job_profile_keywords == ("Python", "Docker")
    assert result.gaps is not None
    assert result.gaps[0].skill_name == "Docker"
    assert result.recommendations is not None
    assert result.recommendations[0].message == "Add Docker"
    assert result.score_details is not None
    assert result.score_details[0].criterion == "technical"
    assert result.matched_competencies is None
    assert result.missing_competencies == ("Docker",)
    json.dumps(asdict(result), default=str)


def test_adapter_returns_none_for_unpersisted_analysis_data(ats_adapter_database) -> None:
    """Absent related rows remain absent instead of being inferred."""
    with ats_adapter_database() as session:
        curriculum = Curriculum(name="Daniel", version="v1", description="Python")
        session.add(curriculum)
        session.flush()
        curriculum_id = curriculum.id
        session.add(ATSScore(curriculum_id=curriculum.id, total_score=50.0))
        session.commit()

    result = ATSHistoryQueryAdapter(ATSRepository()).get_latest_for_curriculum(curriculum_id)

    assert result is not None
    assert result.curriculum_version == "v1"
    assert result.gaps is None
    assert result.recommendations is None
    assert result.score_details is None
    assert result.job_id is None
    assert result.job_profile_keywords is None
    assert result.missing_competencies is None
    assert ATSHistoryQueryAdapter(ATSRepository()).get_latest_for_curriculum(999) is None
