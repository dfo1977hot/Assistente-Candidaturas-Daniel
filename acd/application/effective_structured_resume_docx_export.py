"""Read-only export of an application's effective structured resume to DOCX."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from acd.application.application_resume_source import ApplicationResumeSource
from acd.application.effective_application_resume_use_case import (
    EffectiveApplicationResumeRequest,
    EffectiveApplicationResumeStatus,
    EffectiveApplicationResumeUseCase,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
)


class EffectiveStructuredResumeDocxExportStatus(StrEnum):
    """Functional outcomes of an explicit DOCX export."""

    SUCCESS = "success"
    APPLICATION_NOT_FOUND = "application_not_found"
    CURRICULUM_NOT_FOUND = "curriculum_not_found"
    ADOPTED_RESUME_VERSION_NOT_FOUND = "adopted_resume_version_not_found"
    STRUCTURED_CONTENT_REQUIRED = "structured_content_required"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    INVALID_DESTINATION = "invalid_destination"
    DESTINATION_NOT_WRITABLE = "destination_not_writable"
    EXPORT_FAILED = "export_failed"


@dataclass(frozen=True)
class ExportEffectiveStructuredResumeDocxRequest:
    """Explicit filesystem destination for one application's effective resume."""

    application_id: int
    destination_path: Path


@dataclass(frozen=True)
class ExportEffectiveStructuredResumeDocxResult:
    """Application-safe export outcome without document implementation details."""

    status: EffectiveStructuredResumeDocxExportStatus
    application_id: int
    destination_path: Path
    exported: bool
    message: str
    source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL
    curriculum_id: int | None = None
    resume_version_id: int | None = None


class StructuredResumeDocxExportPort(Protocol):
    """Export a validated snapshot without resolving application state."""

    def export(self, snapshot: StructuredResumeSnapshot, destination_path: Path) -> None:
        """Write a DOCX document to an already-authorized destination."""


class ExportEffectiveStructuredResumeDocxUseCase:
    """Resolve the effective snapshot and export it without domain persistence."""

    def __init__(
        self,
        effective_resume_use_case: EffectiveApplicationResumeUseCase,
        exporter: StructuredResumeDocxExportPort,
    ) -> None:
        self._effective_resume_use_case = effective_resume_use_case
        self._exporter = exporter

    def execute(
        self,
        request: ExportEffectiveStructuredResumeDocxRequest,
    ) -> ExportEffectiveStructuredResumeDocxResult:
        """Export only the snapshot selected by persisted application state."""
        destination = request.destination_path
        invalid_destination = self._validate_destination(destination)
        if invalid_destination is not None:
            return self._result(invalid_destination, request.application_id, destination)

        effective = self._effective_resume_use_case.execute(
            EffectiveApplicationResumeRequest(request.application_id)
        )
        status = self._effective_status(effective.status)
        if status is not None:
            return self._result(
                status,
                request.application_id,
                destination,
                source=effective.resume_source,
                curriculum_id=effective.curriculum_id,
                resume_version_id=effective.effective_resume_version_id,
                message=effective.message,
            )
        if effective.structured_content_status is StructuredResumeContentStatus.UNSUPPORTED_SCHEMA:
            return self._result(
                EffectiveStructuredResumeDocxExportStatus.UNSUPPORTED_SCHEMA,
                request.application_id,
                destination,
                source=effective.resume_source,
                curriculum_id=effective.curriculum_id,
                resume_version_id=effective.effective_resume_version_id,
            )
        if effective.structured_resume is None:
            return self._result(
                EffectiveStructuredResumeDocxExportStatus.STRUCTURED_CONTENT_REQUIRED,
                request.application_id,
                destination,
                source=effective.resume_source,
                curriculum_id=effective.curriculum_id,
                resume_version_id=effective.effective_resume_version_id,
            )
        try:
            self._exporter.export(effective.structured_resume, destination)
        except PermissionError:
            return self._result(
                EffectiveStructuredResumeDocxExportStatus.DESTINATION_NOT_WRITABLE,
                request.application_id,
                destination,
                source=effective.resume_source,
                curriculum_id=effective.curriculum_id,
                resume_version_id=effective.effective_resume_version_id,
            )
        except OSError:
            return self._result(
                EffectiveStructuredResumeDocxExportStatus.EXPORT_FAILED,
                request.application_id,
                destination,
                source=effective.resume_source,
                curriculum_id=effective.curriculum_id,
                resume_version_id=effective.effective_resume_version_id,
            )
        return self._result(
            EffectiveStructuredResumeDocxExportStatus.SUCCESS,
            request.application_id,
            destination,
            exported=True,
            source=effective.resume_source,
            curriculum_id=effective.curriculum_id,
            resume_version_id=effective.effective_resume_version_id,
            message="Currículo estruturado exportado com sucesso.",
        )

    @staticmethod
    def _validate_destination(
        destination: Path,
    ) -> EffectiveStructuredResumeDocxExportStatus | None:
        if destination.suffix.lower() != ".docx" or not destination.name:
            return EffectiveStructuredResumeDocxExportStatus.INVALID_DESTINATION
        if not destination.parent.is_dir():
            return EffectiveStructuredResumeDocxExportStatus.INVALID_DESTINATION
        return None

    @staticmethod
    def _effective_status(
        status: EffectiveApplicationResumeStatus,
    ) -> EffectiveStructuredResumeDocxExportStatus | None:
        mapping = {
            EffectiveApplicationResumeStatus.APPLICATION_NOT_FOUND: EffectiveStructuredResumeDocxExportStatus.APPLICATION_NOT_FOUND,
            EffectiveApplicationResumeStatus.CURRICULUM_NOT_FOUND: EffectiveStructuredResumeDocxExportStatus.CURRICULUM_NOT_FOUND,
            EffectiveApplicationResumeStatus.SELECTED_VERSION_NOT_FOUND: EffectiveStructuredResumeDocxExportStatus.ADOPTED_RESUME_VERSION_NOT_FOUND,
            EffectiveApplicationResumeStatus.SELECTED_VERSION_CURRICULUM_MISMATCH: EffectiveStructuredResumeDocxExportStatus.ADOPTED_RESUME_VERSION_NOT_FOUND,
            EffectiveApplicationResumeStatus.CONTENT_UNAVAILABLE: EffectiveStructuredResumeDocxExportStatus.STRUCTURED_CONTENT_REQUIRED,
            EffectiveApplicationResumeStatus.CURRICULUM_REQUIRED: EffectiveStructuredResumeDocxExportStatus.STRUCTURED_CONTENT_REQUIRED,
            EffectiveApplicationResumeStatus.SELECTION_INCONSISTENT: EffectiveStructuredResumeDocxExportStatus.ADOPTED_RESUME_VERSION_NOT_FOUND,
        }
        return mapping.get(status)

    @staticmethod
    def _result(
        status: EffectiveStructuredResumeDocxExportStatus,
        application_id: int,
        destination_path: Path,
        *,
        exported: bool = False,
        message: str = "",
        source: ApplicationResumeSource = ApplicationResumeSource.ORIGINAL,
        curriculum_id: int | None = None,
        resume_version_id: int | None = None,
    ) -> ExportEffectiveStructuredResumeDocxResult:
        return ExportEffectiveStructuredResumeDocxResult(
            status,
            application_id,
            destination_path,
            exported,
            message,
            source,
            curriculum_id,
            resume_version_id,
        )
