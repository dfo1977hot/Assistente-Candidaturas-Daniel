"""Regression tests for selected-curriculum workflow on Applications page."""

from __future__ import annotations

import ast
from pathlib import Path

SOURCE_PATH = Path("acd/presentation/pages/application_page.py")
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")


def _method_source(name: str) -> str:
    tree = ast.parse(SOURCE)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            lines = SOURCE.splitlines()
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise AssertionError(f"Método {name!r} não encontrado.")


def test_select_curriculum_button_is_not_part_of_visible_actions() -> None:
    build_start = SOURCE.index("action_buttons = (")
    build_end = SOURCE.index(")", build_start)
    actions = SOURCE[build_start:build_end]

    assert "self.select_curriculum_button" not in actions
    assert "self.analyze_resume_button" in actions
    assert "self.optimize_resume_button" in actions


def test_curriculum_combo_controls_analysis_and_optimization_availability() -> None:
    assert "self.curriculum_combo.currentIndexChanged.connect(" in SOURCE
    method = _method_source("_on_curriculum_selection_changed")

    assert "self.curriculum_combo.currentData()" in method
    assert "self.analyze_resume_button.setEnabled(can_use_curriculum)" in method
    assert "self.optimize_resume_button.setEnabled(" in method


def test_analysis_automatically_associates_selected_curriculum() -> None:
    method = _method_source("_analyze_resume_match")

    assert "_associate_selected_curriculum()" in method
    assert "Selecione um currículo no campo Currículo antes de continuar." in method
    assert "Selecione e associe um currículo." not in method


def test_optimization_automatically_associates_selected_curriculum() -> None:
    method = _method_source("_optimize_resume")

    assert "_associate_selected_curriculum()" in method
    assert "source_curriculum_id = int(selected_curriculum_id)" in method
    assert "Selecione um currículo no campo Currículo antes de continuar." in method
    assert "Selecione e associe um currículo" not in method
