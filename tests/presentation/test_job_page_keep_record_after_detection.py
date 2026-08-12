from pathlib import Path


def test_detected_application_url_is_saved_without_clearing_current_record() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "self._save_job(clear_after=False, show_success=False)" in source


def test_save_without_clear_reselects_current_job_row() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "selected_job_id = self.current_job_id" in source
    assert "self._select_job_row_by_id(selected_job_id)" in source
    assert "def _select_job_row_by_id" in source
    assert "self.table.selectRow(row)" in source
