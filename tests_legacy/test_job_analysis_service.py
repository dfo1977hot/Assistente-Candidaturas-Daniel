import os
import tempfile

import pytest

from acd.infrastructure.repositories.job_profile_repository import JobProfileRepository
from acd.services.job_analysis_service import JobAnalysisService


@pytest.fixture
def analysis_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-job-analysis-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd.db")
    monkeypatch.setattr(
        "acd.database.database.DATABASE_URL",
        f"sqlite:///{db_path}",
    )

    import acd.database.database as database_module

    database_module.engine.dispose()
    database_module.engine = database_module.create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        future=True,
    )
    database_module.SessionLocal = database_module.sessionmaker(
        bind=database_module.engine,
        autoflush=False,
        autocommit=False,
    )

    from acd.models.base import Base

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield JobAnalysisService(repository=JobProfileRepository())

    Base.metadata.drop_all(bind=database_module.engine)


def test_job_analysis_service_extracts_skills_and_metadata(analysis_setup):
    service = analysis_setup
    profile = service.analyze_job(
        job_id=1,
        raw_description="Vaga para Analista de Supply Chain com experiência em Power BI, Excel, SQL, Lean e Six Sigma. Requisitos: inglês avançado, certificado em Green Belt.",
    )

    assert profile is not None
    assert "Power BI" in profile.technologies
    assert "Lean" in profile.skills
    assert "Inglês" in profile.languages
    assert "Green Belt" in profile.certifications
    assert profile.seniority == "Pleno"


def test_job_analysis_service_gets_statistics(analysis_setup):
    service = analysis_setup
    service.analyze_job(
        job_id=1, raw_description="Vaga para analista de dados com Python, SQL e Power BI."
    )
    stats = service.get_statistics()
    assert stats["total_profiles"] >= 1
    assert "Python" in stats["top_skills"]
