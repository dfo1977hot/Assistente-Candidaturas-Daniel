from __future__ import annotations

from datetime import datetime
from types import SimpleNamespace

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QTableWidget,
)

from acd.presentation.pages.application_page import ApplicationPage


class _CompanyService:
    def list_companies(self):
        return [
            SimpleNamespace(id=1, name="Empresa Alpha"),
            SimpleNamespace(id=2, name="Empresa Beta"),
        ]


class _JobService:
    def __init__(self) -> None:
        self.filter_calls: list[int] = []

        self.jobs = {
            10: SimpleNamespace(
                id=10,
                title="Engenheiro de Produção",
                company_id=1,
                salary_min=9000,
                salary_max=12000,
            ),
            20: SimpleNamespace(
                id=20,
                title="Coordenador de Logística",
                company_id=2,
                salary_min=None,
                salary_max=None,
            ),
        }

    def filter_jobs(self, **filters):
        company_id = int(filters["company_id"])
        self.filter_calls.append(company_id)

        return [
            job
            for job in self.jobs.values()
            if job.company_id == company_id
        ]

    def get_job(self, job_id: int):
        return self.jobs.get(job_id)


class _CurriculumService:
    def __init__(self) -> None:
        self.curricula = [
            SimpleNamespace(
                id=100,
                name="Currículo Produção",
                version="1",
            ),
            SimpleNamespace(
                id=200,
                name="Currículo Logística",
                version="2",
            ),
        ]
        self.associations: list[tuple[int, int]] = []
        self.association_result = SimpleNamespace(id=1)

    def list_curricula(self):
        return list(self.curricula)

    def associate_to_application(
        self,
        *,
        application_id: int,
        curriculum_id: int,
    ):
        self.associations.append(
            (application_id, curriculum_id)
        )
        return self.association_result

    def resolve_document_path(self, curriculum_id: int):
        del curriculum_id
        return None


class _ApplicationService:
    def __init__(self) -> None:
        self.created: list[dict[str, object]] = []
        self.updated: list[tuple[int, dict[str, object]]] = []
        self.deleted: list[int] = []
        self.search_queries: list[str] = []
        self.filter_calls: list[dict[str, object]] = []

        company = SimpleNamespace(
            id=1,
            name="Empresa Alpha",
        )
        job = SimpleNamespace(
            id=10,
            title="Engenheiro de Produção",
        )

        self.application = SimpleNamespace(
            id=300,
            company=company,
            company_id=1,
            job=job,
            job_id=10,
            curriculum_id=None,
            status="Aplicada",
            application_date=datetime(2026, 8, 10),
            next_follow_up=datetime(2026, 8, 20),
            response_date=None,
            interview_date=None,
            salary_expected=12000.0,
            salary_offered=None,
            application_channel="LinkedIn",
            recruiter_name="Maria",
            recruiter_email="maria@example.com",
            recruiter_phone="11999999999",
            feedback="",
            notes="",
        )

        self.applications = [self.application]
        self.delete_result = True

    def list_applications(self):
        return list(self.applications)

    def search_applications(self, query: str):
        self.search_queries.append(query)
        return list(self.applications)

    def filter_applications(self, **filters):
        self.filter_calls.append(dict(filters))
        return list(self.applications)

    def get_application(self, application_id: int):
        if application_id == self.application.id:
            return self.application
        return None

    def create_application(self, **data):
        self.created.append(dict(data))
        return self.application

    def update_application(
        self,
        application_id: int,
        **data,
    ):
        self.updated.append(
            (
                application_id,
                dict(data),
            )
        )
        return self.application

    def delete_application(
        self,
        application_id: int,
        *,
        delete_linked: bool = False,
    ):
        del delete_linked
        self.deleted.append(application_id)
        return self.delete_result

