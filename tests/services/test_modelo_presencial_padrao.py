from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_single_linkedin_import_defaults_to_presencial() -> None:
    source = _read("acd/services/linkedin_job_import_service.py")
    assert (
        'work_model=cls._choice(data.get("work_model"), '
        '{"Presencial", "Híbrido", "Remoto"}) or "Presencial"'
    ) in source
    assert (
        "- Se o modelo de trabalho não puder ser determinado, use Presencial."
        in source
    )


def test_saved_jobs_import_defaults_to_presencial() -> None:
    source = _read("acd/services/linkedin_saved_jobs_import_service.py")
    assert 'reference.work_model or "Presencial"' in source
    assert 'job.work_model.strip() or "Presencial"' in source


def test_job_page_shows_presencial_when_model_is_missing() -> None:
    source = _read("acd/presentation/pages/job_page.py")
    assert 'self.work_model_combo.setCurrentText(result.work_model or "Presencial")' in source
    assert 'self.work_model_combo.setCurrentText(job.work_model or "Presencial")' in source
