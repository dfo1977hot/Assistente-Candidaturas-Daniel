"""Tests for Education entity."""

from __future__ import annotations

from datetime import date

from acd.domain.entities.education import Education


def test_education_defaults() -> None:
    """Education should initialize without persisted defaults."""

    education = Education()

    assert education.institution is None
    assert education.degree is None
    assert education.field is None
    assert education.start_date is None
    assert education.end_date is None
    assert education.description is None


def test_education_assign_attributes() -> None:
    """Education should store assigned attributes."""

    education = Education(
        profile_id=1,
        institution="Universidade Federal",
        degree="Engenharia de Produção",
        field="Engenharia",
        start_date=date(2015, 2, 1),
        end_date=date(2019, 12, 15),
        description="Curso de graduação em Engenharia de Produção.",
    )

    assert education.profile_id == 1
    assert education.institution == "Universidade Federal"
    assert education.degree == "Engenharia de Produção"
    assert education.field == "Engenharia"
    assert education.start_date == date(2015, 2, 1)
    assert education.end_date == date(2019, 12, 15)
    assert (
        education.description
        == "Curso de graduação em Engenharia de Produção."
    )


def test_education_repr_without_id() -> None:
    """repr should support transient objects."""

    education = Education(
        institution="Universidade Federal",
        degree="Engenharia",
    )

    assert (
        repr(education)
        == "Education(id=None, institution='Universidade Federal', degree='Engenharia')"
    )


def test_education_repr_with_id() -> None:
    """repr should expose identifier."""

    education = Education(
        institution="Universidade Federal",
        degree="Engenharia",
    )

    education.id = 12

    assert (
        repr(education)
        == "Education(id=12, institution='Universidade Federal', degree='Engenharia')"
    )