"""Tests for Application entity."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from acd.domain.entities.application import Application


def test_application_defaults() -> None:
    """Application should initialize without persisted defaults."""

    application = Application()

    assert application.status is None
    assert application.curriculum_version is None
    assert application.application_channel is None
    assert application.recruiter_name is None
    assert application.recruiter_email is None
    assert application.recruiter_phone is None
    assert application.feedback is None
    assert application.notes is None


def test_application_assign_attributes() -> None:
    """Application should store assigned attributes."""

    application = Application(
        job_id=1,
        company_id=2,
        curriculum_id=3,
        curriculum_version="v2",
        cover_letter_id=4,
        status="Entrevista",
        application_date=date(2026, 7, 1),
        last_update=date(2026, 7, 2),
        next_follow_up=date(2026, 7, 5),
        response_date=date(2026, 7, 8),
        interview_date=date(2026, 7, 10),
        salary_expected=Decimal("18000.00"),
        salary_offered=Decimal("17500.00"),
        application_channel="LinkedIn",
        recruiter_name="Maria Silva",
        recruiter_email="maria@empresa.com",
        recruiter_phone="11999999999",
        feedback="Excelente perfil.",
        notes="Aguardar retorno.",
    )

    assert application.job_id == 1
    assert application.company_id == 2
    assert application.curriculum_id == 3
    assert application.curriculum_version == "v2"
    assert application.cover_letter_id == 4
    assert application.status == "Entrevista"

    assert application.application_date == date(2026, 7, 1)
    assert application.last_update == date(2026, 7, 2)
    assert application.next_follow_up == date(2026, 7, 5)
    assert application.response_date == date(2026, 7, 8)
    assert application.interview_date == date(2026, 7, 10)

    assert application.salary_expected == Decimal("18000.00")
    assert application.salary_offered == Decimal("17500.00")

    assert application.application_channel == "LinkedIn"
    assert application.recruiter_name == "Maria Silva"
    assert application.recruiter_email == "maria@empresa.com"
    assert application.recruiter_phone == "11999999999"
    assert application.feedback == "Excelente perfil."
    assert application.notes == "Aguardar retorno."


def test_application_repr_without_id() -> None:
    """repr should support transient objects."""

    application = Application()

    assert repr(application) == "<Application None>"


def test_application_repr_with_id() -> None:
    """repr should expose identifier."""

    application = Application()
    application.id = 99

    assert repr(application) == "<Application 99>"