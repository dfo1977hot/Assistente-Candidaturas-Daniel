from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtWidgets import QMessageBox

from acd.presentation.pages.job_page import JobPage
from acd.services.linkedin_application_resolver import (
    LinkedInApplicationResolution,
)
from acd.services.linkedin_job_import_service import (
    ImportedLinkedInJob,
    LinkedInJobImportError,
)
from acd.services.linkedin_saved_jobs_import_service import (
    SavedJobsImportResult,
    SavedJobsProgress,
)
from acd.services.salary_research_service import (
    SalaryResearchResult,
)


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
            application_url="",
            recruiter="Maria",
            recruiter_email="",
            application_deadline="",
            application_date="",
            priority=3,
            notes="",
            created_at=None,
        )

        self.updated: list[tuple[int, dict[str, object]]] = []
        self.created: list[dict[str, object]] = []
        self.deleted: list[tuple[int, bool]] = []
        self.url_exists = False
        self.by_url = None
        self.by_linkedin_id = None

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

    def get_job_by_url(self, url: str):
        del url
        return self.by_url

    def get_job_by_linkedin_job_id(self, linkedin_job_id: str):
        del linkedin_job_id
        return self.by_linkedin_id

    def job_url_exists(
        self,
        url: str,
        *,
        exclude_job_id: int | None = None,
    ) -> bool:
        del url, exclude_job_id
        return self.url_exists

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
        self.deleted.append(
            (
                job_id,
                delete_linked,
            )
        )
        return True


class _ImportService:
    def __init__(self) -> None:
        self.import_calls: list[str] = []
        self._closed_jobs_registry = _ClosedJobsRegistry()

    def normalize_linkedin_job_url(self, url: str) -> str:
        value = url.strip()

        if not value:
            raise LinkedInJobImportError(
                "Cole a URL da vaga do LinkedIn."
            )

        if "linkedin.com/jobs/" not in value:
            raise LinkedInJobImportError(
                "A URL informada não pertence ao LinkedIn."
            )

        return value

    def import_from_url(self, url: str):
        self.import_calls.append(url)

        return ImportedLinkedInJob(
            title="Engenheiro de Produção",
            source_url=url,
        )


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

        assert not cancellation_requested()

        progress_callback(
            SavedJobsProgress(
                stage="importing",
                message="Importando",
                current=1,
                total=2,
            )
        )

        return SavedJobsImportResult(
            found=2,
            imported=1,
            existing=1,
            failed=0,
            companies_created=0,
            deleted=0,
        )


class _SalaryService:
    def __init__(self) -> None:
        self.calls = []

    def research(
        self,
        request,
        *,
        force_refresh: bool = False,
    ):
        self.calls.append(
            (
                request,
                force_refresh,
            )
        )

        return SalaryResearchResult(
            salary_min=10000,
            salary_max=14000,
            currency="BRL",
            confidence="alta",
        )


class _RecruiterEmailService:
    def __init__(self) -> None:
        self.calls = []

    def research(self, request):
        self.calls.append(request)
        return "recrutador@example.com"


class _ApplicationResolver:
    def __init__(self) -> None:
        self.calls = []

    def resolve_linkedin_application_url(
        self,
        job_url: str,
        progress=None,
    ):
        self.calls.append(job_url)

        if progress is not None:
            progress(
                (
                    50,
                    "Localizando candidatura",
                )
            )

        return LinkedInApplicationResolution(
            url="https://empresa.com/apply",
            application_type="external",
            accepting_applications=True,
        )


class _ClosedJobsRegistry:
    def __init__(self) -> None:
        self.closed: list[str] = []

    def job_id_from_url(self, url: str):
        if "123" in url:
            return "123"

        return ""

    def mark_closed(self, linkedin_job_id: str):
        self.closed.append(linkedin_job_id)


