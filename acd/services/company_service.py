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

    def create_company(self, *, name: str, city: str, segment: str = "", state: str = "", country: str = "", company_size: str = "", website: str = "", linkedin_url: str = "", notes: str = "", legal_name: str = "", tax_id: str = "", registration_status: str = "", address: str = "", postal_code: str = "", phone: str = "", data_source: str = "", source_reference: str = "", data_retrieved_at=None) -> Company:
        self._validate_required_fields(name=name, city=city)
        normalized_tax_id = self._normalize_tax_id(tax_id)
        self._validate_duplicate(name=name, website=website, tax_id=normalized_tax_id)
        company = Company(name=name.strip(), legal_name=legal_name.strip(), tax_id=normalized_tax_id, registration_status=registration_status.strip(), segment=segment.strip(), address=address.strip(), city=city.strip(), state=state.strip(), postal_code=postal_code.strip(), country=country.strip(), phone=phone.strip(), company_size=company_size.strip(), website=website.strip(), linkedin_url=linkedin_url.strip(), data_source=data_source.strip(), source_reference=source_reference.strip(), data_retrieved_at=data_retrieved_at, notes=notes.strip())
        created = self.repository.create(company)
        logger.info("Company created: id=%s", created.id)
        self._crud_logger.info("company.created entity_id=%s", created.id)
        return created

    def update_company(self, company_id: int, *, name: str, city: str, segment: str = "", state: str = "", country: str = "", company_size: str = "", website: str = "", linkedin_url: str = "", notes: str = "", legal_name: str = "", tax_id: str = "", registration_status: str = "", address: str = "", postal_code: str = "", phone: str = "", data_source: str = "", source_reference: str = "", data_retrieved_at=None) -> Company | None:
        self._validate_required_fields(name=name, city=city)
        normalized_tax_id = self._normalize_tax_id(tax_id)
        self._validate_duplicate(name=name, website=website, tax_id=normalized_tax_id, exclude_id=company_id)
        company = self.repository.get_by_id(company_id)
        if company is None:
            return None
        values = locals()
        for field in ("name", "legal_name", "registration_status", "segment", "address", "city", "state", "postal_code", "country", "phone", "company_size", "website", "linkedin_url", "data_source", "source_reference", "notes"):
            setattr(company, field, values[field].strip())
        company.tax_id = normalized_tax_id
        company.data_retrieved_at = data_retrieved_at
        updated = self.repository.update(company)
        logger.info("Company updated: id=%s", updated.id)
        self._crud_logger.info("company.updated entity_id=%s", updated.id)
        return updated

    def delete_company(self, company_id: int, *, delete_linked: bool = False) -> bool:
        if delete_linked:
            deleted = self.repository.delete(company_id, delete_linked=True)
        else:
            deleted = self.repository.delete(company_id)
        if deleted:
            logger.info("Company deleted: id=%s", company_id)
            self._crud_logger.info("company.deleted entity_id=%s", company_id)
        return deleted

    def list_companies(self) -> list[Company]: return self.repository.get_all()
    def search_companies(self, query: str) -> list[Company]: return self.repository.search(query)
    def count_companies(self) -> int: return self.repository.count()

    def _validate_required_fields(self, *, name: str, city: str) -> None:
        if not name or not name.strip():
            raise ValueError("Nome é obrigatório.")
        if not city or not city.strip():
            raise ValueError("Cidade é obrigatória.")

    def _validate_duplicate(self, *, name: str, website: str, tax_id: str = "", exclude_id: int | None = None) -> None:
        if tax_id and self.repository.exists_by_tax_id(tax_id, exclude_id=exclude_id):
            raise ValueError("Já existe uma empresa cadastrada com este CNPJ.")
        if self.repository.exists_by_name_and_website(name=name, website=website, exclude_id=exclude_id):
            raise ValueError("Empresa duplicada: nome + site já cadastrado.")

    @staticmethod
    def _normalize_tax_id(value: str) -> str:
        digits = "".join(character for character in value if character.isdigit())
        if digits and len(digits) != 14:
            raise ValueError("CNPJ deve conter 14 dígitos.")
        return digits


def _build_crud_logger() -> logging.Logger:
    audit_logger = logging.getLogger("acd.audit.company")
    audit_logger.setLevel(logging.INFO)
    audit_logger.propagate = False
    if not audit_logger.handlers:
        audit_logger.addHandler(logging.NullHandler())
    return audit_logger
