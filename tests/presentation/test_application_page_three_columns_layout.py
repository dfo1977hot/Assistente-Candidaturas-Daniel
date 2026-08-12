from pathlib import Path


def _source() -> str:
    return Path(
        "acd/presentation/pages/application_page.py"
    ).read_text(encoding="utf-8")


def test_application_form_is_split_into_three_columns() -> None:
    source = _source()

    assert "first_column = QFormLayout()" in source
    assert "second_column = QFormLayout()" in source
    assert "third_column = QFormLayout()" in source
    assert "form_columns.addLayout(first_column, 1)" in source
    assert "form_columns.addLayout(second_column, 1)" in source
    assert "form_columns.addLayout(third_column, 1)" in source


def test_full_width_text_fields_have_reduced_height() -> None:
    source = _source()

    assert "self.feedback_input.setMaximumHeight(90)" in source
    assert "self.notes_input.setMaximumHeight(90)" in source
    assert "self.resume_match_details.setMaximumHeight(120)" in source
    assert 'full_width_fields.addRow(QLabel("Feedback"), self.feedback_input)' in source
    assert 'full_width_fields.addRow(QLabel("Observações"), self.notes_input)' in source


def test_action_buttons_are_at_the_end_of_the_page() -> None:
    source = _source()

    actions = "self.content_layout.addLayout(actions)"
    final_panel = "self.content_layout.addWidget(self.optimization_status_label)"

    assert actions in source
    assert final_panel in source
    assert source.index(final_panel) < source.index(actions)
    assert "actions = QGridLayout()" in source
    assert "actions.addWidget(button, index // 3, index % 3)" in source
