"""Read-only review of generated versions for an application's curriculum."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.composition.resume_context_service import ResumeContextService
from acd.application.query_ports import (
    GeneratedResumeVersionQueryDTO,
    GeneratedResumeVersionQueryPort,
)


class ResumeVersionReviewStatus(StrEnum):
    """Functional outcomes for a resume version review."""

    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_REQUIRED = "curriculum_required"
    NO_VERSIONS = "no_versions"
    VERSION_NOT_FOUND = "version_not_found"
    SUCCESS = "success"


@dataclass(frozen=True)
class ResumeVersionReviewResult:
    """Immutable data required to review versions for one curriculum."""

    status: ResumeVersionReviewStatus
    application_id: int
    curriculum_id: int | None = None
    original_content: str = ""
    versions: tuple[GeneratedResumeVersionQueryDTO, ...] = ()
    selected_version: GeneratedResumeVersionQueryDTO | None = None
    resume_source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL
    selected_resume_version_id: int | None = None


class ResumeVersionReviewUseCase:
    """Load persisted generated versions without creating or changing data."""

    def __init__(
        self,
        application_context_service: ApplicationContextService,
        resume_context_service: ResumeContextService,
        version_query_port: GeneratedResumeVersionQueryPort,
    ) -> None:
        self._applications = application_context_service
        self._resumes = resume_context_service
        self._versions = version_query_port

    def execute(
        self,
        application_id: int,
        selected_version_id: int | None = None,
    ) -> ResumeVersionReviewResult:
        """Return original content and versions belonging to the linked curriculum."""
        application = self._applications.build(application_id)
        if application is None:
            return ResumeVersionReviewResult(
                ResumeVersionReviewStatus.APPLICATION_NOT_FOUND,
                application_id,
            )
        if application.curriculum_id is None:
            return ResumeVersionReviewResult(
                ResumeVersionReviewStatus.CURRICULUM_REQUIRED,
                application_id,
            )

        resume = self._resumes.build(application.curriculum_id)
        if resume is None:
            return ResumeVersionReviewResult(
                ResumeVersionReviewStatus.CURRICULUM_REQUIRED,
                application_id,
                application.curriculum_id,
            )

        versions = self._versions.list_by_curriculum_id(application.curriculum_id)
        if not versions:
            return ResumeVersionReviewResult(
                ResumeVersionReviewStatus.NO_VERSIONS,
                application_id,
                application.curriculum_id,
                resume.description,
                resume_source=application.resume_source,
                selected_resume_version_id=application.selected_resume_version_id,
            )

        selected_version = self._select_version(versions, selected_version_id)
        if selected_version is None:
            return ResumeVersionReviewResult(
                ResumeVersionReviewStatus.VERSION_NOT_FOUND,
                application_id,
                application.curriculum_id,
                resume.description,
                versions,
                resume_source=application.resume_source,
                selected_resume_version_id=application.selected_resume_version_id,
            )
        return ResumeVersionReviewResult(
            ResumeVersionReviewStatus.SUCCESS,
            application_id,
            application.curriculum_id,
            resume.description,
            versions,
            selected_version,
            application.resume_source,
            application.selected_resume_version_id,
        )

    @staticmethod
    def _select_version(
        versions: tuple[GeneratedResumeVersionQueryDTO, ...],
        selected_version_id: int | None,
    ) -> GeneratedResumeVersionQueryDTO | None:
        if selected_version_id is None:
            return versions[-1]
        return next(
            (version for version in versions if version.version_id == selected_version_id),
            None,
        )
