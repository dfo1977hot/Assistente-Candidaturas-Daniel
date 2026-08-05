"""Atomic Infrastructure write adapter for structured resume versions."""

from __future__ import annotations

from sqlalchemy import select

from acd.application.structured_resume_snapshot import StructuredResumeSnapshotCodec
from acd.application.structured_resume_version_generation import (
    CreatedStructuredResumeVersion,
    CreateStructuredResumeVersionRequest,
    StructuredResumeVersionWritePort,
)
from acd.database import database as database_module
from acd.domain.entities.resume_version import ResumeVersion


class StructuredResumeVersionWriteAdapter(StructuredResumeVersionWritePort):
    """Store text and canonical structured JSON in one database transaction."""

    def __init__(self, codec: StructuredResumeSnapshotCodec | None = None) -> None:
        self._codec = codec or StructuredResumeSnapshotCodec()

    def create_structured_resume_version(
        self, request: CreateStructuredResumeVersionRequest
    ) -> CreatedStructuredResumeVersion:
        """Create one complete version or roll the transaction back on failure."""
        structured_content = self._codec.dumps(request.structured_resume)
        with database_module.SessionLocal() as session:
            try:
                versions = list(
                    session.scalars(
                        select(ResumeVersion.id).where(
                            ResumeVersion.curriculum_id == request.curriculum_id
                        )
                    )
                )
                version = ResumeVersion(
                    curriculum_id=request.curriculum_id,
                    version=f"v{len(versions) + 2}.0",
                    content=request.content,
                    structured_content_json=structured_content,
                    explanation=request.explanation,
                )
                session.add(version)
                session.flush()
                assert version.id is not None
                created = CreatedStructuredResumeVersion(version.id, version.version)
                session.commit()
                return created
            except Exception:
                session.rollback()
                raise
