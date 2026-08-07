"""Read-only contracts shared by Application composition services."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.structured_resume_snapshot import StructuredResumeSnapshot


@dataclass(frozen=True)
class ApplicationContext:
    """Read-only view of an application and its related history."""

    application_id: int
    job_id: int
    company_id: int
    status: str
    curriculum_id: int | None = None
    selected_resume_version_id: int | None = None
    resume_source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL
    history: tuple[Mapping[str, Any], ...] = ()


@dataclass(frozen=True)
class VacancyContext:
    """Read-only view of a job used by composition flows."""

    job_id: int
    title: str
    competencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class CompanyContext:
    """Read-only view of a company used by composition flows."""

    company_id: int
    name: str
    segment: str = ""


@dataclass(frozen=True)
class ResumeContext:
    """Read-only view of the curriculum used in an application."""

    curriculum_id: int
    version: str
    description: str
    structured_resume: StructuredResumeSnapshot | None = None


@dataclass(frozen=True)
class ATSContext:
    """Reusable representation of an available ATS result."""

    total_score: float
    recommendations: tuple[str, ...] = ()
    details: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class GapContext:
    """Reusable representation of gaps derived from existing analysis."""

    missing_skills: tuple[str, ...] = ()
    desired_skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class InterviewContext:
    """Read-only context required by interview preparation consumers."""

    application: ApplicationContext
    vacancy: VacancyContext
    company: CompanyContext
    resume: ResumeContext | None
    identified_competencies: tuple[str, ...]
    ats_result: ATSContext | None
    gaps: GapContext | None
    related_history: tuple[Mapping[str, Any], ...] = ()
