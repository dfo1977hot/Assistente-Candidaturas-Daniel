"""Tests for JobAnalysisService."""

from __future__ import annotations

from acd.services.job_analysis_service import JobAnalysisService


class FakeParser:
    """Fake text parser."""

    def parse(self, text: str) -> dict[str, list[str]]:
        return {
            "skills": ["Python", "Power BI"],
            "technologies": ["SQL"],
            "methodologies": ["Lean"],
            "languages": ["English"],
            "certifications": ["PMP"],
            "seniority": ["Senior"],
        }


class FakeRepository:
    """Fake repository."""

    def create(self, profile):
        profile.id = 123
        return profile

    def get_statistics(self):
        return {
            "jobs": 10,
            "profiles": 8,
        }


def create_service() -> JobAnalysisService:
    """Create service with fake dependencies."""

    service = JobAnalysisService(repository=FakeRepository())
    service.parser = FakeParser()
    return service


def test_analyze_job() -> None:
    """Should analyze and persist a job profile."""

    service = create_service()

    profile = service.analyze_job(
        job_id=5,
        raw_description=" Python Developer ",
    )

    assert profile is not None
    assert profile.id == 123
    assert profile.job_id == 5
    assert profile.raw_description == "Python Developer"

    assert profile.skills == "Python,Power BI"
    assert profile.technologies == "SQL"
    assert profile.methodologies == "Lean"
    assert profile.languages == "English"
    assert profile.certifications == "PMP"

    assert profile.seniority == "Senior"

    assert "Competências" in profile.structured_description
    assert "Tecnologias" in profile.structured_description


def test_get_statistics() -> None:
    """Should return repository statistics."""

    service = create_service()

    stats = service.get_statistics()

    assert stats == {
        "jobs": 10,
        "profiles": 8,
    }


def test_build_structured_description() -> None:
    """Should build formatted description."""

    service = create_service()

    description = service._build_structured_description(
        {
            "skills": ["Python"],
            "technologies": ["SQL"],
            "methodologies": ["Lean"],
            "languages": ["English"],
            "certifications": ["PMP"],
        }
    )

    assert "Competências: Python" in description
    assert "Tecnologias: SQL" in description
    assert "Metodologias: Lean" in description
    assert "Idiomas: English" in description
    assert "Certificações: PMP" in description


def test_build_structured_description_empty() -> None:
    """Should handle empty parser output."""

    service = create_service()

    description = service._build_structured_description({})

    assert "Competências: Nenhuma" in description
    assert "Tecnologias: Nenhuma" in description
    assert "Metodologias: Nenhuma" in description
    assert "Idiomas: Nenhum" in description
    assert "Certificações: Nenhuma" in description


def test_select_seniority() -> None:
    """Should select first seniority."""

    service = create_service()

    assert service._select_seniority(["Senior", "Specialist"]) == "Senior"


def test_select_seniority_empty() -> None:
    """Should return default seniority."""

    service = create_service()

    assert service._select_seniority([]) == "Não informada"