"""Regression tests for Gupy magic-link authentication flow."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_PATH = Path(
    "acd/infrastructure/application_automation/"
    "playwright_application_browser.py"
)
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")


def _method_source(name: str) -> str:
    tree = ast.parse(SOURCE)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name == name:
                lines = SOURCE.splitlines()
                start = node.lineno - 1
                end = node.end_lineno or node.lineno
                return "`n".join(lines[start:end])

    raise AssertionError(f"Método {name!r} não encontrado.")


def test_magic_link_authentication_stops_after_session_confirmation() -> None:
    assert "_wait_for_gupy_authenticated_page" in SOURCE


def test_gupy_login_only_does_not_resume_post_auth_automation() -> None:
    method = _method_source("_prepare_gupy")

    assert "_return_to_gupy_application(" not in method
    assert "_open_gupy_application_after_authentication(" not in method
    assert "_prepare_gupy_post_auth(" not in method
    assert "_fill_profile(" not in method
    assert "_attach_resume(" not in method
