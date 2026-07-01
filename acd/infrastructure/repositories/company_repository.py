from __future__ import annotations

from typing import Optional

from sqlalchemy import select

from acd.database import database as database_module
from acd.models.company import Company


class CompanyRepository:
    """Repositório responsável pela persistência de empresas no SQLite."""

    def create(self, company: Company) -> Company:
        with database_module.SessionLocal() as session:
            session.add(company)
            session.commit()
            session.refresh(company)
            return company

    def update(self, company: Company) -> Company:
        with database_module.SessionLocal() as session:
            session.add(company)
            session.commit()
            session.refresh(company)
            return company

    def delete(self, company_id: int) -> bool:
        with database_module.SessionLocal() as session:
            company = session.get(Company, company_id)
            if company is None:
                return False
            session.delete(company)
            session.commit()
            return True

    def get_by_id(self, company_id: int) -> Optional[Company]:
        with database_module.SessionLocal() as session:
            return session.get(Company, company_id)

    def get_all(self) -> list[Company]:
        with database_module.SessionLocal() as session:
            stmt = select(Company).order_by(Company.name.asc())
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Company]:
        with database_module.SessionLocal() as session:
            stmt = select(Company).where(Company.name.ilike(f"%{query}%"))
            return list(session.scalars(stmt).all())

    def exists(self, company_id: int) -> bool:
        with database_module.SessionLocal() as session:
            return session.get(Company, company_id) is not None

    def count(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(Company).count()
