from __future__ import annotations

import pytest

from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.services.company_service import CompanyService


@pytest.fixture
def company_repository(db_session):
    """
    Repositório de empresas.
    """

    return CompanyRepository()


@pytest.fixture
def company_service(company_repository):
    """
    Serviço de empresas.
    """

    return CompanyService(
        repository=company_repository,
    )


@pytest.fixture
def sample_company(company_service):
    """
    Empresa padrão utilizada nos testes.
    """

    return company_service.create_company(
        name="Acme",
        segment="Tecnologia",
        city="São Paulo",
        state="SP",
        country="Brasil",
        company_size="Grande",
        website="https://acme.com",
    )