from __future__ import annotations

from typing import TYPE_CHECKING

from acd.models.company import Company

if TYPE_CHECKING:
    from acd.infrastructure.repositories.company_repository import CompanyRepository


def create_company(
    repository: "CompanyRepository",
    *,
    name: str,
    city: str,
    website: str = "",
) -> Company:
    """Cria uma nova empresa e persiste no repositório."""
    cleaned_name = name.strip()
    cleaned_city = city.strip()
    cleaned_website = website.strip()

    if not cleaned_name or not cleaned_city:
        raise ValueError("Nome e cidade são obrigatórios.")

    company = Company(
        name=cleaned_name,
        city=cleaned_city,
        website=cleaned_website,
    )
    return repository.add(company)
