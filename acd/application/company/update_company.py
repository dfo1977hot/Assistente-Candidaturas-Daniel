from __future__ import annotations

from typing import TYPE_CHECKING

from acd.models.company import Company

if TYPE_CHECKING:
    from acd.infrastructure.repositories.company_repository import CompanyRepository


def update_company(
    repository: CompanyRepository,
    company_id: int,
    *,
    name: str,
    city: str,
    website: str = "",
) -> Company | None:
    """Atualiza os dados de uma empresa existente."""
    cleaned_name = name.strip()
    cleaned_city = city.strip()
    cleaned_website = website.strip()

    if not cleaned_name or not cleaned_city:
        raise ValueError("Nome e cidade são obrigatórios.")

    company = repository.get_by_id(company_id)
    if company is None:
        return None

    company.name = cleaned_name
    company.city = cleaned_city
    company.website = cleaned_website
    return repository.update(company)
