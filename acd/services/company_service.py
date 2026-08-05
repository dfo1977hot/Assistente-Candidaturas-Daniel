from __future__ import annotations

import logging

from acd.core.logger import logger
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.models.company import Company


class CompanyService:
    """Camada de serviço para regras de negócio das empresas."""

    def __init__(self, repository: CompanyRepository | None = None) -> None:
        self.repository = repository or CompanyRepository()
        self._crud_logger = _build_crud_logger()

    def create_company(
        self,
        *,
        name: str,
        city: str,
        segment: str = "",
        state: str = "",
        country: str = "",
        company_size: str = "",
        website: str = "",
        linkedin_url: str = "",
        notes: str = "",
    ) -> Company:
        """Valida e cria uma empresa."""

        self._validate_required_fields(
            name=name,
            city=city,
        )

        self._validate_duplicate(
            name=name,
            website=website,
        )

        company = Company(
            name=name.strip(),
            segment=segment.strip(),
            city=city.strip(),
            state=state.strip(),
            country=country.strip(),
            company_size=company_size.strip(),
            website=website.strip(),
            linkedin_url=linkedin_url.strip(),
            notes=notes.strip(),
        )

        created = self.repository.create(company)

        logger.info("Company created: id=%s", created.id)
        self._crud_logger.info(
            "company.created entity_id=%s",
            created.id,
        )

        return created

    def update_company(
        self,
        company_id: int,
        *,
        name: str,
        city: str,
        segment: str = "",
        state: str = "",
        country: str = "",
        company_size: str = "",
        website: str = "",
        linkedin_url: str = "",
        notes: str = "",
    ) -> Company | None:
        """Valida e atualiza uma empresa existente."""

        self._validate_required_fields(
            name=name,
            city=city,
        )

        self._validate_duplicate(
            name=name,
            website=website,
            exclude_id=company_id,
        )

        company = self.repository.get_by_id(company_id)

        if company is None:
            return None

        company.name = name.strip()
        company.segment = segment.strip()
        company.city = city.strip()
        company.state = state.strip()
        company.country = country.strip()
        company.company_size = company_size.strip()
        company.website = website.strip()
        company.linkedin_url = linkedin_url.strip()
        company.notes = notes.strip()

        updated = self.repository.update(company)

        logger.info("Company updated: id=%s", updated.id)
        self._crud_logger.info(
            "company.updated entity_id=%s",
            updated.id,
        )

        return updated

    def delete_company(self, company_id: int) -> bool:
        """Remove uma empresa, se existir."""

        deleted = self.repository.delete(company_id)

        if deleted:
            logger.info("Company deleted: id=%s", company_id)
            self._crud_logger.info(
                "company.deleted entity_id=%s",
                company_id,
            )

        return deleted

    def list_companies(self) -> list[Company]:
        """Retorna todas as empresas ordenadas por nome."""
        return self.repository.get_all()

    def search_companies(self, query: str) -> list[Company]:
        """Busca empresas pelo nome."""
        return self.repository.search(query)

    def count_companies(self) -> int:
        """Retorna o total de empresas cadastradas."""
        return self.repository.count()

    def _validate_required_fields(
        self,
        *,
        name: str,
        city: str,
    ) -> None:
        """Validação mínima compatível com versões anteriores."""

        if not name or not name.strip():
            raise ValueError("Nome é obrigatório.")

        if not city or not city.strip():
            raise ValueError("Cidade é obrigatória.")

    def _validate_duplicate(
        self,
        *,
        name: str,
        website: str,
        exclude_id: int | None = None,
    ) -> None:
        """Valida duplicidade por nome + website."""

        if self.repository.exists_by_name_and_website(
            name=name,
            website=website,
            exclude_id=exclude_id,
        ):
            raise ValueError(
                "Empresa duplicada: nome + site já cadastrado."
            )


def _build_crud_logger() -> logging.Logger:
    """Return the file-free compatibility logger used by the legacy service."""
    logger = logging.getLogger("acd.audit.company")
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger
