from pathlib import Path


def test_runtime_fallback_strips_one_backslash_character() -> None:
    source = Path(
        "acd/infrastructure/application_automation/playwright_application_browser.py"
    ).read_text(encoding="utf-8")

    expected = 'wrapped = variant[index:end].rstrip("\\\\")'
    assert expected in source
    assert 'wrapped = variant[index:end].rstrip("\\\\\\\\")' not in source
