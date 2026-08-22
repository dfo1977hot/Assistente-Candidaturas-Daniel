"""Regression tests for Gupy login-only post-authentication behavior."""

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


def test_prepare_gupy_does_not_return_to_application_after_authentication() -> None:
    method = _method_source("_prepare_gupy")

    assert "_return_to_gupy_application(" not in method
    assert "_open_gupy_application_after_authentication(" not in method


def test_prepare_gupy_stops_before_application_form_automation() -> None:
    method = _method_source("_prepare_gupy")

    assert "_prepare_gupy_post_auth(" not in method
    assert "_fill_profile(" not in method
    assert "_attach_resume(" not in method
