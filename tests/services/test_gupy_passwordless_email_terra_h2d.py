from pathlib import Path

SOURCE = Path(
    "acd/infrastructure/application_automation/"
    "playwright_application_browser.py"
).read_text(encoding="utf-8")


def test_gupy_passwordless_email_comes_from_candidate_profile() -> None:
    assert "passwordless_email = profile.email.strip()" in SOURCE
    assert 'passwordless_email = "dfo1977@terra.com.br"' not in SOURCE


def test_gupy_passwordless_email_uses_semantic_textbox() -> None:
    start = SOURCE.index("    def _fill_gupy_passwordless_email(")
    method = SOURCE[start:]

    assert 'page.get_by_role("textbox")' in method
    assert "candidate.fill(email_address)" in method


def test_gupy_passwordless_email_rejects_unsafe_input_types() -> None:
    start = SOURCE.index("    def _fill_gupy_passwordless_email(")
    method = SOURCE[start:]

    for input_type in (
        '"password"',
        '"hidden"',
        '"submit"',
        '"button"',
        '"checkbox"',
        '"radio"',
        '"file"',
    ):
        assert input_type in method
