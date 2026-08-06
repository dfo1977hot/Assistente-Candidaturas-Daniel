"""Infrastructure adapter for read-only generated resume version queries."""

from __future__ import annotations

import logging

from sqlalchemy import select

from acd.application.query_ports import (
    GeneratedResumeVersionQueryDTO,
    GeneratedResumeVersionQueryPort,
)
from acd.application.structured_resume_snapshot import (
    StructuredResumeContentStatus,
    StructuredResumeSnapshot,
    StructuredResumeSnapshotCodec,
)
from acd.database import database as database_module
from acd.domain.entities.resume_version import ResumeVersion


class GeneratedResumeVersionQueryAdapter(GeneratedResumeVersionQueryPort):
    """Map persisted ``ResumeVersion`` records to Application-safe DTOs."""

    def __init__(self) -> None:
        self._codec = StructuredResumeSnapshotCodec()

    def list_by_curriculum_id(
        self, curriculum_id: int
    ) -> tuple[GeneratedResumeVersionQueryDTO, ...]:
        """Return versions ordered by their persisted creation time."""
        with database_module.SessionLocal() as session:
            versions = session.scalars(
                select(ResumeVersion)
                .where(ResumeVersion.curriculum_id == curriculum_id)
                .order_by(ResumeVersion.created_at.asc(), ResumeVersion.id.asc())
            ).all()
        return tuple(self._to_dto(version) for version in versions)

    def _to_dto(self, version: ResumeVersion) -> GeneratedResumeVersionQueryDTO:
        structured_resume, structured_status = self._structured_resume(
            getattr(version, "structured_content_json", None)
        )
        return GeneratedResumeVersionQueryDTO(
            version_id=version.id,
            curriculum_id=version.curriculum_id,
            version=version.version,
            content=version.content,
            explanation=version.explanation,
            created_at=version.created_at,
            structured_resume=structured_resume,
            structured_content_status=structured_status,
        )

    def _structured_resume(
        self, content: str | None
    ) -> tuple[StructuredResumeSnapshot | None, StructuredResumeContentStatus]:
        snapshot, status = self._codec.decode(content)
        if status is StructuredResumeContentStatus.UNSUPPORTED_SCHEMA:
            logging.getLogger(__name__).warning("Unsupported generated resume structured schema.")
        elif status is StructuredResumeContentStatus.INVALID:
            logging.getLogger(__name__).warning("Invalid generated resume structured payload.")
        return snapshot, status
