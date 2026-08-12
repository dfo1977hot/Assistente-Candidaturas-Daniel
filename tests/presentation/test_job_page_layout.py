from pathlib import Path


def test_job_page_places_search_and_listing_before_edit_form() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    search = source.index("self.layout.addLayout(search_layout)")
    filters = source.index("self.layout.addLayout(filter_layout)")
    table = source.index("self.layout.addWidget(self.table)")
    form = source.index("self.layout.addLayout(form_columns)")

    assert search < filters < table < form


def test_job_page_uses_three_column_edit_form() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "form_columns = QHBoxLayout()" in source
    assert "first_column = QFormLayout()" in source
    assert "second_column = QFormLayout()" in source
    assert "third_column = QFormLayout()" in source
    assert "form_columns.addLayout(first_column, 1)" in source
    assert "form_columns.addLayout(second_column, 1)" in source
    assert "form_columns.addLayout(third_column, 1)" in source
