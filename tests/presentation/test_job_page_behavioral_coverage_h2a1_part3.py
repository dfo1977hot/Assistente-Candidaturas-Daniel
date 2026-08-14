from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QMessageBox

import acd.presentation.pages.job_page as job_page_module
from acd.presentation.pages.job_page import JobPage


class _CompanyService:
    def list_companies(self):
        return [
            SimpleNamespace(id=1, name="Empresa Alpha"),
            SimpleNamespace(id=2, name="Empresa Beta"),
        ]


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
            job_url="https://www.linkedin.com/jobs/view/123",
            application_url="https://empresa.com/apply",
            recruiter="Maria",
            recruiter_email="maria@example.com",
            application_deadline=QDate(2026, 8, 31),
            application_date=QDate(2026, 8, 10),
            priority=3,
            notes="Observação",
            created_at=None,
        )

        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[int, dict[str, object]]] = []
        self.deleted: list[tuple[int, bool]] = []

        self.create_result = self.job
        self.update_result = self.job

        self.delete_outcomes: list[object] = []

    def list_jobs(self):
        return [self.job]

    def search_jobs(self, query: str):
        del query
        return [self.job]

    def filter_jobs(self, **filters):
        del filters
        return [self.job]

    def get_job(self, job_id: int):
        if job_id == 10:
            return self.job
        return None

    def create_job(self, **data):
        self.created.append(dict(data))
        return self.create_result

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
        return self.update_result

    def delete_job(
        self,
        job_id: int,
        *,
        delete_linked: bool = False,
    ):
        self.deleted.append(
            (
                job_id,
                delete_linked,
            )
        )

        if self.delete_outcomes:
            outcome = self.delete_outcomes.pop(0)

            if isinstance(outcome, Exception):
                raise outcome

            return outcome

        return True


class _SavedJobsService:
    def __init__(self) -> None:
        self.calls = 0

    def import_saved_jobs(
        self,
        *,
        progress_callback,
        cancellation_requested,
    ):
        self.calls += 1

        assert cancellation_requested() is False

        progress_callback(
            SimpleNamespace(
                stage="importing",
                message="Importando vagas",
            )
        )

        return SimpleNamespace(
            found=1,
            imported=1,
            existing=0,
            failed=0,
            companies_created=0,
            deleted=0,
        )


class _Executor:
    def __init__(self) -> None:
        self.tasks = []
        self.cancelled = False

    def execute_with_context(self, task):
        self.tasks.append(task)

        token = SimpleNamespace(
            is_cancellation_requested=False,
        )

        return task(
            lambda payload: setattr(
                self,
                "progress",
                payload,
            ),
            token,
        )

    def cancel(self):
        self.cancelled = True


class _Signal:
    def __init__(self) -> None:
        self.callbacks = []

    def connect(self, callback):
        self.callbacks.append(callback)


class _ProgressDialog:
    instances = []

    def __init__(self, parent) -> None:
        self.parent = parent
        self.cancel_requested = _Signal()
        self.opened = False

        self.__class__.instances.append(self)

    def open(self) -> None:
        self.opened = True


class IntegrityError(Exception):
    pass


def _page(
    *,
    saved_jobs_service=None,
):
    jobs = _JobService()

    page = JobPage(
        job_service=jobs,  # type: ignore[arg-type]
        company_service=_CompanyService(),  # type: ignore[arg-type]
        saved_jobs_import_service=saved_jobs_service,  # type: ignore[arg-type]
    )

    return page, jobs


def _fill_valid_form(page: JobPage) -> None:
    page.company_combo.setCurrentIndex(
        page.company_combo.findData(1)
    )
    page.title_input.setText("Coordenador de Logística")
    page.location_input.setText("Guarulhos - SP")
    page.work_model_combo.setCurrentText("Híbrido")
    page.employment_type_combo.setCurrentText("CLT")
    page.salary_min_input.setValue(12000)
    page.salary_max_input.setValue(15000)
    page.currency_input.setCurrentText("BRL")
    page.status_combo.setCurrentText("Nova")
    page.source_input.setText("LinkedIn")
    page.url_input.setText(
        "https://www.linkedin.com/jobs/view/123"
    )
    page.application_url_input.setText(
        "https://empresa.com/apply"
    )
    page.recruiter_input.setText("Maria")
    page.recruiter_email_input.setText(
        "maria@example.com"
    )
    page.priority_input.setValue(4)
    page.notes_input.setPlainText("Observação")
    page.benefits_input.setPlainText(
        "Vale-refeição\nPlano de saúde"
    )


def test_save_job_creates_new_record_and_clears_form(
    qapp,
) -> None:
    page, jobs = _page()

    _fill_valid_form(page)

    page.current_job_id = None

    result = page._save_job(
        clear_after=True,
        show_success=True,
    )

    assert result is True
    assert len(jobs.created) == 1

    payload = jobs.created[0]

    assert payload["company_id"] == 1
    assert payload["title"] == "Coordenador de Logística"
    assert payload["location"] == "Guarulhos - SP"
    assert payload["work_model"] == "Híbrido"
    assert payload["employment_type"] == "CLT"
    assert payload["salary_min"] == 12000
    assert payload["salary_max"] == 15000
    assert payload["currency"] == "BRL"
    assert payload["status"] == "Nova"
    assert payload["source"] == "LinkedIn"

    assert (
        payload["job_url"]
        == "https://www.linkedin.com/jobs/view/123"
    )

    assert (
        payload["application_url"]
        == "https://empresa.com/apply"
    )

    assert payload["recruiter"] == "Maria"

    assert (
        payload["recruiter_email"]
        == "maria@example.com"
    )

    assert payload["priority"] == 4

    assert "[BENEFICIOS]" in str(payload["notes"])
    assert "Vale-refeição" in str(payload["notes"])

    assert page.current_job_id is None
    assert page.title_input.text() == ""


