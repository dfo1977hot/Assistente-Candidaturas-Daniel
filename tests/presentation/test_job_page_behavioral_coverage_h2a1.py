from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QMessageBox, QTableWidgetItem

from acd.presentation.pages.job_page import JobPage, _is_integrity_error


class _CompanyService:
    def __init__(self) -> None:
        self.companies = [
            SimpleNamespace(
                id=1,
                name="Empresa Alpha",
            ),
            SimpleNamespace(
                id=2,
                name="Empresa Beta",
            ),
        ]

    def list_companies(self):
        return list(self.companies)


class _JobService:
    def __init__(self) -> None:
        company = SimpleNamespace(
            id=1,
            name="Empresa Alpha",
        )

        self.job = SimpleNamespace(
            id=10,
            company_id=1,
            company=company,
            title="Engenheiro de Produção",
            location="Guarulhos - SP",
            work_model="Híbrido",
            employment_type="CLT",
            salary_min=10000.0,
            salary_max=13000.0,
            currency="BRL",
            status="Nova",
            source="LinkedIn",
            job_url="https://example.com/job",
            application_url="https://example.com/apply",
            recruiter="Maria",
            recruiter_email="maria@example.com",
            application_deadline=QDate(2026, 8, 31),
            application_date=QDate(2026, 8, 10),
            priority=4,
            notes=(
                "Observação principal\n\n"
                "[BENEFICIOS]\n"
                "Vale-refeição\nPlano de saúde\n"
                "[/BENEFICIOS]"
            ),
            created_at=datetime(2026, 8, 10, 9, 30),
        )

        self.jobs = [self.job]
        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[int, dict[str, object]]] = []
        self.deleted: list[tuple[int, bool]] = []
        self.search_queries: list[str] = []
        self.filter_calls: list[dict[str, object]] = []
        self.delete_result = True
        self.delete_error: Exception | None = None

    def list_jobs(self):
        return list(self.jobs)

    def search_jobs(self, query: str):
        self.search_queries.append(query)
        return list(self.jobs)

    def filter_jobs(self, **filters):
        self.filter_calls.append(dict(filters))
        return list(self.jobs)

    def get_job(self, job_id: int):
        if job_id == 10:
            return self.job
        return None

    def create_job(self, **data):
        self.created.append(dict(data))
        return self.job

    def update_job(
        self,
        job_id: int,
        **data,
    ):
        self.updated.append(
            (
                job_id,
                dict(data),
            )
        )
        return self.job

    def delete_job(
        self,
        job_id: int,
        *,
        delete_linked: bool = False,
    ):
        if self.delete_error is not None:
            error = self.delete_error
            self.delete_error = None
            raise error

        self.deleted.append(
            (
                job_id,
                delete_linked,
            )
        )
        return self.delete_result


def _page():
    job_service = _JobService()
    company_service = _CompanyService()

    page = JobPage(
        job_service=job_service,  # type: ignore[arg-type]
        company_service=company_service,  # type: ignore[arg-type]
    )

    return page, job_service, company_service


def test_job_page_loads_companies_and_jobs(qapp) -> None:
    page, _jobs, _companies = _page()

    assert page.company_combo.count() == 3
    assert page.filter_company_combo.count() == 3
    assert page.table.rowCount() == 1

    assert page.table.item(0, 0).text() == "10"
    assert page.table.item(0, 1).text() == "Empresa Alpha"
    assert page.table.item(0, 2).text() == "Engenheiro de Produção"
    assert page.table.item(0, 3).text() == "Nova"
    assert page.table.item(0, 4).text() == "Guarulhos - SP"
    assert page.table.item(0, 5).text() == "10/08/2026"


def test_job_page_refresh_reference_data_restores_company(
    qapp,
) -> None:
    page, _jobs, _companies = _page()

    page.company_combo.setCurrentIndex(
        page.company_combo.findData(2)
    )

    page.refresh_reference_data()
    qapp.processEvents()

    assert page.company_combo.currentData() == 2
    assert page.table.rowCount() == 1


def test_job_page_filters_by_search_status_company_and_all(
    qapp,
) -> None:
    page, jobs, _companies = _page()

    page.search_input.setText("engenheiro")
    page._filter_jobs()

    assert jobs.search_queries == ["engenheiro"]

    page.search_input.clear()
    page.filter_company_combo.setCurrentIndex(
        page.filter_company_combo.findData(1)
    )
    page.filter_status_combo.setCurrentText("Nova")
    page._filter_jobs()

    assert jobs.filter_calls[-1] == {
        "company_id": 1,
        "status": "Nova",
    }

    page.filter_company_combo.setCurrentIndex(0)
    page.filter_status_combo.setCurrentIndex(0)
    page._filter_jobs()

    assert page.table.rowCount() == 1