class _ResumeMatchService:
    def __init__(self) -> None:
        self.result = SimpleNamespace(
            has_vacancy_description=True,
            score=82.0,
            overall_score=82.0,
            classification="Alta aderência",
            ats_score=70.0,
            adapted_ats_score=88.0,
            adapted_score=91.0,
            interview_probability_min=30.0,
            interview_probability_max=45.0,
            adapted_interview_probability_min=55.0,
            adapted_interview_probability_max=70.0,
            requirements=(
                SimpleNamespace(
                    category="Melhoria Contínua",
                    requirement="Experiência com Lean",
                    evidence="Experiência comprovada com Lean",
                    score=100.0,
                    status="Atende",
                ),
                SimpleNamespace(
                    category="Planejamento",
                    requirement="Experiência com PCP",
                    evidence="Experiência comprovada com PCP",
                    score=100.0,
                    status="Atende",
                ),
                SimpleNamespace(
                    category="Sistemas",
                    requirement="Conhecimento em SAP",
                    evidence="Não evidenciado no currículo",
                    score=0.0,
                    status="Gap",
                ),
            ),
            dimension_scores=(
                SimpleNamespace(
                    name="Experiência profissional",
                    score=85.0,
                ),
                SimpleNamespace(
                    name="Competências técnicas",
                    score=80.0,
                ),
            ),
            strengths=(
                "Experiência com Lean",
                "Experiência com PCP",
                "Vivência em logística",
            ),
            gaps=(
                "SAP não evidenciado",
                "Power BI não evidenciado",
            ),
            differentials=(
                "Experiência em melhoria contínua",
            ),
            recommendation=(
                "Currículo apresenta boa aderência à vaga e deve destacar "
                "as experiências diretamente relacionadas aos requisitos."
            ),
            adaptation_strategy=(
                "Priorizar experiências aderentes aos requisitos da vaga.",
                "Destacar resultados mensuráveis já existentes no currículo.",
                "Reforçar palavras-chave verdadeiras sem criar competências.",
            ),
            matched_keywords=(
                "Lean",
                "PCP",
                "Logística",
            ),
            missing_keywords=(
                "SAP",
                "Power BI",
            ),
        )
        self.calls: list[tuple[object, object]] = []

    def analyze(
        self,
        *,
        application: object,
        curriculum: object,
    ):
        self.calls.append(
            (
                application,
                curriculum,
            )
        )
        return self.result

    def get_cached(
        self,
        application_id: int,
        curriculum_id: int,
    ):
        del application_id
        del curriculum_id
        return None


class _AtsService:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def persist_resume_match_result(self, **kwargs):
        self.calls.append(dict(kwargs))


class _FollowUpService:
    ACTION_TYPES = (
        "Enviar mensagem",
        "Cobrar retorno",
    )
    PRIORITIES = (
        "Baixa",
        "Normal",
        "Alta",
    )
    INTERACTION_TYPES = (
        "E-mail",
        "Telefone",
    )

    def __init__(self) -> None:
        self.actions: list[tuple[int, dict[str, object]]] = []
        self.interactions: list[tuple[int, dict[str, object]]] = []
        self.completed: list[int] = []
        self.postponed: list[tuple[int, object]] = []

        self.state = SimpleNamespace(
            next_action="Cobrar retorno",
            priority="Alta",
            note="Retornar amanhã",
            follow_up_time="09:30",
            last_interaction_at=datetime(
                2026,
                8,
                13,
                14,
                30,
            ),
            last_interaction_type="E-mail",
        )

        self.timeline = (
            SimpleNamespace(
                occurred_at=datetime(
                    2026,
                    8,
                    13,
                    14,
                    30,
                ),
                interaction_type="E-mail",
                summary="Resposta recebida",
                origin="outlook",
                reference_type="mail_message",
                reference_id=10,
            ),
            SimpleNamespace(
                occurred_at=datetime(
                    2026,
                    8,
                    12,
                    10,
                    0,
                ),
                interaction_type="Telefone",
                summary="Ligação realizada",
                origin="manual",
                reference_type=None,
                reference_id=None,
            ),
        )

    def get_state(self, application_id: int):
        assert application_id == 300
        return self.state

    def get_timeline(self, application_id: int):
        assert application_id == 300
        return self.timeline

    def set_next_action(
        self,
        application_id: int,
        **data,
    ):
        self.actions.append(
            (
                application_id,
                dict(data),
            )
        )
        return self.state

    def register_interaction(
        self,
        application_id: int,
        **data,
    ):
        self.interactions.append(
            (
                application_id,
                dict(data),
            )
        )
        return self.state

    def complete_follow_up(
        self,
        application_id: int,
        *,
        note: str = "",
    ):
        del note
        self.completed.append(application_id)
        return self.state

    def postpone_follow_up(
        self,
        application_id: int,
        new_date: object,
        *,
        note: str = "",
    ):
        del note
        self.postponed.append(
            (
                application_id,
                new_date,
            )
        )
        return self.state


