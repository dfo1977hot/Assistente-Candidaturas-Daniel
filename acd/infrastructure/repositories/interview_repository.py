from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.interview import Interview


class InterviewRepository:
    """Repositório para persistência de entrevistas."""

    def create(self, interview: Interview) -> Interview:
        with database_module.SessionLocal() as session:
            session.add(interview)
            session.commit()
            session.refresh(interview)
            return interview

    def update(self, interview: Interview) -> Interview:
        with database_module.SessionLocal() as session:
            session.add(interview)
            session.commit()
            session.refresh(interview)
            return interview

    def delete(self, interview_id: int) -> bool:
        with database_module.SessionLocal() as session:
            interview = session.get(Interview, interview_id)
            if interview is None:
                return False
            session.delete(interview)
            session.commit()
            return True

    def get_by_id(self, interview_id: int) -> Interview | None:
        with database_module.SessionLocal() as session:
            return session.get(Interview, interview_id)

    def get_all(self) -> list[Interview]:
        with database_module.SessionLocal() as session:
            stmt = select(Interview).order_by(Interview.interview_date.asc())
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Interview]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Interview)
                .where(
                    Interview.interviewer.ilike(f"%{query}%") | Interview.notes.ilike(f"%{query}%")
                )
                .order_by(Interview.interview_date.asc())
            )
            return list(session.scalars(stmt).all())

    def filter(
        self,
        *,
        interview_type: str | None = None,
        result: str | None = None,
        period_start: datetime | None = None,
        period_end: datetime | None = None,
    ) -> list[Interview]:
        with database_module.SessionLocal() as session:
            stmt = select(Interview)
            if interview_type:
                stmt = stmt.where(Interview.interview_type == interview_type)
            if result:
                stmt = stmt.where(Interview.result == result)
            if period_start:
                stmt = stmt.where(Interview.interview_date >= period_start)
            if period_end:
                stmt = stmt.where(Interview.interview_date <= period_end)
            stmt = stmt.order_by(Interview.interview_date.asc())
            return list(session.scalars(stmt).all())

    def get_today(self) -> list[Interview]:
        today = datetime.now().date()
        with database_module.SessionLocal() as session:
            stmt = select(Interview).where(
                Interview.interview_date >= datetime.combine(today, datetime.min.time()),
                Interview.interview_date
                < datetime.combine(today + timedelta(days=1), datetime.min.time()),
            )
            return list(session.scalars(stmt).all())

    def get_next(self, limit: int = 5) -> list[Interview]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Interview)
                .where(Interview.interview_date >= datetime.now())
                .order_by(Interview.interview_date.asc())
                .limit(limit)
            )
            return list(session.scalars(stmt).all())

    def get_statistics(self) -> dict[str, int]:
        with database_module.SessionLocal() as session:
            total = session.query(Interview).count()
            today = datetime.now().date()
            today_count = (
                session.query(Interview)
                .filter(
                    Interview.interview_date >= datetime.combine(today, datetime.min.time()),
                    Interview.interview_date
                    < datetime.combine(today + timedelta(days=1), datetime.min.time()),
                )
                .count()
            )
            week_end = today + timedelta(days=7)
            week_count = (
                session.query(Interview)
                .filter(
                    Interview.interview_date >= datetime.combine(today, datetime.min.time()),
                    Interview.interview_date < datetime.combine(week_end, datetime.min.time()),
                )
                .count()
            )
            return {"total": total, "today": today_count, "week": week_count}