def test_save_job_updates_existing_record_and_keeps_selection(
    qapp,
) -> None:
    page, jobs = _page()

    _fill_valid_form(page)

    page.current_job_id = 10

    result = page._save_job(
        clear_after=False,
        show_success=True,
    )

    qapp.processEvents()

    assert result is True

    assert len(jobs.updated) == 1

    job_id, payload = jobs.updated[0]

    assert job_id == 10
    assert payload["company_id"] == 1
    assert payload["title"] == "Coordenador de Logística"
    assert payload["salary_min"] == 12000
    assert payload["salary_max"] == 15000

    assert page.current_job_id == 10

    assert (
        page.import_status_label.text()
        == "Vaga salva."
    )

    selected_rows = page.table.selectionModel().selectedRows()

    assert len(selected_rows) == 1
    assert selected_rows[0].row() == 0


def test_save_job_without_company_warns_and_returns_false(
    qapp,
    monkeypatch,
) -> None:
    page, jobs = _page()

    _fill_valid_form(page)

    page.company_combo.setCurrentIndex(0)

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    result = page._save_job()

    assert result is False
    assert jobs.created == []
    assert jobs.updated == []

    assert warnings == [
        "Selecione uma empresa."
    ]


def test_save_job_update_missing_record_warns(
    qapp,
    monkeypatch,
) -> None:
    page, jobs = _page()

    _fill_valid_form(page)

    page.current_job_id = 10
    jobs.update_result = None

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    result = page._save_job(
        clear_after=False,
        show_success=False,
    )

    assert result is False
    assert len(jobs.updated) == 1

    assert warnings == [
        "A vaga não foi encontrada para atualização."
    ]


def test_save_current_job_shows_confirmation(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    _fill_valid_form(page)

    page.current_job_id = 10

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._save_current_job()

    qapp.processEvents()

    assert infos == [
        "O registro foi salvo"
    ]


def test_import_saved_jobs_requires_service(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._import_saved_linkedin_jobs()

    assert warnings == [
        "O serviço de importação em lote não está disponível."
    ]


def test_import_saved_jobs_executes_service_and_opens_dialog(
    qapp,
    monkeypatch,
) -> None:
    service = _SavedJobsService()

    page, _jobs = _page(
        saved_jobs_service=service,
    )

    executor = _Executor()

    page._saved_jobs_executor = executor  # type: ignore[assignment]

    _ProgressDialog.instances.clear()

    monkeypatch.setattr(
        job_page_module,
        "LinkedInSavedJobsProgressDialog",
        _ProgressDialog,
    )

    page._import_saved_linkedin_jobs()

    assert service.calls == 1
    assert len(executor.tasks) == 1

    assert len(_ProgressDialog.instances) == 1

    dialog = _ProgressDialog.instances[0]

    assert dialog.parent is page
    assert dialog.opened is True

    assert dialog.cancel_requested.callbacks == [
        executor.cancel
    ]

    assert page._saved_jobs_dialog is dialog

    assert not page.import_saved_jobs_button.isEnabled()


def test_delete_integrity_error_can_cancel_cascade(
    qapp,
    monkeypatch,
) -> None:
    page, jobs = _page()

    page.current_job_id = 10

    jobs.delete_outcomes = [
        IntegrityError("foreign key"),
    ]

    answers = iter(
        [
            QMessageBox.Yes,
            QMessageBox.No,
        ]
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: next(answers),
    )

    page._delete_job()

    assert jobs.deleted == [
        (
            10,
            False,
        )
    ]

    assert page.current_job_id == 10


def test_delete_integrity_error_can_delete_linked_records(
    qapp,
    monkeypatch,
) -> None:
    page, jobs = _page()

    page.current_job_id = 10

    jobs.delete_outcomes = [
        IntegrityError("foreign key"),
        True,
    ]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_job()

    qapp.processEvents()

    assert jobs.deleted == [
        (
            10,
            False,
        ),
        (
            10,
            True,
        ),
    ]

    assert page.current_job_id is None


def test_delete_cascade_false_result_warns(
    qapp,
    monkeypatch,
) -> None:
    page, jobs = _page()

    page.current_job_id = 10

    jobs.delete_outcomes = [
        IntegrityError("foreign key"),
        False,
    ]

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

    page._delete_job()

    assert jobs.deleted == [
        (
            10,
            False,
        ),
        (
            10,
            True,
        ),
    ]

    assert warnings == [
        "O registro não pôde ser excluído."
    ]


def test_delete_cascade_exception_is_reported(
    qapp,
    monkeypatch,
) -> None:
    page, jobs = _page()

    page.current_job_id = 10

    jobs.delete_outcomes = [
        IntegrityError("foreign key"),
        RuntimeError("cascade failure"),
    ]

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._delete_job()

    assert jobs.deleted == [
        (
            10,
            False,
        ),
        (
            10,
            True,
        ),
    ]

    assert messages == [
        "Não foi possível excluir o registro e seus vínculos."
    ]