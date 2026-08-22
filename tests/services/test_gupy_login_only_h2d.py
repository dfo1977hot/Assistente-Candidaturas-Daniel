"""Regression tests for Gupy login-only assisted application flow."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_PATH = Path(
    "acd/infrastructure/application_automation/playwright_application_browser.py"
)


def _method_source(name: str) -> str:
    source = SOURCE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = source.splitlines()
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise AssertionError(f"Método não encontrado: {name}")


def test_prepare_stops_gupy_automation_after_login() -> None:
    method = _method_source("prepare")

    gupy_start = method.index('if platform == "Gupy":')
    else_start = method.index("else:", gupy_start)
    gupy_branch = method[gupy_start:else_start]

    assert "self._prepare_gupy(page, profile, progress)" in gupy_branch
    assert "_prepare_gupy_post_auth" not in gupy_branch
    assert "_fill_profile" not in gupy_branch
    assert "_attach_resume" not in gupy_branch
    assert "fields_filled = 0" in gupy_branch
    assert "resume_attached = False" in gupy_branch
    assert "preencha manualmente" in gupy_branch


def test_prepare_gupy_does_not_return_to_application_after_login() -> None:
    method = _method_source("_prepare_gupy")
    source = SOURCE_PATH.read_text(encoding="utf-8")

    assert 'locator("#passwordlessSignin")' in source
    assert "_wait_for_gupy_authenticated_page" in method
    assert "_return_to_gupy_application" not in method
    assert "preenchimento seguirá manualmente" in method


def test_prepare_gupy_accepts_existing_authenticated_candidate_page() -> None:
    method = _method_source("_prepare_gupy")

    assert "_gupy_application_page_is_ready(page)" in method
    assert "_gupy_authenticated_candidate_page(page)" in method
    assert "preenchimento será manual" in method