class _CommunicationsService:
    def __init__(self) -> None:
        self.calls: list[int] = []

    def sync_application(
        self,
        application_id: int,
        progress=None,
    ):
        self.calls.append(application_id)

        if progress is not None:
            progress(
                (
                    50,
                    "Lendo mensagens",
                )
            )

        return SimpleNamespace(
            matched_messages=3,
            imported_messages=2,
            skipped_duplicates=1,
        )


class _CommunicationsExecutor:
    def __init__(self) -> None:
        self.is_running = False
        self.tasks = []

    def execute_with_context(self, task) -> None:
        self.tasks.append(task)

        def emit(payload):
            self.last_payload = payload

        task(
            emit,
            None,
        )


def _page():
    application_service = _ApplicationService()
    company_service = _CompanyService()
    job_service = _JobService()
    curriculum_service = _CurriculumService()
    resume_match_service = _ResumeMatchService()
    ats_service = _AtsService()
    follow_up_service = _FollowUpService()
    communications_service = _CommunicationsService()

    page = ApplicationPage(
        application_service=application_service,  # type: ignore[arg-type]
        application_follow_up_service=follow_up_service,  # type: ignore[arg-type]
        communications_service=communications_service,  # type: ignore[arg-type]
        company_service=company_service,  # type: ignore[arg-type]
        job_service=job_service,  # type: ignore[arg-type]
        curriculum_service=curriculum_service,  # type: ignore[arg-type]
        resume_match_service=resume_match_service,  # type: ignore[arg-type]
        ats_service=ats_service,  # type: ignore[arg-type]
    )

    return (
        page,
        application_service,
        job_service,
        curriculum_service,
        resume_match_service,
        ats_service,
        follow_up_service,
        communications_service,
    )