def test_job_page_selects_row_and_populates_form(qapp) -> None:
    page, _jobs, _companies = _page()

    page.table.selectRow(0)
    qapp.processEvents()

    assert page.current_job_id == 10
    assert page.company_combo.currentData() == 1
    assert page.title_input.text() == "Engenheiro de Produção"
    assert page.location_input.text() == "Guarulhos - SP"
    assert page.work_model_combo.currentText() == "Híbrido"
    assert page.employment_type_combo.currentText() == "CLT"
    assert page.salary_min_input.value() == 10000.0
    assert page.salary_max_input.value() == 13000.0
    assert page.currency_input.currentText() == "BRL"
    assert page.status_combo.currentText() == "Nova"
    assert page.source_input.text() == "LinkedIn"
    assert page.url_input.text() == "https://example.com/job"
    assert (
        page.application_url_input.text()
        == "https://example.com/apply"
    )
    assert page.recruiter_input.text() == "Maria"
    assert page.recruiter_email_input.text() == "maria@example.com"
    assert page.priority_input.value() == 4
    assert "Vale-refeição" in page.benefits_input.toPlainText()
    assert page.notes_input.toPlainText() == "Observação principal"


def test_job_page_row_selection_without_selection_is_ignored(
    qapp,
) -> None:
    page, _jobs, _companies = _page()

    page.table.clearSelection()
    page.current_job_id = None

    page._on_row_selected()

    assert page.current_job_id is None


def test_job_page_row_selection_handles_missing_job(qapp) -> None:
    page, jobs, _companies = _page()

    page.table.setRowCount(1)
    page.table.setItem(
        0,
        0,
        QTableWidgetItem("999"),
    )

    page.table.selectRow(0)

    page._on_row_selected()

    assert page.current_job_id == 999
    assert jobs.get_job(999) is None


def test_job_page_select_job_row_by_id(qapp) -> None:
    page, _jobs, _companies = _page()

    page.table.clearSelection()

    page._select_job_row_by_id(None)

    assert page.table.selectionModel().selectedRows() == []

    page._select_job_row_by_id(10)
    qapp.processEvents()

    selected = page.table.selectionModel().selectedRows()

    assert len(selected) == 1
    assert selected[0].row() == 0

    page.table.clearSelection()
    page._select_job_row_by_id(999)

    assert page.table.selectionModel().selectedRows() == []


def test_job_page_clear_form_resets_edit_state(qapp) -> None:
    page, _jobs, _companies = _page()

    page.current_job_id = 10
    page.company_combo.setCurrentIndex(
        page.company_combo.findData(1)
    )
    page.title_input.setText("Cargo")
    page.location_input.setText("Cidade")
    page.work_model_combo.setCurrentText("Remoto")
    page.salary_min_input.setValue(1000)
    page.salary_max_input.setValue(2000)
    page.source_input.setText("Fonte")
    page.url_input.setText("https://example.com")
    page.application_url_input.setText(
        "https://example.com/apply"
    )
    page.recruiter_input.setText("Maria")
    page.recruiter_email_input.setText("maria@example.com")
    page.priority_input.setValue(5)
    page.benefits_input.setPlainText("Benefício")
    page.notes_input.setPlainText("Nota")
    page.table.selectRow(0)

    page._clear_form()
    qapp.processEvents()

    assert page.current_job_id is None
    assert page.company_combo.currentIndex() == 0
    assert page.title_input.text() == ""
    assert page.location_input.text() == ""
    assert page.work_model_combo.currentText() == "Presencial"
    assert page.salary_min_input.value() == 0
    assert page.salary_max_input.value() == 0
    assert page.source_input.text() == ""
    assert page.url_input.text() == ""
    assert page.application_url_input.text() == ""
    assert page.recruiter_input.text() == ""
    assert page.recruiter_email_input.text() == ""
    assert page.priority_input.value() == 3
    assert page.benefits_input.toPlainText() == ""
    assert page.notes_input.toPlainText() == ""
    assert page.table.selectionModel().selectedRows() == []


def test_job_page_currency_updates_salary_prefixes(qapp) -> None:
    page, _jobs, _companies = _page()

    expected = {
        "BRL": "R$ ",
        "USD": "US$ ",
        "EUR": "€ ",
        "GBP": "£ ",
    }

    for currency, prefix in expected.items():
        page.currency_input.setCurrentText(currency)
        page._update_currency_symbol()

        assert page.salary_min_input.prefix() == prefix
        assert page.salary_max_input.prefix() == prefix

    page.currency_input.addItem("XYZ")
    page.currency_input.setCurrentText("XYZ")
    page._update_currency_symbol()

    assert page.salary_min_input.prefix() == "R$ "
    assert page.salary_max_input.prefix() == "R$ "


def test_job_page_offered_remuneration_helpers(qapp) -> None:
    page, _jobs, _companies = _page()

    page._set_offered_remuneration(None)

    assert page.salary_min_input.value() == 0.0
    assert page._parse_offered_remuneration() is None

    page._set_offered_remuneration(12345.67)

    assert page.salary_min_input.value() == 12345.67
    assert page._parse_offered_remuneration() == 12345.67


