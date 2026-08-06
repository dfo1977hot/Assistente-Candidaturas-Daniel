from __future__ import annotations

from PySide6.QtCore import QDate, QDateTime, QTime

from tests.acceptance.conftest import _select_combo_data, build_acceptance_runtime


def _seed_mvp_flow(runtime) -> dict[str, int]:
    company_page = runtime.company_page
    job_page = runtime.job_page
    application_page = runtime.application_page
    interview_page = runtime.interview_page
    curriculum_page = runtime.curriculum_page

    company_page.name_input.setText("Empresa Sintetica Ltda")
    company_page.segment_input.setText("Software")
    company_page.city_input.setText("Cidade Sintetica")
    company_page.state_input.setText("SP")
    company_page.country_input.setText("Brasil")
    company_page.company_size_input.setText("51-200")
    company_page.website_input.setText("https://empresa-sintetica.example")
    company_page.notes_input.setPlainText("Empresa sintética para aceite do MVP.")
    company_page._save_company()

    runtime.job_page._load_companies()
    runtime.application_page._load_companies()

    company_id = runtime.company_service.list_companies()[0].id

    _select_combo_data(job_page.company_combo, company_id)
    job_page.title_input.setText("Analista de Dados")
    job_page.location_input.setText("Remoto")
    job_page.work_model_combo.setCurrentText("Remoto")
    job_page.employment_type_combo.setCurrentText("CLT")
    job_page.currency_input.setCurrentText("BRL")
    job_page.status_combo.setCurrentText("Nova")
    job_page.source_input.setText("Portal Sintetico")
    job_page.url_input.setText("https://vagas.example/analista-dados")
    job_page.recruiter_input.setText("Recrutador Sintetico")
    job_page.priority_input.setValue(4)
    job_page.notes_input.setPlainText("Vaga sintética de aceite.")
    job_page._save_job()

    job_id = runtime.job_service.list_jobs()[0].id

    curriculum_page.name_input.setText("Curriculo MVP")
    curriculum_page.version_input.setText("v1.0")
    curriculum_page.language_input.setText("pt-BR")
    curriculum_page.description_input.setPlainText("Curriculo sintético para aceite do MVP.")
    curriculum_page._save_curriculum()

    curriculum_id = runtime.curriculum_service.repository.get_all()[0].id

    _select_combo_data(application_page.company_combo, company_id)
    application_page._load_jobs()
    _select_combo_data(application_page.job_combo, job_id)
    application_page.status_combo.setCurrentText("Rascunho")
    application_page.application_date_input.setDate(QDate(2026, 8, 3))
    application_page.next_follow_up_input.setDate(QDate(2026, 8, 10))
    application_page.response_date_input.setDate(QDate(2026, 8, 4))
    application_page.interview_date_input.setDate(QDate(2026, 8, 5))
    application_page.salary_expected_input.setText("12000")
    application_page.salary_offered_input.setText("11000")
    application_page.channel_input.setText("LinkedIn")
    application_page.recruiter_name_input.setText("Recrutador Sintetico")
    application_page.recruiter_email_input.setText("recrutador@example.test")
    application_page.recruiter_phone_input.setText("+55 11 99999-0000")
    application_page.feedback_input.setPlainText("Sem feedback inicial.")
    application_page.notes_input.setPlainText("Observacoes sinteticas para busca.")
    application_page._save_application()

    application = runtime.application_service.list_applications()[0]
    runtime.curriculum_service.associate_to_application(
        application_id=application.id,
        curriculum_id=curriculum_id,
    )
    runtime.application_service.change_status(application.id, "Pronta para Aplicação")

    interview_page._load_applications()
    _select_combo_data(interview_page.application_combo, application.id)
    interview_page.datetime_input.setDateTime(QDateTime(QDate(2026, 8, 5), QTime(10, 30)))
    interview_page.type_combo.setCurrentText("RH")
    interview_page.interviewer_input.setText("Maria Sintetica")
    interview_page.interviewer_email_input.setText("maria@example.test")
    interview_page.link_input.setText("https://meet.example/aceite")
    interview_page.location_input.setText("Online")
    interview_page.duration_input.setText("45m")
    interview_page.notes_input.setPlainText("Entrevista sintética para o aceite do MVP.")
    interview_page.feedback_input.setPlainText("Fluxo sem bloqueios.")
    interview_page.result_combo.setCurrentText("Agendada")
    interview_page._save_interview()

    return {
        "company_id": company_id,
        "job_id": job_id,
        "curriculum_id": curriculum_id,
        "application_id": application.id,
        "interview_id": runtime.interview_service.list_interviews()[0].id,
    }


