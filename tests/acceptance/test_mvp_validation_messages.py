from __future__ import annotations

from datetime import datetime

from PySide6.QtWidgets import QMessageBox
import pytest


def test_mvp_validation_messages_are_user_friendly(acceptance_runtime, monkeypatch) -> None:
    warnings: list[str] = []

    def warning(_parent, _title: str, text: str) -> int:
        warnings.append(text)
        return QMessageBox.Ok

    monkeypatch.setattr(QMessageBox, "warning", warning)

    acceptance_runtime.company_page.name_input.clear()
    acceptance_runtime.company_page.city_input.clear()
    acceptance_runtime.company_page._save_company()
    assert "Nome é obrigatório." in warnings[-1]

    acceptance_runtime.company_page.name_input.setText("Empresa Sintetica")
    acceptance_runtime.company_page.city_input.setText("Cidade Sintetica")
    acceptance_runtime.company_page.website_input.setText("https://empresa-sintetica.example")
    acceptance_runtime.company_page._save_company()
    acceptance_runtime.job_page._load_companies()

    company_id = acceptance_runtime.company_service.list_companies()[0].id
    index = acceptance_runtime.job_page.company_combo.findData(company_id)
    acceptance_runtime.job_page.company_combo.setCurrentIndex(index)
    acceptance_runtime.job_page.title_input.setText("Analista")
    acceptance_runtime.job_page.url_input.setText("https://vagas.example/analista")
    acceptance_runtime.job_page._save_job()
    job_id = acceptance_runtime.job_service.list_jobs()[0].id
    acceptance_runtime.job_page.company_combo.setCurrentIndex(index)
    acceptance_runtime.job_page.title_input.setText("Analista")
    acceptance_runtime.job_page.current_job_id = job_id
    acceptance_runtime.job_page.url_input.setText("ftp://invalid")
    acceptance_runtime.job_page._save_job()
    assert "URL da vaga deve iniciar com http:// ou https://." in warnings[-1]

    acceptance_runtime.company_page.current_company_id = None
    acceptance_runtime.company_page.name_input.setText("Empresa Sintetica")
    acceptance_runtime.company_page.city_input.setText("Cidade Sintetica")
    acceptance_runtime.company_page.website_input.setText("https://empresa-sintetica.example")
    acceptance_runtime.company_page._save_company()
    assert "Empresa duplicada: nome + site já cadastrado." in warnings[-1]

    acceptance_runtime.application_page._load_companies()
    acceptance_runtime.application_page.company_combo.setCurrentIndex(
        acceptance_runtime.application_page.company_combo.findData(company_id)
    )
    acceptance_runtime.application_page._load_jobs()
    acceptance_runtime.application_page.job_combo.setCurrentIndex(
        acceptance_runtime.application_page.job_combo.findData(job_id)
    )
    application = acceptance_runtime.application_service.create_application(
        job_id=job_id,
        company_id=company_id,
    )

    with pytest.raises(ValueError, match="Transição inválida de Rascunho para Contratada."):
        acceptance_runtime.application_service.change_status(application.id, "Contratada")

    with pytest.raises(ValueError, match="Tipo inválido: Inexistente"):
        acceptance_runtime.interview_service.create_interview(
            application_id=application.id,
            interview_date=datetime(2026, 8, 5, 10, 30),
            interview_type="Inexistente",
        )
