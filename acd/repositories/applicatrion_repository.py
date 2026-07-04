from __future__ import annotations

from collections import Counter
from typing import Any, Optional

from sqlalchemy import select

from acd.core.logger import logger
from acd.database import database as database_module
from acd.domain.entities.application import Application


class ApplicationRepository:
    """Repositório para persistência das candidaturas."""

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

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
            return session.get(Application, application_id)

    def get_all(self) -> list[Application]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Application)
                .order_by(Application.created_at.desc())
            )

            return list(session.scalars(stmt).all())

    # ------------------------------------------------------------------
    # Pesquisa
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[Application]:
        with database_module.SessionLocal() as session:

            stmt = (
                select(Application)
                .where(
                    Application.recruiter_name.ilike(f"%{query}%")
                )
                .order_by(Application.created_at.desc())
            )

            return list(session.scalars(stmt).all())

    def filter(
        self,
        *,
        company_id: Optional[int] = None,
        job_id: Optional[int] = None,
        status: Optional[str] = None,
        channel: Optional[str] = None,
    ) -> list[Application]:

        with database_module.SessionLocal() as session:

            stmt = select(Application)

            if company_id is not None:
                stmt = stmt.where(
                    Application.company_id == company_id
                )

            if job_id is not None:
                stmt = stmt.where(
                    Application.job_id == job_id
                )

            if status:
                stmt = stmt.where(
                    Application.status == status
                )

            if channel:
                stmt = stmt.where(
                    Application.application_channel == channel
                )

            stmt = stmt.order_by(
                Application.created_at.desc()
            )

            return list(session.scalars(stmt).all())

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def exists(self, application_id: int) -> bool:
        with database_module.SessionLocal() as session:
            return (
                session.get(Application, application_id)
                is not None
            )

    def count(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(Application).count()

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------

    def change_status(
        self,
        application_id: int,
        new_status: str,
    ) -> Optional[Application]:

        with database_module.SessionLocal() as session:

            application = session.get(
                Application,
                application_id,
            )

            if application is None:
                return None

            application.status = new_status

            session.commit()
            session.refresh(application)

            return application

    # ------------------------------------------------------------------
    # Timeline
    # ------------------------------------------------------------------

    def add_event(
        self,
        application_id: int,
        event_type: str,
        description: str,
    ) -> None:
        """
        Implementação temporária.

        Na Sprint 0.4 será criada a entidade
        ApplicationTimeline.
        """

        logger.info(
            "APPLICATION_EVENT | id=%s | %s | %s",
            application_id,
            event_type,
            description,
        )

    def get_followups(
        self,
        application_id: int,
    ) -> list[Any]:
        """
        Placeholder até a criação da tabela
        application_timeline.
        """

        return []

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def get_statistics(self) -> dict[str, int]:

        with database_module.SessionLocal() as session:

            applications = (
                session.scalars(
                    select(Application)
                ).all()
            )

        counter = Counter()

        for application in applications:
            counter[application.status] += 1

        statistics = dict(counter)

        statistics["TOTAL"] = len(applications)

        return statistics