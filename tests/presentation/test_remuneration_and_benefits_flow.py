from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_job_page_uses_new_remuneration_labels_and_benefits() -> None:
    source = _read("acd/presentation/pages/job_page.py")
    assert 'QLabel("Remuneração oferecida")' in source
    assert 'QLabel("Remuneração ideal")' in source
    assert 'QLabel("Benefícios e valores")' in source
    assert 'self.salary_min_input.setSpecialValueText("A combinar")' in source
    assert 'self.salary_min_input.setPrefix("R$ ")' in source
    assert "QLocale(QLocale.Portuguese, QLocale.Brazil)" in source
    assert "self.benefits_input.setPlaceholderText" not in source


def test_salary_research_persists_ideal_remuneration() -> None:
    source = _read("acd/presentation/pages/job_page.py")
    method = source.split("    def _on_salary_research_succeeded", 1)[1].split(
        "    def _on_salary_research_failed", 1
    )[0]
    assert "self.salary_max_input.setValue(result.salary_max)" in method
    assert "self._save_job(clear_after=False, show_success=False)" in method


def test_application_uses_ideal_remuneration_as_expected_salary() -> None:
    source = _read("acd/presentation/pages/application_page.py")
    method = source.split("    def _populate_salary_from_job", 1)[1].split(
        "    def _save_application", 1
    )[0]
    assert 'self._format_brl_currency(ideal) if ideal is not None else ""' in method
    assert "max(candidates)" not in method
    assert 'else ""' in method


def test_linkedin_import_researches_ideal_and_keeps_advertised_value() -> None:
    source = _read("acd/services/linkedin_saved_jobs_import_service.py")
    assert "offered = max(advertised) if advertised else None" in source
    assert "salary_max=result.median_salary" in source
    assert "_notes_with_benefits" in source
