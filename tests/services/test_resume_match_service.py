from __future__ import annotations

from types import SimpleNamespace

from acd.services.resume_match_service import ResumeMatchService


def _curriculum(description: str) -> SimpleNamespace:
    return SimpleNamespace(
        name="Currículo Logística",
        description=description,
        language="pt-BR",
        structured_content_json=None,
    )


def test_resume_match_uses_only_job_notes_as_vacancy_description() -> None:
    application = SimpleNamespace(
        job=SimpleNamespace(
            title="Desenvolvedor Python",
            description="Python Django FastAPI",
            notes="Gestão de transportes, indicadores, WMS e liderança.",
        ),
        notes="Conteúdo da candidatura que não deve participar da análise.",
    )

    result = ResumeMatchService().analyze(
        application=application,
        curriculum=_curriculum("Logística, transportes, indicadores e liderança."),
    )

    assert result.has_vacancy_description
    assert "transportes" in result.matched_keywords
    assert "wms" in result.missing_keywords
    assert "python" not in result.missing_keywords
    assert "django" not in result.missing_keywords


def test_resume_match_returns_current_and_adapted_indicators() -> None:
    application = SimpleNamespace(
        job=SimpleNamespace(
            notes="Logística transportes indicadores WMS liderança custos SAP Power BI",
        )
    )

    result = ResumeMatchService().analyze(
        application=application,
        curriculum=_curriculum(
            "Experiência em logística, transportes, indicadores, liderança, custos e SAP."
        ),
    )

    assert 0 < result.score <= result.adapted_score <= 99
    assert 0 < result.ats_score <= result.adapted_ats_score <= 99
    assert result.interview_probability_min <= result.interview_probability_max
    assert (
        result.adapted_interview_probability_min
        <= result.adapted_interview_probability_max
    )
    assert (
        result.adapted_interview_probability_max
        >= result.interview_probability_max
    )


def test_resume_match_does_not_use_title_when_job_notes_are_empty() -> None:
    application = SimpleNamespace(
        job=SimpleNamespace(
            title="Coordenador de Logística",
            description="Gestão de transportes e WMS",
            notes="",
        )
    )

    result = ResumeMatchService().analyze(
        application=application,
        curriculum=_curriculum("Logística transportes WMS"),
    )

    assert result.score == 0
    assert result.ats_score == 0
    assert not result.has_vacancy_description
