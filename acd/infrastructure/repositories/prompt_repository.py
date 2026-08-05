from __future__ import annotations

from typing import Any

from sqlalchemy import select

from acd.application.structured_resume_snapshot import (
    StructuredResumeSnapshot,
    StructuredResumeSnapshotCodec,
)
from acd.database import database as database_module
from acd.domain.entities.ai_generation import AIGeneration
from acd.domain.entities.ai_prompt import AIPrompt
from acd.domain.entities.cover_letter_version import CoverLetterVersion
from acd.domain.entities.generation_log import GenerationLog
from acd.domain.entities.prompt_template import PromptTemplate
from acd.domain.entities.resume_version import ResumeVersion


class PromptRepository:
    """Repositório para persistência de prompts, gerações e versões."""

    def save_prompt(self, prompt: AIPrompt) -> AIPrompt:
        with database_module.SessionLocal() as session:
            session.add(prompt)
            session.commit()
            session.refresh(prompt)
            return prompt

    def save_generation(self, generation: AIGeneration) -> AIGeneration:
        with database_module.SessionLocal() as session:
            session.add(generation)
            session.commit()
            session.refresh(generation)
            return generation

    def save_resume_version(
        self,
        version: ResumeVersion,
        structured_resume: StructuredResumeSnapshot | None = None,
    ) -> ResumeVersion:
        """Persist a text version and an optional validated structured snapshot."""
        if structured_resume is not None:
            version.structured_content_json = StructuredResumeSnapshotCodec().dumps(
                structured_resume
            )
        with database_module.SessionLocal() as session:
            session.add(version)
            session.commit()
            session.refresh(version)
            return version

    def save_cover_letter_version(self, version: CoverLetterVersion) -> CoverLetterVersion:
        with database_module.SessionLocal() as session:
            session.add(version)
            session.commit()
            session.refresh(version)
            return version

    def save_log(self, log: GenerationLog) -> GenerationLog:
        with database_module.SessionLocal() as session:
            session.add(log)
            session.commit()
            session.refresh(log)
            return log

    def save_template(self, template: PromptTemplate) -> PromptTemplate:
        with database_module.SessionLocal() as session:
            session.add(template)
            session.commit()
            session.refresh(template)
            return template

    def get_resume_versions(self, curriculum_id: int) -> list[ResumeVersion]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(ResumeVersion)
                .where(ResumeVersion.curriculum_id == curriculum_id)
                .order_by(ResumeVersion.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def get_cover_letter_versions(self, curriculum_id: int) -> list[CoverLetterVersion]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(CoverLetterVersion)
                .where(CoverLetterVersion.curriculum_id == curriculum_id)
                .order_by(CoverLetterVersion.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def get_statistics(self) -> dict[str, Any]:
        with database_module.SessionLocal() as session:
            resumes = list(session.scalars(select(ResumeVersion)).all())
            letters = list(session.scalars(select(CoverLetterVersion)).all())
            return {"resumes_generated": len(resumes), "cover_letters_generated": len(letters)}