def test_mvp_workflow_creates_and_filters_records(acceptance_runtime) -> None:
    ids = _seed_mvp_flow(acceptance_runtime)

    assert acceptance_runtime.company_page.table.rowCount() == 1
    assert acceptance_runtime.job_page.table.rowCount() == 1
    assert acceptance_runtime.curriculum_page.table.rowCount() == 1
    assert acceptance_runtime.application_page.table.rowCount() == 1
    assert acceptance_runtime.interview_page.table.rowCount() == 1

    acceptance_runtime.company_page.search_input.setText("Sintetica")
    acceptance_runtime.company_page._search_companies()
    assert acceptance_runtime.company_page.table.rowCount() == 1

    acceptance_runtime.job_page.search_input.setText("Analista")
    acceptance_runtime.job_page._filter_jobs()
    assert acceptance_runtime.job_page.table.rowCount() == 1

    acceptance_runtime.curriculum_page.search_input.setText("MVP")
    acceptance_runtime.curriculum_page._search_curricula()
    assert acceptance_runtime.curriculum_page.table.rowCount() == 1

    acceptance_runtime.application_page.search_input.setText("Observacoes")
    acceptance_runtime.application_page._filter_applications()
    assert acceptance_runtime.application_page.table.rowCount() == 1

    acceptance_runtime.interview_page.search_input.setText("Maria")
    acceptance_runtime.interview_page._filter_interviews()
    assert acceptance_runtime.interview_page.table.rowCount() == 1

    acceptance_runtime.dashboard.refresh_kpis()
    assert acceptance_runtime.dashboard.total_companies_card.valor_label.text() == "1"
    assert acceptance_runtime.dashboard.total_jobs_card.valor_label.text() == "1"
    assert acceptance_runtime.dashboard.total_applications_card.valor_label.text() == "1"
    assert acceptance_runtime.dashboard.total_interviews_card.valor_label.text() == "1"
    assert acceptance_runtime.dashboard.total_curricula_card.valor_label.text() == "1"
    assert acceptance_runtime.dashboard.most_used_curriculum_card.valor_label.text() == "1"

    application = acceptance_runtime.application_service.get_application(ids["application_id"])
    assert application is not None
    assert application.curriculum_id == ids["curriculum_id"]
    assert application.curriculum_version == "v1.0"
    assert acceptance_runtime.application_service.get_followups(ids["application_id"])


def test_mvp_data_survives_application_reopen(acceptance_runtime, monkeypatch, qtbot) -> None:
    ids = _seed_mvp_flow(acceptance_runtime)
    workspace = acceptance_runtime.workspace
    database_path = acceptance_runtime.database_path

    acceptance_runtime.close()

    reopened = build_acceptance_runtime(
        monkeypatch,
        qtbot,
        workspace,
        database_path=database_path,
    )
    try:
        reopened.dashboard.refresh_kpis()
        assert reopened.company_page.table.rowCount() == 1
        assert reopened.job_page.table.rowCount() == 1
        assert reopened.curriculum_page.table.rowCount() == 1
        assert reopened.application_page.table.rowCount() == 1
        assert reopened.interview_page.table.rowCount() == 1
        assert reopened.dashboard.total_companies_card.valor_label.text() == "1"
        assert reopened.dashboard.total_jobs_card.valor_label.text() == "1"
        assert reopened.dashboard.total_applications_card.valor_label.text() == "1"
        assert reopened.dashboard.total_interviews_card.valor_label.text() == "1"
        assert reopened.dashboard.total_curricula_card.valor_label.text() == "1"

        application = reopened.application_service.get_application(ids["application_id"])
        assert application is not None
        assert application.curriculum_id == ids["curriculum_id"]
        assert application.status == "Pronta para Aplicação"
        assert reopened.application_service.get_followups(ids["application_id"])
    finally:
        reopened.close()
