from pathlib import Path

JOB_PAGE = Path("acd/presentation/pages/job_page.py")


def _method(source: str, name: str, next_name: str) -> str:
    start = source.index(f"def {name}")
    end = source.index(f"def {next_name}", start)
    return source[start:end]


def test_salary_research_passes_company_context() -> None:
    source = JOB_PAGE.read_text(encoding="utf-8")
    method = _method(source, "_research_salary", "_on_salary_research_succeeded")

    assert "company=self.company_combo.currentText().strip()" in method


def test_salary_research_keeps_originating_job_selected() -> None:
    source = JOB_PAGE.read_text(encoding="utf-8")
    research = _method(source, "_research_salary", "_on_salary_research_succeeded")
    succeeded = _method(
        source,
        "_on_salary_research_succeeded",
        "_on_salary_research_failed",
    )
    finished = _method(
        source,
        "_on_salary_research_finished",
        "_save_current_job",
    )

    assert "self._salary_research_job_id = self.current_job_id" in research
    assert "self.table.setEnabled(False)" in research
    assert "self._filter_jobs()" in succeeded
    assert "self._select_job_row_by_id(selected_job_id)" in succeeded
    assert "self.table.setEnabled(True)" in finished
    assert "self._select_job_row_by_id(selected_job_id)" in finished