def test_job_page_benefits_marker_helpers() -> None:
    notes = "Texto livre"
    benefits = "VR\nPlano de saúde"

    combined = JobPage._notes_with_benefits(
        notes,
        benefits,
    )

    assert "Texto livre" in combined
    assert "[BENEFICIOS]" in combined
    assert "VR" in combined
    assert "[/BENEFICIOS]" in combined

    assert JobPage._extract_benefits_marker(
        combined
    ) == "VR\nPlano de saúde"

    assert JobPage._strip_benefits_marker(
        combined
    ) == "Texto livre"

    assert JobPage._notes_with_benefits(
        "Texto",
        "",
    ) == "Texto"

    assert JobPage._extract_benefits_marker(
        "Texto sem marcador"
    ) == ""

    assert JobPage._strip_benefits_marker(
        "Texto sem marcador"
    ) == "Texto sem marcador"


def test_job_page_format_benefits_helper() -> None:
    assert JobPage._format_benefits(None) == ""
    assert JobPage._format_benefits("  VR  ") == "VR"

    assert JobPage._format_benefits(
        [
            "VR",
            "",
            " Plano ",
        ]
    ) == "VR\nPlano"

    assert JobPage._format_benefits(
        (
            "Seguro",
            "VT",
        )
    ) == "Seguro\nVT"

    assert JobPage._format_benefits(
        {
            "A",
            "B",
        }
    ) in {
        "A\nB",
        "B\nA",
    }

    assert JobPage._format_benefits(123) == "123"


def test_job_page_parse_optional_number(qapp) -> None:
    page, _jobs, _companies = _page()

    assert page._parse_optional_number("") is None
    assert page._parse_optional_number("   ") is None
    assert page._parse_optional_number("123.45") == 123.45


def test_job_page_delete_requires_selection(
    qapp,
    monkeypatch,
) -> None:
    page, jobs, _companies = _page()

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page.current_job_id = None
    page._delete_job()

    assert jobs.deleted == []
    assert messages


def test_job_page_delete_can_be_cancelled(
    qapp,
    monkeypatch,
) -> None:
    page, jobs, _companies = _page()

    page.current_job_id = 10

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.No,
    )

    page._delete_job()

    assert jobs.deleted == []


def test_job_page_delete_successfully_removes_job(
    qapp,
    monkeypatch,
) -> None:
    page, jobs, _companies = _page()

    page.current_job_id = 10

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_job()

    assert jobs.deleted == [
        (
            10,
            False,
        )
    ]

    assert page.current_job_id is None


def test_job_page_delete_false_result_warns(
    qapp,
    monkeypatch,
) -> None:
    page, jobs, _companies = _page()

    jobs.delete_result = False
    page.current_job_id = 10

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._delete_job()

    assert warnings == [
        "A vaga não pôde ser excluída."
    ]


def test_job_page_delete_non_integrity_error_is_reported(
    qapp,
    monkeypatch,
) -> None:
    page, jobs, _companies = _page()

    jobs.delete_error = RuntimeError("Falha controlada")
    page.current_job_id = 10

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._delete_job()

    assert messages
    assert "Falha controlada" in messages[-1]


def test_integrity_error_helper_walks_exception_chain() -> None:
    class IntegrityError(Exception):
        pass

    root = IntegrityError("constraint")
    wrapped = RuntimeError("wrapped")
    wrapped.__cause__ = root

    assert _is_integrity_error(root) is True
    assert _is_integrity_error(wrapped) is True
    assert _is_integrity_error(RuntimeError("other")) is False


def test_job_page_populate_form_handles_optional_values(
    qapp,
) -> None:
    page, _jobs, _companies = _page()

    job = SimpleNamespace(
        company_id=999,
        title=None,
        location=None,
        work_model=None,
        employment_type=None,
        salary_min=None,
        salary_max=None,
        currency="INVALID",
        status=None,
        source=None,
        job_url=None,
        application_url=None,
        recruiter=None,
        recruiter_email=None,
        application_deadline=None,
        application_date=None,
        priority=None,
        notes=None,
    )

    page._populate_form(job)

    assert page.title_input.text() == ""
    assert page.location_input.text() == ""
    assert page.work_model_combo.currentText() == "Presencial"
    assert page.salary_min_input.value() == 0
    assert page.salary_max_input.value() == 0
    assert page.status_combo.currentText() == "Nova"
    assert page.source_input.text() == ""
    assert page.url_input.text() == ""
    assert page.application_url_input.text() == ""
    assert page.recruiter_input.text() == ""
    assert page.recruiter_email_input.text() == ""
    assert page.priority_input.value() == 3
    assert page.benefits_input.toPlainText() == ""
    assert page.notes_input.toPlainText() == ""


def test_job_page_render_jobs_handles_empty_optional_values(
    qapp,
) -> None:
    page, _jobs, _companies = _page()

    job = SimpleNamespace(
        id=99,
        company=None,
        title="Cargo",
        status=None,
        location=None,
        created_at=None,
    )

    page._render_jobs([job])

    assert page.table.rowCount() == 1
    assert page.table.item(0, 0).text() == "99"
    assert page.table.item(0, 1).text() == ""
    assert page.table.item(0, 2).text() == "Cargo"
    assert page.table.item(0, 3).text() == ""
    assert page.table.item(0, 4).text() == ""
    assert page.table.item(0, 5).text() == ""