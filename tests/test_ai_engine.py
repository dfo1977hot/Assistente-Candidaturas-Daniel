import pytest

from acd.application.prompt.prompt_builder import PromptBuilder, PromptContext
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job_profile import JobProfile
from acd.infrastructure.ai.providers import MockAIProvider
from acd.services.ai_generation_service import (
    CoverLetterGenerationService,
    ResumeGenerationService,
)


@pytest.fixture
def ai_provider() -> MockAIProvider:
    """Mock provider compartilhado entre os testes."""
    return MockAIProvider()


def test_prompt_builder_builds_resume_prompt():
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


def test_mock_ai_provider_generates_content(ai_provider: MockAIProvider):
    result = ai_provider.generate_text(
        prompt="Prompt de teste",
        model="mock",
        temperature=0.2,
        max_tokens=200,
        language="pt-BR",
    )

    assert "mock" in result.lower()
    assert "teste" in result.lower()


def test_resume_generation_service_creates_new_version(
    ai_provider: MockAIProvider,
):
    curriculum = Curriculum(
        name="Analista",
        description="Power BI, Excel, Lean",
    )

    job_profile = JobProfile(
        job_id=1,
        raw_description="Vaga analista",
        skills="Power BI, SQL",
        technologies="Power BI",
        methodologies="Lean",
        languages="Inglês",
        certifications="",
        keywords="Power BI",
    )

    service = ResumeGenerationService(provider=ai_provider)

    result = service.generate_resume(
        curriculum=curriculum,
        job_profile=job_profile,
        language="pt-BR",
    )

    assert result["version"] == "v2.0"
    assert result["content"]
    assert result["explanation"]


def test_cover_letter_generation_service_persists_content(
    ai_provider: MockAIProvider,
):
    curriculum = Curriculum(
        name="Analista",
        description="Power BI, Excel, Lean",
    )

    job_profile = JobProfile(
        job_id=1,
        raw_description="Vaga analista",
        skills="Power BI, SQL",
        technologies="Power BI",
        methodologies="Lean",
        languages="Inglês",
        certifications="",
        keywords="Power BI",
    )

    service = CoverLetterGenerationService(provider=ai_provider)

    result = service.generate_cover_letter(
        curriculum=curriculum,
        job_profile=job_profile,
        language="pt-BR",
    )

    assert result["content"]
    assert result["version"]