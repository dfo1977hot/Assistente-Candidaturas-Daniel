from pathlib import Path


def test_expected_salary_uses_only_job_ideal_remuneration() -> None:
    source = Path("acd/presentation/pages/application_page.py").read_text(
        encoding="utf-8"
    )
    assert 'ideal = float(job.salary_max) if job.salary_max is not None else None' in source
    assert 'self._format_brl_currency(ideal) if ideal is not None else ""' in source
    assert "max(candidates)" not in source


def test_response_date_starts_blank() -> None:
    source = Path("acd/presentation/pages/application_page.py").read_text(
        encoding="utf-8"
    )
    assert "self.response_date_input," in source
    assert "optional_date_input.setSpecialValueText(\" \")" in source
    assert "optional_date_input.setDate(optional_date_input.minimumDate())" in source
    assert "self.response_date_input.setDate(self.response_date_input.minimumDate())" in source
