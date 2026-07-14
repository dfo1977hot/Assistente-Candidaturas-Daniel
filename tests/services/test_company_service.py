"""Tests for CompanyService."""

from __future__ import annotations

import logging

import pytest

from acd.models.company import Company
from acd.services.company_service import (
    CompanyService,
    _build_crud_logger,
)


class FakeRepository:
    """Fake repository for CompanyService tests."""

    def __init__(self) -> None:
        self.company: Company | None = None
        self.deleted = False
        self.duplicate = False

    def create(self, company: Company) -> Company:
        company.id = 1
        self.company = company
        return company

    def update(self, company: Company) -> Company:
        self.company = company
        return company

    def delete(self, company_id: int) -> bool:
        return self.deleted

    def get_by_id(self, company_id: int) -> Company | None:
        return self.company

    def get_all(self) -> list[Company]:
        if self.company is None:
            return []
        return [self.company]

    def search(self, query: str) -> list[Company]:
        if self.company is None:
            return []
        return [self.company]

    def count(self) -> int:
        return 1 if self.company else 0

    def exists_by_name_and_website(
        self,
        *,
        name: str,
        website: str,
        exclude_id: int | None = None,
    ) -> bool:
        return self.duplicate


def create_service() -> CompanyService:
    """Create CompanyService with fake repository."""

    service = CompanyService.__new__(CompanyService)

    service.repository = FakeRepository()
    service._crud_logger = logging.getLogger("TEST")

    return service


def create_company() -> Company:
    """Create fake company."""

    company = Company(
        name="OpenAI",
        city="São Paulo",
        segment="Technology",
        state="SP",
        country="Brasil",
        company_size="Grande",
        website="https://openai.com",
        linkedin_url="https://linkedin.com/company/openai",
        notes="Observações",
    )

    company.id = 1

    return company


# ==========================================================
# create_company
# ==========================================================


def test_create_company() -> None:
    """Should create company."""

    service = create_service()

    company = service.create_company(
        name="OpenAI",
        city="São Paulo",
        segment="Technology",
        state="SP",
        country="Brasil",
        company_size="Grande",
        website="https://openai.com",
        linkedin_url="https://linkedin.com/company/openai",
        notes="Observações",
    )

    assert company.id == 1
    assert company.name == "OpenAI"
    assert company.city == "São Paulo"


def test_create_company_trims_fields() -> None:
    """Should trim string fields."""

    service = create_service()

    company = service.create_company(
        name="  OpenAI  ",
        city="  São Paulo ",
        segment=" Technology ",
        state=" SP ",
        country=" Brasil ",
        company_size=" Grande ",
        website=" https://openai.com ",
        linkedin_url=" https://linkedin.com/company/openai ",
        notes=" Notes ",
    )

    assert company.name == "OpenAI"
    assert company.city == "São Paulo"
    assert company.segment == "Technology"
    assert company.state == "SP"
    assert company.country == "Brasil"
    assert company.company_size == "Grande"
    assert company.website == "https://openai.com"
    assert company.linkedin_url == "https://linkedin.com/company/openai"
    assert company.notes == "Notes"


def test_create_company_duplicate() -> None:
    """Should reject duplicate company."""

    service = create_service()

    service.repository.duplicate = True

    with pytest.raises(ValueError, match="Empresa duplicada"):
        service.create_company(
            name="OpenAI",
            city="São Paulo",
            website="https://openai.com",
        )


def test_create_company_missing_name() -> None:
    """Should require company name."""

    service = create_service()

    with pytest.raises(ValueError, match="Nome é obrigatório"):
        service.create_company(
            name="",
            city="São Paulo",
        )


def test_create_company_missing_city() -> None:
    """Should require city."""

    service = create_service()

    with pytest.raises(ValueError, match="Cidade é obrigatória"):
        service.create_company(
            name="OpenAI",
            city="",
        )
        # ==========================================================
# update_company
# ==========================================================


def test_update_company() -> None:
    """Should update existing company."""

    service = create_service()

    service.repository.company = create_company()

    updated = service.update_company(
        1,
        name="OpenAI Brasil",
        city="Campinas",
        segment="AI",
        state="SP",
        country="Brasil",
        company_size="Muito Grande",
        website="https://openai.com.br",
        linkedin_url="https://linkedin.com/company/openai-br",
        notes="Atualizada",
    )

    assert updated is not None
    assert updated.name == "OpenAI Brasil"
    assert updated.city == "Campinas"
    assert updated.segment == "AI"
    assert updated.website == "https://openai.com.br"


