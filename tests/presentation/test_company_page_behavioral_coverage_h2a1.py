from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from PySide6.QtWidgets import QDialog, QMessageBox

import acd.presentation.pages.company_page as company_page_module
from acd.presentation.pages.company_page import (
    CompanyPage,
    _is_integrity_error,
)


class _Repository:
    def __init__(self, company) -> None:
        self.company = company

    def get_by_id(self, company_id: int):
        if company_id == self.company.id:
            return self.company
        return None


class _CompanyService:
    def __init__(self) -> None:
        self.company = SimpleNamespace(
            id=1,
            name="Empresa Alpha",
            legal_name="Empresa Alpha Ltda.",
            tax_id="12.345.678/0001-90",
            registration_status="ATIVA",
            segment="Logística",
            address="Rua A, 100",
            postal_code="07000-000",
            phone="(11) 99999-9999",
            city="Guarulhos",
            state="SP",
            country="Brasil",
            company_size="Grande",
            website="https://alpha.example.com",
            linkedin_url="https://linkedin.com/company/alpha",
            notes="Observações",
            data_source="ReceitaWS",
            source_reference="ref-1",
            data_retrieved_at=datetime(2026, 8, 14, 8, 0),
            created_at=datetime(2026, 8, 1, 10, 0),
        )

        self.repository = _Repository(self.company)

        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[int, dict[str, object]]] = []
        self.deleted: list[tuple[int, bool]] = []

        self.create_result = self.company
        self.update_result = self.company
        self.delete_outcomes: list[object] = []

        self.search_query = ""

    def list_companies(self):
        return [self.company]

    def search_companies(self, query: str):
        self.search_query = query
        return [self.company]

    def create_company(self, **data):
        self.created.append(dict(data))
        return self.create_result

    def update_company(
        self,
        company_id: int,
        **data,
    ):
        self.updated.append(
            (
                company_id,
                dict(data),
            )
        )
        return self.update_result

    def delete_company(
        self,
        company_id: int,
        *,
        delete_linked: bool = False,
    ):
        self.deleted.append(
            (
                company_id,
                delete_linked,
            )
        )

        if self.delete_outcomes:
            outcome = self.delete_outcomes.pop(0)

            if isinstance(outcome, BaseException):
                raise outcome

            return outcome

        return True


class _LookupGateway:
    def __init__(self) -> None:
        self.calls: list[tuple[str, bool]] = []

    def search(
        self,
        name: str,
        *,
        force_refresh: bool = False,
    ):
        self.calls.append(
            (
                name,
                force_refresh,
            )
        )

        return []


class _Executor:
    def __init__(
        self,
        *,
        is_running: bool = False,
        cancel_result: bool = True,
    ) -> None:
        self.is_running = is_running
        self.cancel_result = cancel_result
        self.tasks = []

    def execute(self, task):
        self.tasks.append(task)
        return task()

    def cancel(self):
        return self.cancel_result


class _LookupDialog:
    result_code = QDialog.Accepted
    selected = None

    def __init__(self, results, parent) -> None:
        self.results = results
        self.parent = parent

    def exec(self):
        return self.result_code

    def selected_result(self):
        return self.selected


class IntegrityError(Exception):
    pass


def _page(
    *,
    lookup_factory=None,
):
    service = _CompanyService()

    page = CompanyPage(
        service,  # type: ignore[arg-type]
        lookup_factory,
    )

    return page, service


def _fill_form(page: CompanyPage) -> None:
    page.name_input.setText("Empresa Nova")
    page.legal_name_input.setText("Empresa Nova Ltda.")
    page.tax_id_input.setText("98.765.432/0001-10")
    page.registration_status_input.setText("ATIVA")
    page.segment_input.setText("Indústria")
    page.address_input.setText("Avenida B, 200")
    page.postal_code_input.setText("07100-000")
    page.phone_input.setText("(11) 98888-8888")
    page.city_input.setText("Guarulhos")
    page.state_input.setText("SP")
    page.country_input.setText("Brasil")
    page.company_size_input.setText("Médio")
    page.website_input.setText("https://nova.example.com")
    page.linkedin_input.setText(
        "https://linkedin.com/company/nova"
    )
    page.notes_input.setPlainText("Notas da empresa")


