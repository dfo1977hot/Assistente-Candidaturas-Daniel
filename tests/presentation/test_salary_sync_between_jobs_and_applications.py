from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_salary_research_success_saves_job_automatically() -> None:
    source = _source("acd/presentation/pages/job_page.py")
    method = source.split(
        "    def _on_salary_research_succeeded", 1
    )[1].split("    def _on_salary_research_failed", 1)[0]

    assert "self.salary_min_input.setValue(result.salary_min)" not in method
    assert "self.salary_max_input.setValue(result.salary_max)" in method
    assert "self._save_job(clear_after=False, show_success=False)" in method
    assert "Remuneração ideal atualizada pela IA e vaga salva." in method


def test_application_page_fills_expected_and_offered_salary_from_job() -> None:
    source = _source("acd/presentation/pages/application_page.py")

    assert (
        "self.job_combo.currentIndexChanged.connect("
        "self._populate_salary_from_job)"
    ) in source
    assert "ideal = float(job.salary_max) if job.salary_max is not None else None" in source
    assert 'f"{ideal:.2f}" if ideal is not None else ""' in source
    assert "(salary_min + salary_max) / 2" not in source
    assert 'self.salary_offered_input.setText("A combinar")' in source
    assert 'normalized.casefold() in {"a combinar", "combinar"}' in source


def test_linkedin_import_persists_advertised_salary_provenance() -> None:
    source = _source("acd/services/linkedin_saved_jobs_import_service.py")

    assert "salary_min=prepared.salary_min" in source
    assert "salary_max=result.salary_max" in source
    assert "salary_min=offered" in source
    assert "salary_max=None" in source
    assert "salary_min=result.salary_min" not in source
