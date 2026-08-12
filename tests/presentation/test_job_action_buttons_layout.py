from pathlib import Path


def test_job_action_buttons_share_the_same_row() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "for column, button in enumerate(action_buttons):" in source
    assert "actions.addWidget(button, 0, column)" in source
    assert "actions.addWidget(button, index // 3, index % 3)" not in source
