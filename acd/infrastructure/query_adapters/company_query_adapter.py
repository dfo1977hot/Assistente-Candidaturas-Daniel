"""Infrastructure adapter for company read queries."""

from __future__ import annotations

from acd.application.query_ports import CompanyQueryDTO, CompanyQueryPort
from acd.infrastructure.repositories.company_repository import CompanyRepository


class CompanyQueryAdapter(CompanyQueryPort):
    """Maps existing company repository reads to Application DTOs."""

    def __init__(self, repository: CompanyRepository) -> None:
        self._repository = repository

    def get_by_id(self, company_id: int) -> CompanyQueryDTO | None:
        """Return a company DTO when the repository has the requested entity."""
        company = self._repository.get_by_id(company_id)
        if company is None:
            return None
        return CompanyQueryDTO(
            company_id=company.id,
            name=company.name,
            segment=company.segment,
        )
