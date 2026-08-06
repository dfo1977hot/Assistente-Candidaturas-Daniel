from __future__ import annotations

from sqlalchemy import or_, select

from acd.database import database as database_module
from acd.infrastructure.database.dependency_delete import delete_with_dependencies
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

    def delete(self, company_id: int, *, delete_linked: bool = False) -> bool:
        with database_module.SessionLocal() as session:
            if delete_linked:
                return delete_with_dependencies(
                    session,
                    table_name="companies",
                    primary_key="id",
                    value=company_id,
                )
            entity = session.get(Company, company_id)
            if entity is None:
                return False
            session.delete(entity)
            session.commit()
            return True

    def get_by_id(self, company_id: int) -> Company | None:
        with database_module.SessionLocal() as session:
            return session.get(Company, company_id)

    def get_all(self) -> list[Company]:
        with database_module.SessionLocal() as session:
            stmt = select(Company).order_by(Company.name.asc())
            return list(session.scalars(stmt).all())

    def search(self, query: str) -> list[Company]:
        with database_module.SessionLocal() as session:
            stmt = (
                select(Company)
                .where(
                    or_(
                        Company.name.ilike(f"%{query}%"),
                        Company.segment.ilike(f"%{query}%"),
                        Company.city.ilike(f"%{query}%"),
                        Company.website.ilike(f"%{query}%"),
                        Company.legal_name.ilike(f"%{query}%"),
                        Company.tax_id.ilike(f"%{query}%"),
                    )
                )
                .order_by(Company.name.asc())
            )
            return list(session.scalars(stmt).all())

    def get_all_sorted(self, *, by: str = "name", descending: bool = False) -> list[Company]:
        with database_module.SessionLocal() as session:
            sortable = {
                "name": Company.name,
                "city": Company.city,
                "segment": Company.segment,
                "created_at": Company.created_at,
            }
            column = sortable.get(by, Company.name)
            stmt = select(Company).order_by(column.desc() if descending else column.asc())
            return list(session.scalars(stmt).all())

    def exists_by_name_and_website(
        self, *, name: str, website: str, exclude_id: int | None = None
    ) -> bool:
        normalized_name = name.strip().lower()
        normalized_website = website.strip().lower()

        with database_module.SessionLocal() as session:
            stmt = select(Company).where(Company.name.ilike(normalized_name))
            if normalized_website:
                stmt = stmt.where(Company.website.ilike(normalized_website))
            if exclude_id is not None:
                stmt = stmt.where(Company.id != exclude_id)
            return session.scalar(stmt) is not None

    def exists_by_tax_id(self, tax_id: str, *, exclude_id: int | None = None) -> bool:
        normalized = "".join(character for character in tax_id if character.isdigit())
        if not normalized:
            return False
        with database_module.SessionLocal() as session:
            stmt = select(Company).where(Company.tax_id == normalized)
            if exclude_id is not None:
                stmt = stmt.where(Company.id != exclude_id)
            return session.scalar(stmt) is not None

    def exists(self, company_id: int) -> bool:
        with database_module.SessionLocal() as session:
            return session.get(Company, company_id) is not None

    def count(self) -> int:
        with database_module.SessionLocal() as session:
            return session.query(Company).count()
