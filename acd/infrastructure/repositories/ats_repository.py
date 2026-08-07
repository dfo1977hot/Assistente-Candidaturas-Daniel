from __future__ import annotations

from typing import Any

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.ats_score import ATSScore
from acd.domain.entities.recommendation import Recommendation
from acd.domain.entities.score_detail import ScoreDetail
from acd.domain.entities.skill_gap import SkillGap


class ATSRepository:
    """Repositório para persistência do histórico de comparações ATS."""

    def save_score(self, score: ATSScore) -> ATSScore:
        with database_module.SessionLocal() as session:
            session.add(score)
            session.commit()
            session.refresh(score)
            return score

    def save_detail(self, detail: ScoreDetail) -> ScoreDetail:
        with database_module.SessionLocal() as session:
            session.add(detail)
            session.commit()
            session.refresh(detail)
            return detail

    def save_gap(self, gap: SkillGap) -> SkillGap:
        with database_module.SessionLocal() as session:
            session.add(gap)
            session.commit()
            session.refresh(gap)
            return gap

    def save_recommendation(self, recommendation: Recommendation) -> Recommendation:
        with database_module.SessionLocal() as session:
            session.add(recommendation)
            session.commit()
            session.refresh(recommendation)
            return recommendation

    def get_history(self) -> list[ATSScore]:
        with database_module.SessionLocal() as session:
            stmt = select(ATSScore).order_by(ATSScore.calculated_at.desc())
            return list(session.scalars(stmt).all())

    def get_statistics(self) -> dict[str, Any]:
        with database_module.SessionLocal() as session:
            scores = list(session.scalars(select(ATSScore)).all())
            if not scores:
                return {
                    "total_scores": 0,
                    "highest_score": 0.0,
                    "lowest_score": 0.0,
                    "average_score": 0.0,
                }
            values = [score.total_score for score in scores]
            return {
                "total_scores": len(scores),
                "highest_score": max(values),
                "lowest_score": min(values),
                "average_score": round(sum(values) / len(values), 2),
            }
