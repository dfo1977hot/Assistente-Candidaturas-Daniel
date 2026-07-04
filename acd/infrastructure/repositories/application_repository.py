from __future__ import annotations
from sqlalchemy.orm import joinedload
from datetime import date
from typing import Optional

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.application import Application
from acd.domain.entities.timeline_event import TimelineEvent


class ApplicationRepository:
    """Repositório para persistência de candidaturas."""

    def create(self, application: Application) -> Application:
        with database_module.SessionLocal() as session:
            session.add(application)
            session.commit()
            session.refresh(application)
            return application

    def update(self, application: Application) -> Application:
        with database_module.SessionLocal() as session:
            session.add(application)
            session.commit()
            session.refresh(application)
            return application

    def delete(self, application_id: int) -> bool:
        with database_module.SessionLocal() as session:
            application = session.get(Application, application_id)
            if application is None:
                return False
            session.delete(application)
            session.commit()
            return True

    def get_by_id(self, application_id: int) -> Optional[Application]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Application)
                .options(
                    joinedload(Application.company),
                    joinedload(Application.job),
                )
                .where(Application.id == application_id)
            )

            return session.scalar(stmt)
        
    def get_all(self) -> list[Application]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Application)
                .options(
                    joinedload(Application.company),
                    joinedload(Application.job),
                )
                .order_by(
                    Application.application_date.desc(),
                    Application.created_at.desc(),
                )
            )

            return list(session.scalars(stmt).all())
            


    def search(self, query: str) -> list[Application]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Application)
                .where(
                    Application.notes.ilike(f"%{query}%")
                    | Application.feedback.ilike(f"%{query}%")
                )
                .order_by(Application.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def filter(self, *, status: Optional[str] = None, company_id: Optional[int] = None, channel: Optional[str] = None) -> list[Application]:
        with database_module.SessionLocal() as session:
            stmt = select(Application)
            if status:
                stmt = stmt.where(Application.status == status)
            if company_id is not None:
                stmt = stmt.where(Application.company_id == company_id)
            if channel:
                stmt = stmt.where(Application.application_channel == channel)
            stmt = stmt.order_by(Application.created_at.desc())
            return list(session.scalars(stmt).all())

    def change_status(self, application_id: int, status: str) -> Optional[Application]:
        with database_module.SessionLocal() as session:
            application = session.get(Application, application_id)
            if application is None:
                return None
            application.status = status
            application.last_update = date.today()
            session.commit()
            session.refresh(application)
            return application

    def get_followups(self, application_id: int) -> list[TimelineEvent]:
        with database_module.SessionLocal() as session:
            stmt = select(TimelineEvent).where(TimelineEvent.application_id == application_id).order_by(TimelineEvent.created_at.desc())
            return list(session.scalars(stmt).all())

    def get_statistics(self) -> dict[str, int]:
        with database_module.SessionLocal() as session:
            total = session.query(Application).count()
            active = session.query(Application).filter(Application.status != "Encerrada").count()
            return {"total": total, "active": active}
        
    def count(self) -> int:
        """
        Retorna o número total de candidaturas cadastradas.
        """

        with database_module.SessionLocal() as session:
            return session.query(Application).count()

    def add_event(self, application_id: int, event_type: str, description: str) -> TimelineEvent:
        with database_module.SessionLocal() as session:
            event = TimelineEvent(application_id=application_id, event_type=event_type, description=description)
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
