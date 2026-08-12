from pathlib import Path

PAGES = (
    "company_page.py",
    "curriculum_page.py",
    "interview_page.py",
    "job_page.py",
)


def _source(page_name: str) -> str:
    return Path(
        "acd/presentation/pages"
    ).joinpath(page_name).read_text(encoding="utf-8")


def test_remaining_form_pages_use_three_columns() -> None:
    for page_name in PAGES:
        source = _source(page_name)

        assert "form_columns = QHBoxLayout()" in source
        assert "first_column = QFormLayout()" in source
        assert "second_column = QFormLayout()" in source
        assert "third_column = QFormLayout()" in source
        assert "form_columns.addLayout(first_column, 1)" in source
        assert "form_columns.addLayout(second_column, 1)" in source
        assert "form_columns.addLayout(third_column, 1)" in source


def test_long_text_fields_keep_full_width_and_reduced_height() -> None:
    company = _source("company_page.py")
    curriculum = _source("curriculum_page.py")
    interview = _source("interview_page.py")
    job = _source("job_page.py")

    assert 'full_width_fields.addRow(QLabel("Observações"), self.notes_input)' in company
    assert "self.notes_input.setMaximumHeight(90)" in company

    assert 'full_width_fields.addRow(QLabel("Descrição"), self.description_input)' in curriculum
    assert "self.description_input.setMaximumHeight(90)" in curriculum

    assert 'full_width_fields.addRow(QLabel("Observações"), self.notes_input)' in interview
    assert 'full_width_fields.addRow(QLabel("Feedback"), self.feedback_input)' in interview
    assert "self.notes_input.setMaximumHeight(90)" in interview
    assert "self.feedback_input.setMaximumHeight(90)" in interview

    assert 'full_width_fields.addRow(QLabel("Link da vaga"), link_layout)' in job
    assert (
        'full_width_fields.addRow(QLabel("URL da candidatura"), '
        "application_url_layout)"
    ) in job
    assert 'full_width_fields.addRow(QLabel("Observações"), self.notes_input)' in job
    assert "self.notes_input.setMaximumHeight(90)" in job


def test_action_buttons_are_at_the_end_in_grid_layouts() -> None:
    for page_name in PAGES:
        source = _source(page_name)

        assert "actions = QGridLayout()" in source
        assert "self.layout.addLayout(actions)" in source
        assert source.index("self.layout.addWidget(self.table)") < source.index(
            "self.layout.addLayout(actions)"
        )
