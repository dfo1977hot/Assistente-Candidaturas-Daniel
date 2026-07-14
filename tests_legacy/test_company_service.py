from __future__ import annotations

from acd.services.company_service import CompanyService


def test_service_creates_and_searches_company(
    company_service: CompanyService,
):
    created = company_service.create_company(
        name="Acme",
        segment="Tecnologia",
        city="São Paulo",
        state="SP",
        country="Brasil",
        company_size="Grande",
        website="https://acme.com",
    )

    assert created.id is not None
    assert company_service.count_companies() == 1

    companies = company_service.search_companies("Acme")

    assert len(companies) == 1
    assert companies[0].name == "Acme"


def test_service_updates_and_deletes_company(
    company_service: CompanyService,
):
    created = company_service.create_company(
        name="Acme",
        segment="Tecnologia",
        city="São Paulo",
        state="SP",
        country="Brasil",
        company_size="Grande",
    )

    updated = company_service.update_company(
        created.id,
        name="Acme LTDA",
        segment="Tecnologia",
        city="Campinas",
        state="SP",
        country="Brasil",
        company_size="Grande",
    )

    assert updated is not None
    assert updated.name == "Acme LTDA"

    assert company_service.delete_company(created.id)

    assert company_service.count_companies() == 0