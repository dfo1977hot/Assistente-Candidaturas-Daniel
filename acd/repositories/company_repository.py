from sqlalchemy import select

from acd.database.database import SessionLocal
from acd.models.company import Company


class CompanyRepository:

    def get_all(self):

        with SessionLocal() as session:

            stmt = select(Company)

            return session.scalars(stmt).all()

    def add(self, company):

        with SessionLocal() as session:

            session.add(company)

            session.commit()

    def delete(self, company):

        with SessionLocal() as session:

            session.delete(company)

            session.commit()
