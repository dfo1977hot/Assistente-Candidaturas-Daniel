from pathlib import Path


def test_job_page_formats_offered_remuneration_as_currency() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "self.salary_min_input = QDoubleSpinBox()" in source
    assert 'self.salary_min_input.setSpecialValueText("A combinar")' in source
    assert "self.salary_min_input.setGroupSeparatorShown(True)" in source
    assert "QLocale(QLocale.Portuguese, QLocale.Brazil)" in source
    assert 'self.salary_min_input.setPrefix("R$ ")' in source


def test_job_page_has_recruiter_email_next_to_recruiter_and_empty_benefits() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "self.recruiter_email_input = QLineEdit()" in source
    assert 'second_column.addRow(QLabel("E-mail"), self.recruiter_email_input)' in source
    assert "self.benefits_input.setPlaceholderText" not in source
    assert "recruiter_email=recruiter_email" in source
    assert 'getattr(job, "recruiter_email", "")' in source