def test_update_company_trims_fields() -> None:
    """Should trim updated fields."""

    service = create_service()

    service.repository.company = create_company()

    updated = service.update_company(
        1,
        name=" OpenAI ",
        city=" São Paulo ",
        segment=" Technology ",
        state=" SP ",
        country=" Brasil ",
        company_size=" Grande ",
        website=" https://openai.com ",
        linkedin_url=" https://linkedin.com/company/openai ",
        notes=" Teste ",
    )

    assert updated is not None
    assert updated.name == "OpenAI"
    assert updated.city == "São Paulo"
    assert updated.segment == "Technology"
    assert updated.state == "SP"
    assert updated.country == "Brasil"
    assert updated.company_size == "Grande"
    assert updated.website == "https://openai.com"
    assert updated.linkedin_url == "https://linkedin.com/company/openai"
    assert updated.notes == "Teste"


def test_update_company_not_found() -> None:
    """Should return None when company does not exist."""

    service = create_service()

    result = service.update_company(
        999,
        name="OpenAI",
        city="São Paulo",
    )

    assert result is None


def test_update_company_duplicate() -> None:
    """Should reject duplicate company."""

    service = create_service()

    service.repository.company = create_company()
    service.repository.duplicate = True

    with pytest.raises(ValueError, match="Empresa duplicada"):
        service.update_company(
            1,
            name="OpenAI",
            city="São Paulo",
            website="https://openai.com",
        )


# ==========================================================
# delete_company
# ==========================================================


def test_delete_company() -> None:
    """Should delete company."""

    service = create_service()

    service.repository.deleted = True

    assert service.delete_company(1) is True


def test_delete_company_not_found() -> None:
    """Should return False when company is not found."""

    service = create_service()

    service.repository.deleted = False

    assert service.delete_company(1) is False


# ==========================================================
# list / search / count
# ==========================================================


def test_list_companies() -> None:
    """Should list companies."""

    service = create_service()

    service.repository.company = create_company()

    companies = service.list_companies()

    assert len(companies) == 1
    assert companies[0].name == "OpenAI"


def test_search_companies() -> None:
    """Should search companies."""

    service = create_service()

    service.repository.company = create_company()

    companies = service.search_companies("Open")

    assert len(companies) == 1
    assert companies[0].name == "OpenAI"


def test_count_companies() -> None:
    """Should count companies."""

    service = create_service()

    assert service.count_companies() == 0

    service.repository.company = create_company()

    assert service.count_companies() == 1
    # ==========================================================
# private methods
# ==========================================================


def test_validate_required_fields_name() -> None:
    """Should validate required company name."""

    service = create_service()

    with pytest.raises(ValueError, match="Nome é obrigatório"):
        service._validate_required_fields(
            name="",
            city="São Paulo",
        )

    with pytest.raises(ValueError, match="Nome é obrigatório"):
        service._validate_required_fields(
            name="   ",
            city="São Paulo",
        )


def test_validate_required_fields_city() -> None:
    """Should validate required city."""

    service = create_service()

    with pytest.raises(ValueError, match="Cidade é obrigatória"):
        service._validate_required_fields(
            name="OpenAI",
            city="",
        )

    with pytest.raises(ValueError, match="Cidade é obrigatória"):
        service._validate_required_fields(
            name="OpenAI",
            city="   ",
        )


def test_validate_duplicate_false() -> None:
    """Should accept non-duplicate company."""

    service = create_service()

    service.repository.duplicate = False

    service._validate_duplicate(
        name="OpenAI",
        website="https://openai.com",
    )


def test_validate_duplicate_true() -> None:
    """Should reject duplicate company."""

    service = create_service()

    service.repository.duplicate = True

    with pytest.raises(ValueError, match="Empresa duplicada"):
        service._validate_duplicate(
            name="OpenAI",
            website="https://openai.com",
        )


# ==========================================================
# _build_crud_logger
# ==========================================================


def test_build_crud_logger() -> None:
    """Should create and reuse CRUD logger."""

    logger1 = _build_crud_logger()

    assert isinstance(logger1, logging.Logger)
    assert logger1.level == logging.INFO
    assert logger1.handlers
    assert logger1.propagate is False

    handlers_before = len(logger1.handlers)

    logger2 = _build_crud_logger()

    assert logger1 is logger2
    assert len(logger2.handlers) == handlers_before