from __future__ import annotations

from typing import Optional
import logging
from pathlib import Path

from acd.core.logger import logger
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.models.company import Company


class CompanyService:
    """Camada de serviço para regras de negócio das empresas."""

    def __init__(self, repository: Optional[CompanyRepository] = None) -> None:
        self.repository = repository or CompanyRepository()
        self._crud_logger = _build_crud_logger()

    def create_company(
        self,
        *,
        name: str,
        segment: str,
        city: str,
        state: str,
        country: str,
        company_size: str,
        website: str = "",
        linkedin_url: str = "",
        notes: str = "",
    ) -> Company:
        """Valida e cria uma empresa."""
        self._validate_required_fields(
            name=name,
            segment=segment,
            city=city,
            state=state,
            country=country,
            company_size=company_size,
        )
        self._validate_duplicate(name=name, website=website)
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
        logger.info("Empresa criada: %s", created.name)
        self._crud_logger.info("INCLUSAO company_id=%s name=%s", created.id, created.name)
        return created

    def update_company(
        self,
        company_id: int,
        *,
        name: str,
        segment: str,
        city: str,
        state: str,
        country: str,
        company_size: str,
        website: str = "",
        linkedin_url: str = "",
        notes: str = "",
    ) -> Optional[Company]:
        """Valida e atualiza uma empresa existente."""
        self._validate_required_fields(
            name=name,
            segment=segment,
            city=city,
            state=state,
            country=country,
            company_size=company_size,
        )
        self._validate_duplicate(name=name, website=website, exclude_id=company_id)
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
        logger.info("Empresa editada: %s", updated.name)
        self._crud_logger.info("ALTERACAO company_id=%s name=%s", updated.id, updated.name)
        return updated

    def delete_company(self, company_id: int) -> bool:
        """Remove uma empresa, se existir."""
        deleted = self.repository.delete(company_id)
        if deleted:
            logger.info("Empresa excluída: %s", company_id)
            self._crud_logger.info("EXCLUSAO company_id=%s", company_id)
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

    def _validate_required_fields(self, *, name: str, segment: str, city: str, state: str, country: str, company_size: str) -> None:
        if not name or not name.strip():
            raise ValueError("Nome é obrigatório.")
        if not segment or not segment.strip():
            raise ValueError("Segmento é obrigatório.")
        if not city or not city.strip():
            raise ValueError("Cidade é obrigatória.")
        if not state or not state.strip():
            raise ValueError("Estado é obrigatório.")
        if not country or not country.strip():
            raise ValueError("País é obrigatório.")
        if not company_size or not company_size.strip():
            raise ValueError("Porte é obrigatório.")

    def _validate_duplicate(self, *, name: str, website: str, exclude_id: Optional[int] = None) -> None:
        if self.repository.exists_by_name_and_website(
            name=name,
            website=website,
            exclude_id=exclude_id,
        ):
            raise ValueError("Empresa duplicada: nome + site já cadastrado.")


def _build_crud_logger() -> logging.Logger:
    logger_name = "ACD.CRUD"
    crud_logger = logging.getLogger(logger_name)
    if crud_logger.handlers:
        return crud_logger

    log_dir = Path("logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_dir / "crud_validation.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    crud_logger.addHandler(handler)
    crud_logger.setLevel(logging.INFO)
    crud_logger.propagate = False
    return crud_logger
