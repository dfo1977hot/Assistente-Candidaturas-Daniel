import os
import tempfile

import pytest

from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.application.prompt.prompt_builder import PromptBuilder, PromptContext
from acd.infrastructure.ai.providers import MockAIProvider
from acd.services.ai_generation_service import ResumeGenerationService, CoverLetterGenerationService


@pytest.fixture
def ai_setup(monkeypatch):
    temp_dir = tempfile.mkdtemp(prefix="acd-ai-", dir=".")
    db_path = os.path.join(temp_dir, "test_acd_ai.db")
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

    import acd.domain.entities.curriculum
    import acd.domain.entities.curriculum_version
    import acd.domain.entities.job_profile
    import acd.domain.entities.job
    import acd.domain.entities.application
    import acd.domain.entities.ai_prompt
    import acd.domain.entities.ai_generation
    import acd.domain.entities.resume_version
    import acd.domain.entities.cover_letter_version
    import acd.domain.entities.generation_log
    import acd.domain.entities.prompt_template

    Base.metadata.drop_all(bind=database_module.engine)
    Base.metadata.create_all(bind=database_module.engine)

    yield

    Base.metadata.drop_all(bind=database_module.engine)


def test_prompt_builder_builds_resume_prompt(ai_setup):
    context = PromptContext(
        vacancy_title="Analista de Dados",
        vacancy_description="Vaga para analista com Power BI e SQL.",
        ats_score=82,
        missing_skills=["SAP", "Python"],
        curriculum_summary="Analista com Power BI, Excel e Lean.",
        professional_history="Experiência em análise e projetos.",
        user_goals="Quero crescer em dados e liderança.",
        language="pt-BR",
    )

    prompt = PromptBuilder().build_resume_prompt(context)

    assert "Analista de Dados" in prompt
    assert "82" in prompt
    assert "SAP" in prompt
    assert "pt-BR" in prompt


def test_mock_ai_provider_generates_content():
    provider = MockAIProvider()
    result = provider.generate_text(prompt="Prompt de teste", model="mock", temperature=0.2, max_tokens=200, language="pt-BR")

    assert "mock" in result.lower()
    assert "teste" in result.lower()


def test_resume_generation_service_creates_new_version(ai_setup):
    curriculum = Curriculum(name="Analista", description="Power BI, Excel, Lean")
    job_profile = JobProfile(job_id=1, raw_description="Vaga analista", skills="Power BI, SQL", technologies="Power BI", methodologies="Lean", languages="Inglês", certifications="", keywords="Power BI")
    service = ResumeGenerationService(provider=MockAIProvider())

    result = service.generate_resume(curriculum=curriculum, job_profile=job_profile, language="pt-BR")

    assert result["version"] == "v2.0"
    assert result["content"]
    assert result["explanation"]


def test_cover_letter_generation_service_persists_content(ai_setup):
    curriculum = Curriculum(name="Analista", description="Power BI, Excel, Lean")
    job_profile = JobProfile(job_id=1, raw_description="Vaga analista", skills="Power BI, SQL", technologies="Power BI", methodologies="Lean", languages="Inglês", certifications="", keywords="Power BI")
    service = CoverLetterGenerationService(provider=MockAIProvider())

    result = service.generate_cover_letter(curriculum=curriculum, job_profile=job_profile, language="pt-BR")

    assert result["content"]
    assert result["version"]
