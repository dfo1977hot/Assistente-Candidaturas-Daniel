from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from acd.database import database as database_module
from acd.domain.entities.profile import Profile


class ProfileRepository:
    """Repositório para o perfil profissional unificado."""

    def create(self, profile: Profile) -> Profile:
        with database_module.SessionLocal() as session:
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def update(self, profile: Profile) -> Profile:
        with database_module.SessionLocal() as session:
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return profile

    def get_by_id(self, profile_id: int) -> Optional[Profile]:
        with database_module.SessionLocal() as session:
            return session.get(Profile, profile_id)

    def list_all(self) -> list[Profile]:
        with database_module.SessionLocal() as session:
            return list(session.scalars(select(Profile)).all())

    def delete(self, profile_id: int) -> bool:
        with database_module.SessionLocal() as session:
            profile = session.get(Profile, profile_id)
            if profile is None:
                return False
            session.delete(profile)
            session.commit()
            return True
