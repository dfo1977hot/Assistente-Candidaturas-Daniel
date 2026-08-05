"""Infrastructure adapter for resume read queries."""

from __future__ import annotations

import logging

from acd.application.query_ports import (
    ResumeQueryDTO,
    ResumeQueryPort,
    ResumeVersionQueryDTO,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
    StructuredResumeSnapshotCodec,
)
from acd.infrastructure.repositories.curriculum_repository import CurriculumRepository


class ResumeQueryAdapter(ResumeQueryPort):
    """Maps existing curriculum repository reads to Application DTOs."""

    def __init__(self, repository: CurriculumRepository) -> None:
        self._repository = repository
        self._codec = StructuredResumeSnapshotCodec()

    def get_by_id(self, curriculum_id: int) -> ResumeQueryDTO | None:
        """Return a curriculum DTO when the repository has the requested entity."""
        curriculum = self._repository.get_by_id(curriculum_id)
        if curriculum is None:
            return None
        structured_resume, structured_status = self._structured_resume(
            getattr(curriculum, "structured_content_json", None)
        )
        return ResumeQueryDTO(
            curriculum_id=curriculum.id,
            name=curriculum.name,
            version=curriculum.version,
            language=curriculum.language,
            description=curriculum.description,
            structured_resume=structured_resume,
            structured_content_status=structured_status,
        )

    def list_versions(self, curriculum_id: int) -> tuple[ResumeVersionQueryDTO, ...]:
        """Return curriculum version history as immutable DTOs."""
        return tuple(
            ResumeVersionQueryDTO(
                version_id=version.id,
                curriculum_id=version.curriculum_id,
                version=version.version,
                file_name=version.file_name,
                created_at=version.created_at,
            )
            for version in self._repository.get_versions(curriculum_id)
        )

    def _structured_resume(
        self, content: str | None
    ) -> tuple[StructuredResumeSnapshot | None, StructuredResumeContentStatus]:
        if content is None:
            return None, StructuredResumeContentStatus.UNAVAILABLE
        snapshot, status = self._codec.decode(content)
        if status is StructuredResumeContentStatus.UNSUPPORTED_SCHEMA:
            logging.getLogger(__name__).warning("Unsupported curriculum structured resume schema.")
        elif status is StructuredResumeContentStatus.INVALID:
            logging.getLogger(__name__).warning("Invalid curriculum structured resume payload.")
        return snapshot, status
