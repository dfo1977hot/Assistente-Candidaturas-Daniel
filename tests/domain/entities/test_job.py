"""Tests for Job entity."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from acd.domain.entities.job import Job


def test_job_defaults() -> None:
    """Job should initialize without persisted defaults."""

    job = Job()

    assert job.location is None
    assert job.work_model is None
    assert job.employment_type is None
    assert job.salary_min is None
    assert job.salary_max is None
    assert job.currency is None
    assert job.status is None
    assert job.source is None
    assert job.job_url is None
    assert job.recruiter is None
    assert job.application_deadline is None
    assert job.application_date is None
    assert job.priority is None
    assert job.notes is None


def test_job_assign_attributes() -> None:
    """Job should store assigned attributes."""

    job = Job(
        company_id=10,
        title="Coordenador de Logística",
        location="Guarulhos/SP",
        work_model="Híbrido",
        employment_type="CLT",
        salary_min=Decimal("15000.00"),
        salary_max=Decimal("18000.00"),
        currency="BRL",
        status="Aberta",
        source="LinkedIn",
        job_url="https://linkedin.com/job/123",
        recruiter="Maria Silva",
        application_deadline=date(2026, 8, 15),
        application_date=date(2026, 7, 10),
        priority=1,
        notes="Alta prioridade.",
    )

    assert job.company_id == 10
    assert job.title == "Coordenador de Logística"
    assert job.location == "Guarulhos/SP"
    assert job.work_model == "Híbrido"
    assert job.employment_type == "CLT"

    assert job.salary_min == Decimal("15000.00")
    assert job.salary_max == Decimal("18000.00")

    assert job.currency == "BRL"
    assert job.status == "Aberta"
    assert job.source == "LinkedIn"
    assert job.job_url == "https://linkedin.com/job/123"
    assert job.recruiter == "Maria Silva"

    assert job.application_deadline == date(2026, 8, 15)
    assert job.application_date == date(2026, 7, 10)

    assert job.priority == 1
    assert job.notes == "Alta prioridade."


def test_job_repr_without_id() -> None:
    """repr should support transient objects."""

    job = Job(
        company_id=1,
        title="Engenheiro de Produção",
    )

    assert (
        repr(job)
        == "<Job(id=None, title='Engenheiro de Produção', company_id=1, status=None)>"
    )


def test_job_repr_with_id() -> None:
    """repr should expose identifier."""

    job = Job(
        company_id=8,
        title="Supervisor",
        status="Fechada",
    )

    job.id = 99

    assert (
        repr(job)
        == "<Job(id=99, title='Supervisor', company_id=8, status='Fechada')>"
    )


def test_job_company_relationship_default() -> None:
    """Relationship attribute should exist."""

    job = Job()

    assert job.company is None