class _SyncExecutor:
    def __init__(self) -> None:
        self.tasks = []
        self.is_running = False
        self.cancelled = False

    def execute(self, task, **kwargs):
        del kwargs

        self.tasks.append(task)
        self.last_result = task()

        return self.last_result

    def execute_with_context(self, task):
        self.tasks.append(task)

        token = SimpleNamespace(
            is_cancellation_requested=False,
        )

        self.last_result = task(
            lambda value: setattr(
                self,
                "last_progress",
                value,
            ),
            token,
        )

        return self.last_result

    def cancel(self):
        self.cancelled = True


class _SavedJobsDialog:
    def __init__(self) -> None:
        self.progress = []
        self.results = []
        self.failures = []
        self.cancelled = False

    def update_progress(self, progress):
        self.progress.append(progress)

    def show_result(self, result):
        self.results.append(result)

    def show_failure(self, error: str):
        self.failures.append(error)

    def show_cancelled(self):
        self.cancelled = True


def _page(
    *,
    import_service=None,
    saved_jobs_service=None,
    salary_service=None,
    recruiter_email_service=None,
    resolver=None,
):
    jobs = _JobService()

    page = JobPage(
        job_service=jobs,  # type: ignore[arg-type]
        company_service=_CompanyService(),  # type: ignore[arg-type]
        job_import_service=import_service,  # type: ignore[arg-type]
        saved_jobs_import_service=saved_jobs_service,  # type: ignore[arg-type]
        salary_research_service=salary_service,  # type: ignore[arg-type]
        recruiter_email_research_service=recruiter_email_service,  # type: ignore[arg-type]
        application_url_resolver=resolver,  # type: ignore[arg-type]
    )

    return page, jobs


