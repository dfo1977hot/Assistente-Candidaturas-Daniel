from pathlib import Path


def test_recruiter_email_is_below_recruiter() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    recruiter = 'second_column.addRow(QLabel("Recrutador"), self.recruiter_input)'
    email = 'second_column.addRow(QLabel("E-mail"), self.recruiter_email_input)'
    priority = 'second_column.addRow(QLabel("Prioridade"), self.priority_input)'

    assert recruiter in source
    assert email in source
    assert priority in source
    assert source.index(recruiter) < source.index(email) < source.index(priority)
    assert "recruiter_row = QHBoxLayout()" not in source
