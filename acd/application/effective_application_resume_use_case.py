"""Read-only resolution of the resume effectively selected for an application."""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.composition.application_context_service import ApplicationContextService
from acd.application.query_ports import GeneratedResumeVersionQueryPort, ResumeQueryPort
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
)


class EffectiveApplicationResumeStatus(StrEnum):
    """Functional outcomes of effective resume resolution."""

    SUCCESS = "success"
    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_REQUIRED = "curriculum_required"
    CURRICULUM_NOT_FOUND = "curriculum_not_found"
    SELECTED_VERSION_NOT_FOUND = "selected_version_not_found"
    SELECTED_VERSION_CURRICULUM_MISMATCH = "selected_version_curriculum_mismatch"
    SELECTION_INCONSISTENT = "selection_inconsistent"
    CONTENT_UNAVAILABLE = "content_unavailable"


@dataclass(frozen=True)
class EffectiveApplicationResumeRequest:
    """Request the persisted effective resume for one application."""

    application_id: int


@dataclass(frozen=True)
class EffectiveApplicationResumeResult:
    """Immutable Application-safe representation of the effective resume."""

    status: EffectiveApplicationResumeStatus
    application_id: int
    curriculum_id: int | None = None
    resume_source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL
    selected_resume_version_id: int | None = None
    effective_resume_version_id: int | None = None
    title: str = ""
    content: str = ""
    content_format: str = "plain_text"
    message: str = ""
    structured_resume: StructuredResumeSnapshot | None = None
    structured_content_status: StructuredResumeContentStatus = (
        StructuredResumeContentStatus.UNAVAILABLE
    )


class EffectiveApplicationResumeUseCase:
    """Resolve original or explicitly adopted content without changing persistence."""

    def __init__(
        self,
        application_context_service: ApplicationContextService,
        resume_query_port: ResumeQueryPort,
        generated_resume_version_query_port: GeneratedResumeVersionQueryPort,
    ) -> None:
        self._applications = application_context_service
        self._resumes = resume_query_port
        self._versions = generated_resume_version_query_port

    def execute(
        self,
        request: EffectiveApplicationResumeRequest,
    ) -> EffectiveApplicationResumeResult:
        """Return only the resume selected in the persisted application context."""
        application = self._applications.build(request.application_id)
        if application is None:
            return self._result(
                EffectiveApplicationResumeStatus.APPLICATION_NOT_FOUND,
                request.application_id,
                message="A candidatura selecionada não está disponível.",
            )
        if application.curriculum_id is None:
            return self._result(
                EffectiveApplicationResumeStatus.CURRICULUM_REQUIRED,
                application.application_id,
                message="A candidatura não possui currículo associado.",
            )

        resume = self._resumes.get_by_id(application.curriculum_id)
        if resume is None:
            return self._result(
                EffectiveApplicationResumeStatus.CURRICULUM_NOT_FOUND,
                application.application_id,
                application.curriculum_id,
                application.resume_source,
                application.selected_resume_version_id,
                message="O currículo associado à candidatura não está disponível.",
            )

        if application.resume_source is ApplicationResumeSource.ORIGINAL:
            return self._original_result(
                application.application_id,
                resume.curriculum_id,
                resume.description,
                resume.structured_resume,
                resume.structured_content_status,
            )
        if application.selected_resume_version_id is None:
            return self._result(
                EffectiveApplicationResumeStatus.SELECTION_INCONSISTENT,
                application.application_id,
                resume.curriculum_id,
                application.resume_source,
                message="A versão adotada da candidatura não foi informada.",
            )

        selected = next(
            (
                version
                for version in self._versions.list_by_curriculum_id(resume.curriculum_id)
                if version.version_id == application.selected_resume_version_id
            ),
            None,
        )
        if selected is None:
            return self._result(
                EffectiveApplicationResumeStatus.SELECTED_VERSION_NOT_FOUND,
                application.application_id,
                resume.curriculum_id,
                application.resume_source,
                application.selected_resume_version_id,
                message="A versão adotada não pertence ao currículo da candidatura.",
            )
        if selected.curriculum_id != resume.curriculum_id:
            return self._result(
                EffectiveApplicationResumeStatus.SELECTED_VERSION_CURRICULUM_MISMATCH,
                application.application_id,
                resume.curriculum_id,
                application.resume_source,
                application.selected_resume_version_id,
                message="A versão adotada pertence a outro currículo.",
            )
        if not selected.content:
            return self._result(
                EffectiveApplicationResumeStatus.CONTENT_UNAVAILABLE,
                application.application_id,
                resume.curriculum_id,
                application.resume_source,
                application.selected_resume_version_id,
                message="O conteúdo da versão adotada não está disponível.",
            )
        return replace(
            EffectiveApplicationResumeResult(
            EffectiveApplicationResumeStatus.SUCCESS,
            application.application_id,
            resume.curriculum_id,
            ApplicationResumeSource.RESUME_VERSION,
            application.selected_resume_version_id,
            selected.version_id,
            f"Versão {selected.version}",
            selected.content,
            "plain_text",
            "Esta é a versão efetivamente usada nesta candidatura.",
            ),
            structured_resume=selected.structured_resume,
            structured_content_status=selected.structured_content_status,
        )

    def _original_result(
        self,
        application_id: int,
        curriculum_id: int,
        content: str,
        structured_resume: StructuredResumeSnapshot | None,
        structured_content_status: StructuredResumeContentStatus,
    ) -> EffectiveApplicationResumeResult:
        if not content:
            return self._result(
                EffectiveApplicationResumeStatus.CONTENT_UNAVAILABLE,
                application_id,
                curriculum_id,
                ApplicationResumeSource.ORIGINAL,
                message="O conteúdo do currículo original não está disponível.",
            )
        return replace(
            EffectiveApplicationResumeResult(
            EffectiveApplicationResumeStatus.SUCCESS,
            application_id,
            curriculum_id,
            ApplicationResumeSource.ORIGINAL,
            None,
            None,
            "Currículo original",
            content,
            "plain_text",
            "Este é o currículo efetivamente usado nesta candidatura.",
            ),
            structured_resume=structured_resume,
            structured_content_status=structured_content_status,
        )

    @staticmethod
    def _result(
        status: EffectiveApplicationResumeStatus,
        application_id: int,
        curriculum_id: int | None = None,
        resume_source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL,
        selected_resume_version_id: int | None = None,
        message: str = "",
    ) -> EffectiveApplicationResumeResult:
        return EffectiveApplicationResumeResult(
            status,
            application_id,
            curriculum_id,
            resume_source,
            selected_resume_version_id,
            message=message,
        )
