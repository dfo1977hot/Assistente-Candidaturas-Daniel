from __future__ import annotations

from typing import TYPE_CHECKING

from acd.models.company import Company

if TYPE_CHECKING:
    from acd.infrastructure.repositories.company_repository import CompanyRepository


def list_companies(repository: CompanyRepository) -> list[Company]:
    """Retorna todas as empresas cadastradas."""
    return repository.get_all()
