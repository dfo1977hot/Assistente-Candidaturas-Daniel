"""Use cases for selecting an existing resume version for an application."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from acd.application.application_resume_selection_port import ApplicationResumeSelectionPort
from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.query_ports import GeneratedResumeVersionQueryPort


class ResumeAdoptionStatus(StrEnum):
    """Functional outcomes of a resume-source selection request."""

    SUCCESS = "success"
    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_REQUIRED = "curriculum_required"
    VERSION_NOT_FOUND = "version_not_found"
    ALREADY_SELECTED = "already_selected"


@dataclass(frozen=True)
class AdoptResumeVersionRequest:
    """Request to select a generated resume version for an application."""

    application_id: int
    resume_version_id: int


@dataclass(frozen=True)
class UseOriginalResumeRequest:
    """Request to return an application to its original curriculum."""

    application_id: int


@dataclass(frozen=True)
class ResumeAdoptionResult:
    """Immutable result that exposes selection metadata but no resume content."""

    status: ResumeAdoptionStatus
    application_id: int
    curriculum_id: int | None
    resume_source: ApplicationResumeSource
    selected_resume_version_id: int | None
    message: str


class AdoptResumeVersionUseCase:
    """Validate and persist a generated resume version selected for an application."""

    def __init__(
        self,
        application_context_service: ApplicationContextService,
        generated_resume_version_query_port: GeneratedResumeVersionQueryPort,
        selection_port: ApplicationResumeSelectionPort,
    ) -> None:
        self._application_context_service = application_context_service
        self._generated_resume_version_query_port = generated_resume_version_query_port
        self._selection_port = selection_port

    def execute(self, request: AdoptResumeVersionRequest) -> ResumeAdoptionResult:
        """Select a version belonging to the application's base curriculum."""
        application = self._application_context_service.build(request.application_id)
        if application is None:
            return _result(
                ResumeAdoptionStatus.APPLICATION_NOT_FOUND,
                request.application_id,
                None,
                ApplicationResumeSource.ORIGINAL,
                None,
                "Application not found.",
            )
        if application.curriculum_id is None:
            return _result(
                ResumeAdoptionStatus.CURRICULUM_REQUIRED,
                application.application_id,
                None,
                application.resume_source,
                application.selected_resume_version_id,
                "Application requires a base curriculum.",
            )
        versions = self._generated_resume_version_query_port.list_by_curriculum_id(
            application.curriculum_id
        )
        if not any(version.version_id == request.resume_version_id for version in versions):
            return _result(
                ResumeAdoptionStatus.VERSION_NOT_FOUND,
                application.application_id,
                application.curriculum_id,
                application.resume_source,
                application.selected_resume_version_id,
                "Resume version was not found for the application's curriculum.",
            )
        if application.selected_resume_version_id == request.resume_version_id:
            return _result(
                ResumeAdoptionStatus.ALREADY_SELECTED,
                application.application_id,
                application.curriculum_id,
                ApplicationResumeSource.RESUME_VERSION,
                request.resume_version_id,
                "Resume version is already selected.",
            )
        self._selection_port.set_selected_resume_version(
            application.application_id, request.resume_version_id
        )
        return _result(
            ResumeAdoptionStatus.SUCCESS,
            application.application_id,
            application.curriculum_id,
            ApplicationResumeSource.RESUME_VERSION,
            request.resume_version_id,
            "Resume version selected.",
        )


class UseOriginalResumeUseCase:
    """Clear an application's selected generated resume version."""

    def __init__(
        self,
        application_context_service: ApplicationContextService,
        selection_port: ApplicationResumeSelectionPort,
    ) -> None:
        self._application_context_service = application_context_service
        self._selection_port = selection_port

    def execute(self, request: UseOriginalResumeRequest) -> ResumeAdoptionResult:
        """Return the application to the original curriculum idempotently."""
        application = self._application_context_service.build(request.application_id)
        if application is None:
            return _result(
                ResumeAdoptionStatus.APPLICATION_NOT_FOUND,
                request.application_id,
                None,
                ApplicationResumeSource.ORIGINAL,
                None,
                "Application not found.",
            )
        if application.selected_resume_version_id is not None:
            self._selection_port.clear_selected_resume_version(application.application_id)
        return _result(
            ResumeAdoptionStatus.SUCCESS,
            application.application_id,
            application.curriculum_id,
            ApplicationResumeSource.ORIGINAL,
            None,
            "Original resume selected.",
        )


def _result(
    status: ResumeAdoptionStatus,
    application_id: int,
    curriculum_id: int | None,
    resume_source: ApplicationResumeSource,
    selected_resume_version_id: int | None,
    message: str,
) -> ResumeAdoptionResult:
    """Create a result consistently across the two explicit commands."""
    return ResumeAdoptionResult(
        status=status,
        application_id=application_id,
        curriculum_id=curriculum_id,
        resume_source=resume_source,
        selected_resume_version_id=selected_resume_version_id,
        message=message,
    )
