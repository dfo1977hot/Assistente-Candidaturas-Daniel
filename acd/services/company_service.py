from __future__ import annotations

from typing import Optional

from acd.core.logger import logger
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.models.company import Company


class CompanyService:
    """Camada de serviço para regras de negócio das empresas."""

    def __init__(self, repository: Optional[CompanyRepository] = None) -> None:
        self.repository = repository or CompanyRepository()

    def create_company(
        self,
        *,
        name: str,
        city: str,
        website: str = "",
        notes: str = "",
    ) -> Company:
        """Valida e cria uma empresa."""
        self._validate_required_fields(name=name, city=city)
        company = Company(
            name=name.strip(),
            city=city.strip(),
            website=website.strip(),
            notes=notes.strip(),
        )
        created = self.repository.create(company)
        logger.info("Empresa criada: %s", created.name)
        return created

    def update_company(
        self,
        company_id: int,
        *,
        name: str,
        city: str,
        website: str = "",
        notes: str = "",
    ) -> Optional[Company]:
        """Valida e atualiza uma empresa existente."""
        self._validate_required_fields(name=name, city=city)
        company = self.repository.get_by_id(company_id)
        if company is None:
            return None

        company.name = name.strip()
        company.city = city.strip()
        company.website = website.strip()
        company.notes = notes.strip()
        updated = self.repository.update(company)
        logger.info("Empresa editada: %s", updated.name)
        return updated

    def delete_company(self, company_id: int) -> bool:
        """Remove uma empresa, se existir."""
        deleted = self.repository.delete(company_id)
        if deleted:
            logger.info("Empresa excluída: %s", company_id)
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

    def _validate_required_fields(self, *, name: str, city: str) -> None:
        if not name or not name.strip():
            raise ValueError("Nome é obrigatório.")
        if not city or not city.strip():
            raise ValueError("Cidade é obrigatória.")
