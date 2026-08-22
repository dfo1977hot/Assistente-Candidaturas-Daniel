from pathlib import Path

JOB_PAGE = Path("acd/presentation/pages/job_page.py")


def test_job_table_enables_header_sorting() -> None:
    source = JOB_PAGE.read_text(encoding="utf-8")

    assert "self.table.setSortingEnabled(True)" in source
    assert "class _SortableTableWidgetItem" in source


def test_job_table_uses_typed_sort_keys_for_id_and_date() -> None:
    source = JOB_PAGE.read_text(encoding="utf-8")

    assert "_SortableTableWidgetItem(str(job.id), int(job.id))" in source
    assert "_SortableTableWidgetItem(created_text, created_key)" in source
    assert "if sorting_enabled and 0 <= sort_column < 6:" in source
