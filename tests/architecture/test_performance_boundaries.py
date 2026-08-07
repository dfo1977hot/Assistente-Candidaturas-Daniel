"""Architecture constraints for performance, capacity and benchmarks."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_presentation_has_no_direct_openai_or_blocking_sleep() -> None:
    for path in (ROOT / "acd/presentation").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [alias.name for alias in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert not any(
                    module == "openai" or module.startswith("openai.") for module in modules
                )
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                is_sleep = (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "time"
                    and node.func.attr == "sleep"
                )
                assert not is_sleep, f"time.sleep in {path}"


def test_no_unbounded_standard_queue_or_second_qthread_owner() -> None:
    qthread_owners = []
    for path in (ROOT / "acd").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        if "QThread" in source:
            qthread_owners.append(path.relative_to(ROOT).as_posix())
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if node.func.attr in {"Queue", "LifoQueue", "PriorityQueue"}:
                    assert node.args or any(k.arg == "maxsize" for k in node.keywords), path
    assert qthread_owners == ["acd/presentation/long_running_task_executor.py"]


def test_benchmarks_and_profiles_are_not_package_data() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "tests/performance" not in pyproject
    assert "benchmarks" not in pyproject
    assert "*.prof" not in pyproject
