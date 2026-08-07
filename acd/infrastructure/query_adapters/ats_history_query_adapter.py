"""Infrastructure adapter for ATS history read queries."""

from __future__ import annotations

from sqlalchemy import select

from acd.application.query_ports import (
    ATSGapQueryDTO,
    ATSHistoryQueryDTO,
    ATSHistoryQueryPort,
    ATSRecommendationQueryDTO,
    ATSScoreDetailQueryDTO,
)
from acd.database import database as database_module
from acd.domain.entities.curriculum import Curriculum
from acd.domain.entities.job import Job
from acd.domain.entities.job_profile import JobProfile
from acd.domain.entities.recommendation import Recommendation
from acd.domain.entities.score_detail import ScoreDetail
from acd.domain.entities.skill_gap import SkillGap
from acd.infrastructure.repositories.ats_repository import ATSRepository


class ATSHistoryQueryAdapter(ATSHistoryQueryPort):
    """Maps existing ATS history repository reads to Application DTOs."""

    def __init__(self, repository: ATSRepository) -> None:
        self._repository = repository

    def get_latest_for_curriculum(self, curriculum_id: int) -> ATSHistoryQueryDTO | None:
        """Return the latest existing ATS history entry for a curriculum."""
        for score in self._repository.get_history():
            if score.curriculum_id == curriculum_id:
                return self._to_dto(score)
        return None

    def _to_dto(self, score: object) -> ATSHistoryQueryDTO:
        """Project persisted ATS data associated with one score record."""
        with database_module.SessionLocal() as session:
            curriculum = (
                None
                if score.curriculum_id is None
                else session.get(Curriculum, score.curriculum_id)
            )
            profile = (
                None
                if score.job_profile_id is None
                else session.get(JobProfile, score.job_profile_id)
            )
            job = None if profile is None else session.get(Job, profile.job_id)
            gaps = tuple(
                ATSGapQueryDTO(skill_name=gap.skill_name, gap_type=gap.gap_type)
                for gap in session.scalars(
                    select(SkillGap).where(SkillGap.score_id == score.id)
                )
            )
            recommendations = tuple(
                ATSRecommendationQueryDTO(
                    message=recommendation.message,
                    recommendation_type=recommendation.recommendation_type,
                )
                for recommendation in session.scalars(
                    select(Recommendation).where(Recommendation.score_id == score.id)
                )
            )
            details = tuple(
                ATSScoreDetailQueryDTO(
                    criterion=detail.criterion,
                    score=float(detail.score),
                    max_score=float(detail.max_score),
                    weight=float(detail.weight),
                )
                for detail in session.scalars(
                    select(ScoreDetail).where(ScoreDetail.score_id == score.id)
                )
            )
        return ATSHistoryQueryDTO(
                    score_id=score.id,
                    curriculum_id=score.curriculum_id,
                    job_profile_id=score.job_profile_id,
                    total_score=float(score.total_score),
                    calculated_at=score.calculated_at,
                    application_id=getattr(score, "application_id", None),
                    curriculum_version=None if curriculum is None else curriculum.version,
                    job_id=None if profile is None else profile.job_id,
                    job_title=None if job is None else job.title,
                    job_profile_keywords=self._split_values(
                        None if profile is None else profile.keywords
                    ),
                    gaps=gaps or None,
                    recommendations=recommendations or None,
                    score_details=details or None,
                    matched_competencies=None,
                    missing_competencies=(
                        tuple(gap.skill_name for gap in gaps if gap.gap_type == "missing")
                        if gaps
                        else None
                    ),
                )

    @staticmethod
    def _split_values(value: str | None) -> tuple[str, ...] | None:
        """Expose an existing comma-separated persisted value as a sequence."""
        values = () if value is None else tuple(item.strip() for item in value.split(",") if item.strip())
        return values or None
