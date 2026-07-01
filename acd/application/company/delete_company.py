from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from acd.infrastructure.repositories.company_repository import CompanyRepository


def delete_company(repository: "CompanyRepository", company_id: int) -> bool:
    """Remove uma empresa do repositório."""
    return repository.delete(company_id)