def test_import_linkedin_job_requires_service(
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

    page._import_linkedin_job()

    assert warnings
    assert "não está disponível" in warnings[-1]


def test_import_linkedin_job_validates_url(
    qapp,
    monkeypatch,
) -> None:
    importer = _ImportService()

    page, _jobs = _page(
        import_service=importer,
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.url_input.setText("https://example.com/job")

    page._import_linkedin_job()

    assert warnings
    assert importer.import_calls == []


def test_import_linkedin_job_rejects_existing_url(
    qapp,
    monkeypatch,
) -> None:
    importer = _ImportService()

    page, jobs = _page(
        import_service=importer,
    )

    jobs.url_exists = True

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.url_input.setText(
        "https://www.linkedin.com/jobs/view/123"
    )

    page._import_linkedin_job()

    assert warnings
    assert "já está vinculada" in warnings[-1]
    assert importer.import_calls == []


def test_import_linkedin_job_executes_importer(
    qapp,
) -> None:
    importer = _ImportService()

    page, _jobs = _page(
        import_service=importer,
    )

    executor = _SyncExecutor()

    page._import_executor = executor  # type: ignore[assignment]

    page.url_input.setText(
        "https://www.linkedin.com/jobs/view/123"
    )

    page._import_linkedin_job()

    assert importer.import_calls == [
        "https://www.linkedin.com/jobs/view/123"
    ]

    assert not page.import_linkedin_button.isEnabled()

    assert (
        page.import_status_label.text()
        == "Importando vaga..."
    )


def test_linkedin_import_incomplete_result_warns(
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

    page._on_linkedin_import_succeeded(
        ImportedLinkedInJob()
    )

    assert warnings
    assert "dados públicos suficientes" in warnings[-1]


def test_linkedin_import_can_be_cancelled_when_form_has_data(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    page.title_input.setText("Conteúdo existente")

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.No,
    )

    result = ImportedLinkedInJob(
        title="Novo cargo",
        company_name="Empresa Alpha",
        source_url="https://www.linkedin.com/jobs/view/123",
    )

    page._on_linkedin_import_succeeded(result)

    assert page.title_input.text() == "Conteúdo existente"

    assert (
        page.import_status_label.text()
        == "Importação cancelada pelo usuário."
    )


def test_apply_imported_linkedin_job_populates_form(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    result = ImportedLinkedInJob(
        title="Coordenador de Logística",
        company_name="Empresa Alpha",
        location="Guarulhos - SP",
        work_model="Híbrido",
        employment_type="CLT",
        salary_min=11000,
        salary_max=15000,
        currency="BRL",
        recruiter="Maria",
        application_deadline="2026-08-31",
        description="Descrição da vaga",
        requirements=(
            "Lean",
            "SAP",
        ),
        responsibilities=(
            "Gestão de equipe",
        ),
        benefits=(
            "VR",
            "Plano de saúde",
        ),
        source_url="https://www.linkedin.com/jobs/view/123",
    )

    page._apply_imported_job(result)

    assert page.title_input.text() == "Coordenador de Logística"
    assert page.location_input.text() == "Guarulhos - SP"
    assert page.work_model_combo.currentText() == "Híbrido"
    assert page.employment_type_combo.currentText() == "CLT"
    assert page.salary_min_input.value() == 15000
    assert page.salary_max_input.value() == 0
    assert page.currency_input.currentText() == "BRL"
    assert page.source_input.text() == "LinkedIn"

    assert (
        page.url_input.text()
        == "https://www.linkedin.com/jobs/view/123"
    )

    assert page.recruiter_input.text() == "Maria"
    assert "VR" in page.benefits_input.toPlainText()
    assert "Descrição da vaga" in page.notes_input.toPlainText()
    assert page.company_combo.currentData() == 1


def test_imported_company_not_found_informs_user(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._apply_imported_job(
        ImportedLinkedInJob(
            title="Cargo",
            company_name="Empresa Inexistente",
        )
    )

    assert infos
    assert "ainda não existe" in infos[-1]


def test_recruiter_email_research_runs_only_when_needed(
    qapp,
) -> None:
    service = _RecruiterEmailService()

    page, _jobs = _page(
        recruiter_email_service=service,
    )

    executor = _SyncExecutor()

    page._recruiter_email_executor = executor  # type: ignore[assignment]

    result = ImportedLinkedInJob(
        title="Cargo",
        company_name="Empresa Alpha",
        location="Guarulhos",
        recruiter="Maria",
    )

    page._research_recruiter_email_if_needed(result)

    assert len(executor.tasks) == 1
    assert len(service.calls) == 1

    page.recruiter_email_input.setText(
        "existente@example.com"
    )

    page._research_recruiter_email_if_needed(result)

    assert len(executor.tasks) == 1


def test_recruiter_email_success_sets_only_empty_field(
    qapp,
) -> None:
    page, _jobs = _page()

    page._on_recruiter_email_research_succeeded(
        "novo@example.com"
    )

    assert (
        page.recruiter_email_input.text()
        == "novo@example.com"
    )

    page.recruiter_email_input.setText(
        "existente@example.com"
    )

    page._on_recruiter_email_research_succeeded(
        "outro@example.com"
    )

    assert (
        page.recruiter_email_input.text()
        == "existente@example.com"
    )


def test_detect_application_url_validates_job_url(
    qapp,
    monkeypatch,
) -> None:
    resolver = _ApplicationResolver()

    page, _jobs = _page(
        resolver=resolver,
    )

    warnings: list[str] = []
    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page.url_input.clear()

    page._detect_application_url()

    assert warnings

    page.url_input.setText(
        "https://example.com/job"
    )

    page._detect_application_url()

    assert infos
    assert resolver.calls == []


def test_detect_application_url_runs_resolver(
    qapp,
) -> None:
    resolver = _ApplicationResolver()

    page, _jobs = _page(
        resolver=resolver,
    )

    executor = _SyncExecutor()

    page._application_url_executor = executor  # type: ignore[assignment]

    page.url_input.setText(
        "https://www.linkedin.com/jobs/view/123"
    )

    page._detect_application_url()

    assert resolver.calls == [
        "https://www.linkedin.com/jobs/view/123"
    ]

    assert not page.detect_application_url_button.isEnabled()

    assert (
        page.import_status_label.text()
        == "Localizando link Candidatar-se..."
    )


def test_application_url_progress_updates_status(
    qapp,
) -> None:
    page, _jobs = _page()

    page._on_application_url_progress(
        (
            50,
            "Localizando candidatura",
        )
    )

    assert (
        page.import_status_label.text()
        == "Localizando candidatura"
    )

    page._on_application_url_progress(
        "ignorar"
    )

    assert (
        page.import_status_label.text()
        == "Localizando candidatura"
    )


def test_application_url_resolved_external_persists(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    page.current_job_id = 10

    page.url_input.setText(
        "https://www.linkedin.com/jobs/view/123"
    )

    saved: list[tuple[bool, bool]] = []

    monkeypatch.setattr(
        page,
        "_save_job",
        lambda *, clear_after, show_success: (
            saved.append(
                (
                    clear_after,
                    show_success,
                )
            )
            or True
        ),
    )

    page._on_application_url_resolved(
        LinkedInApplicationResolution(
            url="https://empresa.com/apply",
            application_type="external",
            accepting_applications=True,
        )
    )

    assert (
        page.application_url_input.text()
        == "https://empresa.com/apply"
    )

    assert (
        page.import_status_label.text()
        == "Link Candidatar-se localizado."
    )

    assert saved == [
        (
            False,
            False,
        )
    ]


def test_application_url_resolved_easy_apply(
    qapp,
) -> None:
    page, _jobs = _page()

    page._on_application_url_resolved(
        LinkedInApplicationResolution(
            url="https://empresa.com/easy",
            application_type="easy_apply",
            accepting_applications=True,
        )
    )

    assert (
        page.import_status_label.text()
        == "Candidatura simplificada localizada."
    )


def test_application_url_accepting_without_url_warns(
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

    page._on_application_url_resolved(
        LinkedInApplicationResolution(
            url="",
            accepting_applications=True,
        )
    )

    assert warnings
    assert "não expôs a URL" in warnings[-1]


def test_application_url_unknown_state_warns(
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

    page._on_application_url_resolved(
        LinkedInApplicationResolution(
            url="",
            accepting_applications=None,
        )
    )

    assert warnings
    assert "não será excluída" in warnings[-1]


def test_application_url_closed_can_delete_job(
    qapp,
    monkeypatch,
) -> None:
    importer = _ImportService()

    page, jobs = _page(
        import_service=importer,
    )

    page.current_job_id = 10

    page.url_input.setText(
        "https://www.linkedin.com/jobs/view/123"
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: None,
    )

    page._on_application_url_resolved(
        LinkedInApplicationResolution(
            url="",
            accepting_applications=False,
        )
    )

    assert importer._closed_jobs_registry.closed == [
        "123"
    ]

    assert jobs.deleted == [
        (
            10,
            True,
        )
    ]

    assert page.current_job_id is None


def test_same_job_and_application_url_normalizes_trailing_slash() -> None:
    assert JobPage._same_job_and_application_url(
        "https://example.com/job/",
        "https://example.com/job",
    )

    assert not JobPage._same_job_and_application_url(
        "https://example.com/job",
        "https://example.com/apply",
    )


def test_salary_research_requires_service(
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

    page._research_salary()

    assert warnings
    assert "não está disponível" in warnings[-1]


def test_salary_research_validates_fields(
    qapp,
    monkeypatch,
) -> None:
    service = _SalaryService()

    page, _jobs = _page(
        salary_service=service,
    )

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page.title_input.clear()
    page.location_input.clear()

    page._research_salary()

    assert warnings
    assert service.calls == []


def test_salary_research_executes_service(
    qapp,
) -> None:
    service = _SalaryService()

    page, _jobs = _page(
        salary_service=service,
    )

    executor = _SyncExecutor()

    page._salary_research_executor = executor  # type: ignore[assignment]

    page.title_input.setText(
        "Engenheiro de Produção"
    )

    page.location_input.setText(
        "Guarulhos - SP"
    )

    page.work_model_combo.setCurrentText(
        "Híbrido"
    )

    page.employment_type_combo.setCurrentText(
        "CLT"
    )

    page._research_salary()

    assert len(service.calls) == 1

    request, force_refresh = service.calls[0]

    assert request.title == "Engenheiro de Produção"
    assert request.location == "Guarulhos - SP"
    assert request.work_model == "Híbrido"
    assert request.employment_type == "CLT"
    assert force_refresh is True

    assert not page.salary_research_button.isEnabled()


def test_salary_research_rejects_invalid_result(
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

    page._on_salary_research_succeeded(
        object()
    )

    assert warnings
    assert "resultado inválido" in warnings[-1]


def test_salary_research_success_updates_and_saves(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    saved: list[tuple[bool, bool]] = []

    monkeypatch.setattr(
        page,
        "_save_job",
        lambda *, clear_after, show_success: (
            saved.append(
                (
                    clear_after,
                    show_success,
                )
            )
            or True
        ),
    )

    result = SalaryResearchResult(
        salary_min=10000,
        salary_max=15000,
        currency="BRL",
    )

    page._on_salary_research_succeeded(result)

    assert page.salary_max_input.value() == 15000
    assert page.currency_input.currentText() == "BRL"

    assert saved == [
        (
            False,
            False,
        )
    ]

    assert "vaga salva" in page.import_status_label.text()


def test_salary_research_success_handles_save_failure(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    monkeypatch.setattr(
        page,
        "_save_job",
        lambda **_kwargs: False,
    )

    page._on_salary_research_succeeded(
        SalaryResearchResult(
            salary_min=10000,
            salary_max=15000,
            currency="BRL",
        )
    )

    assert (
        "não pôde ser salva"
        in page.import_status_label.text()
    )


def test_salary_callbacks_restore_button(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._on_salary_research_failed(
        RuntimeError("Falha salarial")
    )

    assert messages == [
        "Falha salarial"
    ]

    page.salary_research_button.setEnabled(False)
    page.salary_research_button.setText("Executando")

    page._on_salary_research_finished()

    assert page.salary_research_button.isEnabled()

    assert (
        page.salary_research_button.text()
        == "Pesquisar média salarial com IA"
    )


def test_saved_jobs_callbacks_cover_success_failure_and_cancel(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    dialog = _SavedJobsDialog()

    page._saved_jobs_dialog = dialog  # type: ignore[assignment]

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    progress = SavedJobsProgress(
        stage="importing",
        message="Importando",
        current=1,
        total=2,
    )

    page._on_saved_jobs_progress(progress)

    assert dialog.progress == [
        progress
    ]

    result = SavedJobsImportResult(
        found=2,
        imported=1,
        existing=1,
        failed=0,
        companies_created=0,
        deleted=0,
    )

    page._on_saved_jobs_succeeded(result)

    assert dialog.results == [
        result
    ]

    assert infos
    assert page.import_saved_jobs_button.isEnabled()

    page._on_saved_jobs_failed(
        RuntimeError("Falha")
    )

    assert dialog.failures == [
        "Falha"
    ]

    page._on_saved_jobs_cancelled()

    assert dialog.cancelled is True


def test_linkedin_import_callbacks_restore_ui(
    qapp,
    monkeypatch,
) -> None:
    page, _jobs = _page()

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._on_linkedin_import_failed(
        RuntimeError("Falha de importação")
    )

    assert (
        page.import_status_label.text()
        == "Falha na importação."
    )

    assert messages == [
        "Falha de importação"
    ]

    page.import_linkedin_button.setEnabled(False)

    page._on_linkedin_import_finished()

    assert page.import_linkedin_button.isEnabled()


def test_application_url_callbacks_restore_ui(
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

    page._on_application_url_resolution_failed(
        RuntimeError("Falha URL")
    )

    assert warnings == [
        "Falha URL"
    ]

    assert (
        page.import_status_label.text()
        == "Falha ao localizar link externo."
    )

    page.detect_application_url_button.setEnabled(False)

    page._on_application_url_resolution_finished()

    assert page.detect_application_url_button.isEnabled()