def test_application_page_loads_reference_data_and_jobs(qapp) -> None:
    (
        page,
        _applications,
        jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    assert page.company_combo.count() == 3
    assert page.filter_company_combo.count() == 3
    assert page.curriculum_combo.count() == 3
    assert page.table.rowCount() == 1

    company_index = page.company_combo.findData(1)
    page.company_combo.setCurrentIndex(company_index)
    qapp.processEvents()

    assert jobs.filter_calls[-1] == 1
    assert page.job_combo.count() == 2
    assert page.job_combo.findData(10) >= 0


def test_application_page_populates_salary_and_clears_defaults(qapp) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    page.company_combo.setCurrentIndex(
        page.company_combo.findData(1)
    )
    qapp.processEvents()

    page.job_combo.setCurrentIndex(
        page.job_combo.findData(10)
    )
    qapp.processEvents()

    assert page.salary_expected_input.text() == "R$ 12.000,00"
    assert page.salary_offered_input.text() == "R$ 9.000,00"

    page.job_combo.setCurrentIndex(0)
    qapp.processEvents()

    assert page.salary_expected_input.text() == ""
    assert page.salary_offered_input.text() == ""


def test_application_page_curriculum_selection_and_match(
    qapp,
    qtbot,
    monkeypatch,
) -> None:
    (
        page,
        applications,
        _jobs,
        curricula,
        resume_match,
        ats,
        _follow_up,
        _communications,
    ) = _page()

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

    page._select_curriculum()

    assert infos == ["Selecione uma candidatura."]

    page.current_application_id = 300
    page.curriculum_combo.setCurrentIndex(0)
    page._select_curriculum()

    assert warnings[-1] == "Selecione um currículo cadastrado."

    page.curriculum_combo.setCurrentIndex(
        page.curriculum_combo.findData(100)
    )
    page._select_curriculum()

    assert curricula.associations == [(300, 100)]
    assert "Currículo selecionado" in page.resume_match_label.text()
    assert page.analyze_resume_button.isEnabled()

    page._analyze_resume_match()

    qtbot.waitUntil(
        lambda: not page._resume_match_executor.is_running,
        timeout=5000,
    )
    qapp.processEvents()

    assert len(resume_match.calls) == 1
    assert ats.calls
    assert ats.calls[0]["application_id"] == 300
    assert ats.calls[0]["curriculum_id"] == 100
    assert ats.calls[0]["result"] is resume_match.result
    assert "82%" in page.resume_match_label.text()
    assert "Lean" in page.resume_match_details.toPlainText()
    assert applications.get_application(300) is not None


def test_application_page_handles_missing_vacancy_description(
    qapp,
    qtbot,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page.current_application_id = 300
    page.curriculum_combo.setCurrentIndex(
        page.curriculum_combo.findData(100)
    )

    resume_match.result.has_vacancy_description = False

    page._analyze_resume_match()

    qtbot.waitUntil(
        lambda: not page._resume_match_executor.is_running,
        timeout=5000,
    )
    qapp.processEvents()

    assert messages
    assert "não possui descrição" in messages[-1]
    assert "descrição da vaga indisponível" in (
        page.resume_match_label.text()
    )
    assert not page.optimize_resume_button.isEnabled()


def test_application_page_create_and_update_application(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        follow_up,
        _communications,
    ) = _page()

    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._save_application()

    assert warnings[-1] == "Selecione uma empresa."

    page.company_combo.setCurrentIndex(
        page.company_combo.findData(1)
    )
    qapp.processEvents()

    page.job_combo.setCurrentIndex(
        page.job_combo.findData(10)
    )
    qapp.processEvents()

    page.status_combo.setCurrentText("Aplicada")
    page.salary_expected_input.setText("12000,50")
    page.salary_offered_input.setText("A combinar")
    page.channel_input.setText("LinkedIn")
    page.recruiter_name_input.setText("Maria")
    page.recruiter_email_input.setText("maria@example.com")
    page.recruiter_phone_input.setText("11999999999")
    page.feedback_input.setPlainText("Feedback")
    page.notes_input.setPlainText("Observação")

    page.next_action_combo.setCurrentText("Cobrar retorno")
    page.follow_up_priority_combo.setCurrentText("Alta")
    page.follow_up_time_input.setText("09:30")
    page.follow_up_note_input.setText("Retornar amanhã")

    page._save_application()

    assert len(applications.created) == 1

    created = applications.created[0]

    assert created["company_id"] == 1
    assert created["job_id"] == 10
    assert created["salary_expected"] == 12000.50
    assert created["salary_offered"] is None
    assert created["application_channel"] == "LinkedIn"
    assert created["recruiter_name"] == "Maria"
    assert page.current_application_id == 300
    assert follow_up.actions

    page._save_application()

    assert len(applications.updated) == 1
    assert applications.updated[0][0] == 300


def test_application_page_filters_and_renders_applications(qapp) -> None:
    (
        page,
        applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    page.search_input.setText("engenheiro")
    page._filter_applications()

    assert applications.search_queries == ["engenheiro"]
    assert page.table.rowCount() == 1
    assert page.table.item(0, 1).text() == "Empresa Alpha"
    assert page.table.item(0, 2).text() == "Engenheiro de Produção"
    assert page.table.item(0, 3).text() == "Aplicada"
    assert page.table.item(0, 4).text() == "10/08/2026"
    assert page.table.item(0, 5).text() == "20/08/2026"

    page.search_input.clear()
    page.filter_status_combo.setCurrentText("Aplicada")
    page._filter_applications()

    assert applications.filter_calls[-1]["status"] == "Aplicada"

    page.filter_status_combo.setCurrentIndex(0)
    page._filter_applications()

    assert page.table.rowCount() == 1


def test_application_page_follow_up_state_and_actions(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        follow_up,
        _communications,
    ) = _page()

    messages: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: messages.append(
            str(message)
        ),
    )

    page._complete_follow_up()

    assert messages[-1] == "Selecione uma candidatura."

    page.current_application_id = 300
    page._load_follow_up_state(300)

    assert page.next_action_combo.currentText() == "Cobrar retorno"
    assert page.follow_up_priority_combo.currentText() == "Alta"
    assert page.follow_up_note_input.text() == "Retornar amanhã"
    assert page.follow_up_time_input.text() == "09:30"
    assert "E-mail" in page.last_interaction_label.text()

    page._complete_follow_up()

    assert follow_up.completed == [300]

    page.next_follow_up_input.setDate(
        QDate(2026, 8, 25)
    )
    page._postpone_follow_up()

    assert len(follow_up.postponed) == 1
    assert follow_up.postponed[0][0] == 300


def test_application_page_registers_interaction(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        follow_up,
        _communications,
    ) = _page()

    page.current_application_id = 300

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda *_args, **_kwargs: (
            "E-mail",
            True,
        ),
    )
    monkeypatch.setattr(
        QInputDialog,
        "getText",
        lambda *_args, **_kwargs: (
            "Resposta recebida",
            True,
        ),
    )

    page._register_interaction()

    assert follow_up.interactions == [
        (
            300,
            {
                "interaction_type": "E-mail",
                "summary": "Resposta recebida",
            },
        )
    ]


def test_application_page_timeline_renders_and_filters(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    page.current_application_id = 300

    def fake_exec(dialog: QDialog) -> int:
        table = dialog.findChild(QTableWidget)
        combo = dialog.findChild(QComboBox)

        assert table is not None
        assert combo is not None
        assert table.rowCount() == 2
        assert table.item(0, 1).text() == "E-mail"
        assert table.item(0, 2).text() == "Resposta recebida"
        assert table.item(0, 3).text() == "outlook"
        assert table.item(0, 4).text() == "mail_message"
        assert table.item(0, 5).text() == "10"

        combo.setCurrentText("Telefone")
        qapp.processEvents()

        assert table.rowCount() == 1
        assert table.item(0, 1).text() == "Telefone"

        labels = dialog.findChildren(QLabel)
        assert any(
            label.text() == "1 evento(s)"
            for label in labels
        )

        return 0

    monkeypatch.setattr(
        QDialog,
        "exec",
        fake_exec,
    )

    page._show_timeline()


def test_application_page_outlook_callbacks_and_progress(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        communications,
    ) = _page()

    infos: list[str] = []
    warnings: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda _parent, _title, message: warnings.append(
            str(message)
        ),
    )

    page._sync_outlook_classic()

    assert infos[-1] == (
        "Selecione uma candidatura para sincronizar."
    )

    page.current_application_id = 300
    executor = _CommunicationsExecutor()
    page._communications_executor = executor  # type: ignore[assignment]

    page._sync_outlook_classic()

    assert len(executor.tasks) == 1
    assert communications.calls == [300]
    assert not page.outlook_sync_button.isEnabled()

    dialog = page._outlook_sync_progress

    assert isinstance(dialog, QProgressDialog)

    page._on_outlook_sync_progress(
        (
            75,
            "Importando mensagens",
        )
    )

    assert dialog.value() == 75
    assert dialog.labelText() == "Importando mensagens"

    result = SimpleNamespace(
        matched_messages=3,
        imported_messages=2,
        skipped_duplicates=1,
    )

    page._on_outlook_sync_succeeded(result)

    assert "Encontradas: 3" in infos[-1]
    assert "Importadas: 2" in infos[-1]
    assert "Já registradas: 1" in infos[-1]

    page._on_outlook_sync_failed(
        RuntimeError("Outlook indisponível")
    )

    assert warnings[-1] == "Outlook indisponível"

    page._on_outlook_sync_finished()

    assert page._outlook_sync_progress is None
    assert page.outlook_sync_button.isEnabled()


def test_application_page_delete_and_clear(
    qapp,
    monkeypatch,
) -> None:
    (
        page,
        applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    infos: list[str] = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda _parent, _title, message: infos.append(
            str(message)
        ),
    )

    page._delete_application()

    assert infos[-1] == (
        "Selecione uma candidatura para excluir."
    )

    page.current_application_id = 300

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *_args, **_kwargs: QMessageBox.Yes,
    )

    page._delete_application()

    assert applications.deleted == [300]
    assert page.current_application_id is None
    assert page.company_combo.currentIndex() == 0
    assert page.curriculum_combo.currentIndex() == 0
    assert page.salary_expected_input.text() == ""
    assert page.notes_input.toPlainText() == ""
    assert not page.outlook_sync_button.isEnabled()


def test_application_page_helper_values(qapp) -> None:
    (
        page,
        _applications,
        _jobs,
        _curricula,
        _resume_match,
        _ats,
        _follow_up,
        _communications,
    ) = _page()

    page.next_follow_up_input.setDate(
        page.next_follow_up_input.minimumDate()
    )

    assert (
        page._optional_date_value(
            page.next_follow_up_input
        )
        is None
    )

    page.next_follow_up_input.setDate(
        QDate(2026, 8, 30)
    )

    assert page._optional_date_value(
        page.next_follow_up_input
    ) == "2026-08-30"

    assert page._parse_optional_number("") is None
    assert page._parse_optional_number("A combinar") is None
    assert page._parse_optional_number("combinar") is None
    assert page._parse_optional_number("1234,56") == 1234.56