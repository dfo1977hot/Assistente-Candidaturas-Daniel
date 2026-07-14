"""Tests for Experience entity."""

from __future__ import annotations

from datetime import date

from acd.domain.entities.experience import Experience


def test_experience_defaults() -> None:
    """Experience should initialize without persisted defaults."""

    experience = Experience()

    assert experience.company is None
    assert experience.role is None
    assert experience.start_date is None
    assert experience.end_date is None
    assert experience.description is None
    assert experience.skills_used is None
    assert experience.key_results is None
    assert experience.technologies_used is None


def test_experience_assign_attributes() -> None:
    """Experience should store assigned attributes."""

    experience = Experience(
        profile_id=1,
        company="Barentz Brasil",
        role="Analista de Logística Sênior",
        start_date=date(2025, 10, 1),
        end_date=date(2026, 4, 30),
        description="Responsável pela gestão logística.",
        skills_used="Power BI, Excel, Lean",
        key_results="Redução de custos de 15%",
        technologies_used="Power BI, SQL",
    )

    assert experience.profile_id == 1
    assert experience.company == "Barentz Brasil"
    assert experience.role == "Analista de Logística Sênior"
    assert experience.start_date == date(2025, 10, 1)
    assert experience.end_date == date(2026, 4, 30)
    assert experience.description == "Responsável pela gestão logística."
    assert experience.skills_used == "Power BI, Excel, Lean"
    assert experience.key_results == "Redução de custos de 15%"
    assert experience.technologies_used == "Power BI, SQL"


def test_experience_repr_without_id() -> None:
    """repr should support transient objects."""

    experience = Experience(
        company="Empresa ABC",
        role="Coordenador",
    )

    assert (
        repr(experience)
        == "Experience(id=None, company='Empresa ABC', role='Coordenador')"
    )


def test_experience_repr_with_id() -> None:
    """repr should expose identifier."""

    experience = Experience(
        company="Empresa ABC",
        role="Coordenador",
    )

    experience.id = 25

    assert (
        repr(experience)
        == "Experience(id=25, company='Empresa ABC', role='Coordenador')"
    )
