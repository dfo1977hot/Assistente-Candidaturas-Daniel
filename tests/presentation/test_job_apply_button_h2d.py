from pathlib import Path


def test_job_page_renders_apply_action_column() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")
    assert "[\"ID\", \"Empresa\", \"Cargo\", \"Status\", \"Cidade\", \"Cadastro\", \"Ação\"]" in source
    assert 'QPushButton("Candidatar-se")' in source
    assert "setCellWidget(row, 6, apply_button)" in source
    assert "self._on_apply_job(job_id)" in source


def test_application_page_reuses_existing_application_for_job() -> None:
    source = Path("acd/presentation/pages/application_page.py").read_text(encoding="utf-8")
    start = source.index("def open_job_for_application")
    end = source.index("def _load_jobs", start)
    method = source[start:end]
    assert "self.application_service.list_applications()" in method
    assert "self._select_application_row(int(existing.id))" in method
    assert "self._clear_form()" in method
    assert "self.job_combo.findData(job_id)" in method


def test_composition_routes_job_apply_action_to_applications_page() -> None:
    source = Path("acd/desktop_composition_root.py").read_text(encoding="utf-8")
    assert "application_page.open_job_for_application(job_id)" in source
    assert 'router.navigate("applications")' in source
    assert "on_apply_job=open_job_application" in source
