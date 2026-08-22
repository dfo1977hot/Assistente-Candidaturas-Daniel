from __future__ import annotations

import ast
from pathlib import Path

SOURCE_PATH = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
)


def _source() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _browser() -> ast.ClassDef:
    tree = ast.parse(_source())
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "PlaywrightApplicationBrowser"
    )


def test_passwordless_methods_are_unique() -> None:
    names = [
        node.name
        for node in _browser().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    assert names.count("_wait_for_gupy_passwordless_page") == 1
    assert names.count("_fill_gupy_passwordless_email") == 1


def test_passwordless_email_fills_safe_visible_input() -> None:
    source = _source()
    start = source.index("    def _fill_gupy_passwordless_email(")
    tail = source[start:]

    assert 'page.get_by_role("textbox")' in tail
    assert 'page.locator("input")' in tail
    assert "candidate.fill(email_address)" in tail
    assert '"password",' in tail
