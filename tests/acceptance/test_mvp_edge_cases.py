from __future__ import annotations

from tests.acceptance.test_mvp_workflow_and_persistence import _seed_mvp_flow


def test_mvp_searches_handle_no_results_and_recover(acceptance_runtime) -> None:
    """All productive searches must show an empty state and recover cleanly."""

    _seed_mvp_flow(acceptance_runtime)

    search_cases = (
        (
            acceptance_runtime.company_page.search_input,
            acceptance_runtime.company_page._search_companies,
            acceptance_runtime.company_page.table,
        ),
        (
            acceptance_runtime.job_page.search_input,
            acceptance_runtime.job_page._filter_jobs,
            acceptance_runtime.job_page.table,
        ),
        (
            acceptance_runtime.curriculum_page.search_input,
            acceptance_runtime.curriculum_page._search_curricula,
            acceptance_runtime.curriculum_page.table,
        ),
        (
            acceptance_runtime.application_page.search_input,
            acceptance_runtime.application_page._filter_applications,
            acceptance_runtime.application_page.table,
        ),
        (
            acceptance_runtime.interview_page.search_input,
            acceptance_runtime.interview_page._filter_interviews,
            acceptance_runtime.interview_page.table,
        ),
    )

    for search_input, apply_search, table in search_cases:
        search_input.setText("registro-que-nao-existe")
        apply_search()
        assert table.rowCount() == 0

        search_input.clear()
        apply_search()
        assert table.rowCount() == 1


def test_mvp_repository_results_keep_required_relationships_loaded(
    acceptance_runtime,
) -> None:
    """Application rows must remain usable after repository sessions close."""

    ids = _seed_mvp_flow(acceptance_runtime)

    application = acceptance_runtime.application_service.get_application(
        ids["application_id"]
    )

    assert application is not None
    assert application.job is not None
    assert application.job.title == "Analista de Dados"
    assert application.company is not None
    assert application.company.name == "Empresa Sintetica Ltda"
    assert application.curriculum_id == ids["curriculum_id"]
    assert application.curriculum_version == "v1.0"


def test_mvp_unicode_content_survives_persistence(acceptance_runtime) -> None:
    """User-entered Portuguese and Unicode text must not be corrupted."""

    created = acceptance_runtime.company_service.create_company(
        name="Empresa São José — Pesquisa & Desenvolvimento",
        city="São Paulo",
        segment="Tecnologia",
        notes="Acentuação: ação, currículo, entrevista; símbolo: ✓",
    )

    loaded = acceptance_runtime.company_service.repository.get_by_id(created.id)

    assert loaded is not None
    assert loaded.name == "Empresa São José — Pesquisa & Desenvolvimento"
    assert loaded.city == "São Paulo"
    assert loaded.notes == "Acentuação: ação, currículo, entrevista; símbolo: ✓"