def _lookup_result():
    return SimpleNamespace(
        name="Empresa Encontrada",
        legal_name="Empresa Encontrada S.A.",
        tax_id="11.111.111/0001-11",
        registration_status="ATIVA",
        segment="Tecnologia",
        address="Rua Pesquisa, 10",
        city="São Paulo",
        state="SP",
        postal_code="01000-000",
        country="Brasil",
        phone="(11) 90000-0000",
        website="https://encontrada.example.com",
        source="OpenAI",
        source_reference="https://example.com/source",
        retrieved_at=datetime(2026, 8, 14, 8, 0),
        confidence=0.95,
    )


def test_initial_load_renders_company(qapp) -> None:
    page, _service = _page()

    assert page.table.rowCount() == 1
    assert page.table.item(0, 0).text() == "1"
    assert page.table.item(0, 1).text() == "Empresa Alpha"
    assert page.table.item(0, 2).text() == "Logística"
    assert page.table.item(0, 3).text() == "Guarulhos"
    assert page.table.item(0, 4).text() == "Grande"
    assert (
        page.table.item(0, 5).text()
        == "https://alpha.example.com"
    )
    assert page.table.item(0, 6).text() == "01/08/2026"


def test_lookup_requires_two_characters(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.name_input.setText("A")
    page._lookup_company()

    assert warnings == [
        "Informe pelo menos dois caracteres do nome da empresa."
    ]


def test_lookup_ignores_request_when_executor_running(
    qapp,
) -> None:
    gateway = _LookupGateway()

    page, _service = _page(
        lookup_factory=lambda _provider: gateway,
    )

    page.name_input.setText("Empresa")
    page._lookup_executor = _Executor(  # type: ignore[assignment]
        is_running=True
    )

    page._lookup_company()

    assert gateway.calls == []


def test_lookup_warns_when_factory_unavailable(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.name_input.setText("Empresa")
    page._lookup_company()

    assert (
        page.lookup_status.text()
        == "Serviço de busca indisponível."
    )
    assert warnings == [
        "O serviço de busca de empresas não está disponível."
    ]


def test_lookup_executes_selected_provider_and_force_refresh(
    qapp,
) -> None:
    gateway = _LookupGateway()
    providers: list[str] = []

    def factory(provider: str):
        providers.append(provider)
        return gateway

    page, _service = _page(
        lookup_factory=factory,
    )

    executor = _Executor()
    page._lookup_executor = executor  # type: ignore[assignment]

    page.name_input.setText("Empresa Alpha")

    index = page.lookup_provider.findData("openai")
    page.lookup_provider.setCurrentIndex(index)

    page.force_refresh_checkbox.setChecked(True)

    page._lookup_company()

    assert providers == ["openai"]
    assert gateway.calls == [
        (
            "Empresa Alpha",
            True,
        )
    ]

    assert (
        page.lookup_status.text()
        == "Buscando dados..."
    )
    assert not page.lookup_button.isEnabled()
    assert page.cancel_lookup_button.isEnabled()


def test_cancel_lookup_updates_status(qapp) -> None:
    page, _service = _page()

    page._lookup_executor = _Executor(  # type: ignore[assignment]
        cancel_result=True
    )

    page._cancel_lookup()

    assert page.lookup_status.text().startswith(
        "Cancelamento solicitado"
    )
    assert not page.cancel_lookup_button.isEnabled()


def test_cancel_lookup_does_nothing_when_cancel_fails(
    qapp,
) -> None:
    page, _service = _page()

    page.lookup_status.setText("Original")

    page._lookup_executor = _Executor(  # type: ignore[assignment]
        cancel_result=False
    )

    page._cancel_lookup()

    assert page.lookup_status.text() == "Original"


def test_lookup_success_with_empty_results(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._on_lookup_succeeded([])

    assert (
        page.lookup_status.text()
        == "Nenhuma empresa encontrada."
    )
    assert infos == [
        "Nenhuma empresa foi encontrada."
    ]


def test_lookup_success_can_apply_selected_result(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    result = _lookup_result()

    _LookupDialog.result_code = QDialog.Accepted
    _LookupDialog.selected = result

    monkeypatch.setattr(
        company_page_module,
        "CompanyLookupDialog",
        _LookupDialog,
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: None,
    )

    page._on_lookup_succeeded([result])

    assert (
        page.lookup_status.text()
        == "1 resultado(s) encontrado(s)."
    )
    assert page.name_input.text() == "Empresa Encontrada"
    assert (
        page.legal_name_input.text()
        == "Empresa Encontrada S.A."
    )
    assert page.tax_id_input.text() == "11.111.111/0001-11"
    assert page.segment_input.text() == "Tecnologia"
    assert page.city_input.text() == "São Paulo"
    assert page.state_input.text() == "SP"
    assert page.country_input.text() == "Brasil"

    assert page._lookup_metadata == {
        "data_source": "OpenAI",
        "source_reference": "https://example.com/source",
        "data_retrieved_at": datetime(2026, 8, 14, 8, 0),
    }


def test_lookup_success_can_decline_overwriting_existing_data(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    result = _lookup_result()

    _LookupDialog.result_code = QDialog.Accepted
    _LookupDialog.selected = result

    monkeypatch.setattr(
        company_page_module,
        "CompanyLookupDialog",
        _LookupDialog,
    )

    page.city_input.setText("Cidade existente")

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.No,
    )

    page._on_lookup_succeeded([result])

    assert page.city_input.text() == "Cidade existente"
    assert page.name_input.text() == ""


def test_lookup_cancelled_dialog_does_not_apply_result(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    result = _lookup_result()

    _LookupDialog.result_code = QDialog.Rejected
    _LookupDialog.selected = result

    monkeypatch.setattr(
        company_page_module,
        "CompanyLookupDialog",
        _LookupDialog,
    )

    page._on_lookup_succeeded([result])

    assert page.name_input.text() == ""


def test_lookup_failed_and_finished_restore_ui(
    qapp,
    monkeypatch,
) -> None:
    page, _service = _page()

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._set_lookup_running(True)

    assert not page.lookup_button.isEnabled()
    assert page.cancel_lookup_button.isEnabled()

    page._on_lookup_failed(
        RuntimeError("falha externa")
    )

    assert page.lookup_status.text() == "Falha na consulta."
    assert warnings == ["falha externa"]

    page._on_lookup_finished()

    assert page.lookup_button.isEnabled()
    assert not page.cancel_lookup_button.isEnabled()
    assert page.lookup_provider.isEnabled()
    assert page.force_refresh_checkbox.isEnabled()


def test_lookup_finished_converts_cancel_status(
    qapp,
) -> None:
    page, _service = _page()

    page.lookup_status.setText(
        "Cancelamento solicitado. Aguardando a consulta encerrar..."
    )

    page._on_lookup_finished()

    assert page.lookup_status.text() == "Consulta cancelada."


def test_save_company_creates_record(
    qapp,
) -> None:
    page, service = _page()

    _fill_form(page)

    page.current_company_id = None

    page._lookup_metadata = {
        "data_source": "OpenAI",
        "source_reference": "ref",
        "data_retrieved_at": datetime(2026, 8, 14, 8, 0),
    }

    page._save_company()

    assert len(service.created) == 1

    payload = service.created[0]

    assert payload["name"] == "Empresa Nova"
    assert payload["segment"] == "Indústria"
    assert payload["city"] == "Guarulhos"
    assert payload["state"] == "SP"
    assert payload["country"] == "Brasil"
    assert payload["company_size"] == "Médio"
    assert (
        payload["website"]
        == "https://nova.example.com"
    )
    assert (
        payload["linkedin_url"]
        == "https://linkedin.com/company/nova"
    )
    assert payload["data_source"] == "OpenAI"

    assert page.current_company_id == 1


def test_save_company_updates_current_record(
    qapp,
) -> None:
    page, service = _page()

    _fill_form(page)

    page.current_company_id = 1

    page._save_company()

    assert len(service.updated) == 1

    company_id, payload = service.updated[0]

    assert company_id == 1
    assert payload["name"] == "Empresa Nova"
    assert page.current_company_id == 1


def test_save_company_handles_missing_result(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    _fill_form(page)

    service.create_result = None

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.current_company_id = None

    page._save_company()

    assert warnings == [
        "A empresa não pôde ser salva."
    ]


def test_row_selection_populates_complete_company(
    qapp,
) -> None:
    page, _service = _page()

    page.table.selectRow(0)
    page._on_row_selected()

    assert page.current_company_id == 1
    assert page.name_input.text() == "Empresa Alpha"
    assert (
        page.legal_name_input.text()
        == "Empresa Alpha Ltda."
    )
    assert page.tax_id_input.text() == "12.345.678/0001-90"
    assert page.registration_status_input.text() == "ATIVA"
    assert page.address_input.text() == "Rua A, 100"
    assert page.postal_code_input.text() == "07000-000"
    assert page.phone_input.text() == "(11) 99999-9999"
    assert page.segment_input.text() == "Logística"
    assert page.city_input.text() == "Guarulhos"
    assert page.state_input.text() == "SP"
    assert page.country_input.text() == "Brasil"
    assert page.company_size_input.text() == "Grande"
    assert (
        page.linkedin_input.text()
        == "https://linkedin.com/company/alpha"
    )
    assert page.notes_input.toPlainText() == "Observações"


def test_search_companies_uses_query_and_empty_query(
    qapp,
) -> None:
    page, service = _page()

    page.search_input.setText("Alpha")
    page._search_companies()

    assert service.search_query == "Alpha"
    assert page.table.rowCount() == 1

    service.search_query = "unchanged"

    page.search_input.clear()
    page._search_companies()

    assert service.search_query == "unchanged"
    assert page.table.rowCount() == 1


def test_select_company_row_by_id_handles_none_and_match(
    qapp,
) -> None:
    page, _service = _page()

    page._select_company_row_by_id(None)

    assert not page.table.selectionModel().selectedRows()

    page._select_company_row_by_id(1)

    rows = page.table.selectionModel().selectedRows()

    assert len(rows) == 1
    assert rows[0].row() == 0


def test_clear_form_resets_all_fields(qapp) -> None:
    page, _service = _page()

    _fill_form(page)

    page.current_company_id = 1
    page._lookup_metadata = {
        "data_source": "OpenAI"
    }

    page._clear_form()

    assert page.current_company_id is None
    assert page.name_input.text() == ""
    assert page.legal_name_input.text() == ""
    assert page.tax_id_input.text() == ""
    assert page.registration_status_input.text() == ""
    assert page.address_input.text() == ""
    assert page.postal_code_input.text() == ""
    assert page.phone_input.text() == ""
    assert page.segment_input.text() == ""
    assert page.city_input.text() == ""
    assert page.state_input.text() == ""
    assert page.country_input.text() == ""
    assert page.company_size_input.text() == ""
    assert page.website_input.text() == ""
    assert page.linkedin_input.text() == ""
    assert page.notes_input.toPlainText() == ""
    assert page._lookup_metadata == {}


def test_delete_company_requires_selection(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = None

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._delete_company()

    assert infos == [
        "Selecione uma empresa para excluir."
    ]
    assert service.deleted == []


def test_delete_company_can_be_cancelled(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.No,
    )

    page._delete_company()

    assert service.deleted == []


def test_delete_company_success(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = 1

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_company()

    assert service.deleted == [
        (
            1,
            False,
        )
    ]

    assert page.current_company_id is None


def test_delete_company_false_result_warns(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = 1
    service.delete_outcomes = [False]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._delete_company()

    assert warnings == [
        "A empresa não pôde ser excluída."
    ]


def test_delete_company_integrity_error_can_cancel_cascade(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = 1
    service.delete_outcomes = [
        IntegrityError("foreign key"),
    ]

    answers = iter(
        (
            QMessageBox.Yes,
            QMessageBox.No,
        )
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: next(answers),
    )

    page._delete_company()

    assert service.deleted == [
        (
            1,
            False,
        )
    ]


def test_delete_company_integrity_error_can_cascade(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = 1

    service.delete_outcomes = [
        IntegrityError("foreign key"),
        True,
    ]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_company()

    assert service.deleted == [
        (
            1,
            False,
        ),
        (
            1,
            True,
        ),
    ]

    assert page.current_company_id is None


def test_delete_company_non_integrity_error_is_reported(
    qapp,
    monkeypatch,
) -> None:
    page, service = _page()

    page.current_company_id = 1

    service.delete_outcomes = [
        RuntimeError("database failure")
    ]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    critical: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: critical.append(
            str(message)
        ),
    )

    page._delete_company()

    assert len(critical) == 1
    assert "database failure" in critical[0]


def test_integrity_error_helper_checks_exception_chain() -> None:
    assert _is_integrity_error(
        IntegrityError("fk")
    )

    outer = RuntimeError("outer")

    try:
        raise IntegrityError("inner")
    except IntegrityError as exc:
        outer.__cause__ = exc

    assert _is_integrity_error(outer)

    assert not _is_integrity_error(
        RuntimeError("generic")
    )