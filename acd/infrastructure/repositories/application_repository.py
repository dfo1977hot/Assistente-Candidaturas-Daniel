from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from acd.database import database as database_module
from acd.domain.entities.application import Application
from acd.domain.entities.timeline_event import TimelineEvent
from acd.infrastructure.database.dependency_delete import delete_with_dependencies


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

    def delete(self, application_id: int, *, delete_linked: bool = False) -> bool:
        with database_module.SessionLocal() as session:
            if delete_linked:
                return delete_with_dependencies(
                    session,
                    table_name="applications",
                    primary_key="id",
                    value=application_id,
                )
            entity = session.get(Application, application_id)
            if entity is None:
                return False
            session.delete(entity)
            session.commit()
            return True

    def get_by_id(self, application_id: int) -> Application | None:
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
                .options(
                    joinedload(Application.company),
                    joinedload(Application.job),
                )
                .where(
                    Application.notes.ilike(f"%{query}%") | Application.feedback.ilike(f"%{query}%")
                )
                .order_by(Application.created_at.desc())
            )
            return list(session.scalars(stmt).all())

    def filter(
        self,
        *,
        status: str | None = None,
        company_id: int | None = None,
        channel: str | None = None,
    ) -> list[Application]:
        with database_module.SessionLocal() as session:
            stmt = select(Application).options(
                joinedload(Application.company),
                joinedload(Application.job),
            )
            if status:
                stmt = stmt.where(Application.status == status)
            if company_id is not None:
                stmt = stmt.where(Application.company_id == company_id)
            if channel:
                stmt = stmt.where(Application.application_channel == channel)
            stmt = stmt.order_by(Application.created_at.desc())
            return list(session.scalars(stmt).all())

    def change_status(self, application_id: int, status: str) -> Application | None:
        with database_module.SessionLocal() as session:
            application = session.get(Application, application_id)
            if application is None:
                return None
            application.status = status
            application.last_update = date.today()
            session.commit()
            session.refresh(application)
            return application

    def set_selected_resume_version(
        self, application_id: int, resume_version_id: int
    ) -> bool:
        """Persist only the resume version selected for an application."""
        with database_module.SessionLocal() as session:
            application = session.get(Application, application_id)
            if application is None:
                return False
            application.selected_resume_version_id = resume_version_id
            session.commit()
            return True

    def clear_selected_resume_version(self, application_id: int) -> bool:
        """Clear the resume version selection without changing the base curriculum."""
        with database_module.SessionLocal() as session:
            application = session.get(Application, application_id)
            if application is None:
                return False
            application.selected_resume_version_id = None
            session.commit()
            return True

    def get_followups(self, application_id: int) -> list[TimelineEvent]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(TimelineEvent)
                .where(TimelineEvent.application_id == application_id)
                .order_by(TimelineEvent.created_at.desc())
            )
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
            event = TimelineEvent(
                application_id=application_id, event_type=event_type, description=description
            )
            session.add(event)
            session.commit()
            session.refresh(event)
            return event
