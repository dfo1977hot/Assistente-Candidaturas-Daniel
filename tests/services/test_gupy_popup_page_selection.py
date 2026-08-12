from pathlib import Path


def test_productive_gupy_flow_does_not_depend_on_popup_page_selection() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")
    gupy = source.index('if platform == "Gupy":')
    manual_return = source.index("return AssistedApplicationResult(", gupy)
    assert manual_return > gupy
    assert "Login da Gupy aberto para candidatura manual" in source
