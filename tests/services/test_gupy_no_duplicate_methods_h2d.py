from __future__ import annotations

import ast
from pathlib import Path

SOURCE_PATH = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
)


def _source() -> str:
    return SOURCE_PATH.read_text(encoding="utf-8")


def _browser_class() -> ast.ClassDef:
    tree = ast.parse(_source())
    return next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "PlaywrightApplicationBrowser"
    )


def test_browser_class_has_no_duplicate_methods() -> None:
    names = [
        node.name
        for node in _browser_class().body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]
    duplicates = sorted(
        name for name in set(names) if names.count(name) > 1
    )
    assert duplicates == []


def test_gupy_resolver_is_static_and_passwordless_first() -> None:
    source = _source()
    marker = (
        "    @staticmethod\n"
        "    def _resolve_gupy_candidate_page(page: object) -> object:"
    )
    assert marker in source

    start = source.index(marker)
    tail = source[start:]
    assert tail.index('"/candidates/passwordless-signin"') < tail.index(
        '"/candidates/signin"'
    )


def test_gupy_has_no_password_login_path() -> None:
    source = _source()

    assert "_try_gupy_password_login" not in source
    assert "_fill_gupy_password_login" not in source
    assert "_configured_login_for_gupy_page" not in source
    assert "self._click_gupy_passwordless_entry(auth_surface, progress)" in source
