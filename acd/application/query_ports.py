"""Read-only query contracts used by the Application Composition Layer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
)


@dataclass(frozen=True)
class ApplicationQueryDTO:
    """Read-only application data independent from persistence models."""

    application_id: int
    job_id: int
    company_id: int
    curriculum_id: int | None
    curriculum_version: str | None
    status: str
    selected_resume_version_id: int | None = None
    resume_source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL


@dataclass(frozen=True)
class ResumeQueryDTO:
    """Read-only curriculum data independent from persistence models."""

    curriculum_id: int
    name: str
    version: str
    language: str
    description: str
    structured_resume: StructuredResumeSnapshot | None = None
    structured_content_status: StructuredResumeContentStatus = (
        StructuredResumeContentStatus.UNAVAILABLE
    )


@dataclass(frozen=True)
class ResumeVersionQueryDTO:
    """Read-only curriculum version data independent from persistence models."""

    version_id: int
    curriculum_id: int
    version: str
    file_name: str
    created_at: datetime


@dataclass(frozen=True)
class GeneratedResumeVersionQueryDTO:
    """Read-only generated resume version independent from persistence models."""

    version_id: int
    curriculum_id: int
    version: str
    content: str
    explanation: str
    created_at: datetime
    structured_resume: StructuredResumeSnapshot | None = None
    structured_content_status: StructuredResumeContentStatus = (
        StructuredResumeContentStatus.UNAVAILABLE
    )


@dataclass(frozen=True)
class CompanyQueryDTO:
    """Read-only company data independent from persistence models."""

    company_id: int
    name: str
    segment: str


@dataclass(frozen=True)
class VacancyQueryDTO:
    """Read-only vacancy data independent from persistence models."""

    job_id: int
    title: str
    company_id: int
    notes: str
    requirements: str = ""
    competencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class ATSScoreDetailQueryDTO:
    """Persisted criterion breakdown for an ATS analysis."""

    criterion: str
    score: float
    max_score: float
    weight: float


@dataclass(frozen=True)
class ATSGapQueryDTO:
    """Persisted skill gap for an ATS analysis."""

    skill_name: str
    gap_type: str


@dataclass(frozen=True)
class ATSRecommendationQueryDTO:
    """Persisted recommendation for an ATS analysis."""

    message: str
    recommendation_type: str


@dataclass(frozen=True)
class ATSHistoryQueryDTO:
    """Read-only ATS history entry independent from persistence models."""

    score_id: int
    curriculum_id: int
    job_profile_id: int | None
    total_score: float
    calculated_at: datetime
    application_id: int | None = None
    curriculum_version: str | None = None
    job_id: int | None = None
    job_title: str | None = None
    job_profile_keywords: tuple[str, ...] | None = None
    gaps: tuple[ATSGapQueryDTO, ...] | None = None
    recommendations: tuple[ATSRecommendationQueryDTO, ...] | None = None
    score_details: tuple[ATSScoreDetailQueryDTO, ...] | None = None
    matched_competencies: tuple[str, ...] | None = None
    missing_competencies: tuple[str, ...] | None = None


@dataclass(frozen=True)
class InterviewQueryDTO:
    """Read-only interview data independent from persistence models."""

    interview_id: int
    application_id: int
    interview_date: datetime
    interview_type: str
    result: str


@dataclass(frozen=True)
class ApplicationHistoryQueryDTO:
    """Read-only application timeline entry."""

    event_type: str
    description: str
    created_at: datetime


class ApplicationQueryPort(Protocol):
    """Reads applications and their related history."""

    def get_by_id(self, application_id: int) -> ApplicationQueryDTO | None:
        """Return an application by identifier."""

    def list_history(self, application_id: int) -> tuple[ApplicationHistoryQueryDTO, ...]:
        """Return timeline entries related to an application."""


class ResumeQueryPort(Protocol):
    """Reads curricula."""

    def get_by_id(self, curriculum_id: int) -> ResumeQueryDTO | None:
        """Return a curriculum by identifier."""

    def list_versions(self, curriculum_id: int) -> tuple[ResumeVersionQueryDTO, ...]:
        """Return all available versions of a curriculum."""


class GeneratedResumeVersionQueryPort(Protocol):
    """Reads generated resume versions associated with one curriculum."""

    def list_by_curriculum_id(
        self, curriculum_id: int
    ) -> tuple[GeneratedResumeVersionQueryDTO, ...]:
        """Return generated versions for exactly one curriculum."""


class CompanyQueryPort(Protocol):
    """Reads companies."""

    def get_by_id(self, company_id: int) -> CompanyQueryDTO | None:
        """Return a company by identifier."""


class VacancyQueryPort(Protocol):
    """Reads vacancies."""

    def get_by_id(self, job_id: int) -> VacancyQueryDTO | None:
        """Return a vacancy by identifier."""


class ATSHistoryQueryPort(Protocol):
    """Reads ATS history associated with a curriculum."""

    def get_latest_for_curriculum(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        """Return the latest ATS entry for a curriculum."""


class InterviewQueryPort(Protocol):
    """Reads interviews associated with an application."""

    def list_by_application(self, application_id: int) -> tuple[InterviewQueryDTO, ...]:
        """Return interviews associated with an application."""
