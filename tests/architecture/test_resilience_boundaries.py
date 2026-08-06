"""Architecture protections for resilience ownership and finite recovery."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_retry_policy_is_central_and_presentation_has_no_retry_or_sleep() -> None:
    assert (ROOT / "acd/resilience/policy.py").is_file()
    for path in (ROOT / "acd/presentation").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        assert "execute_with_retry" not in source
        assert "time.sleep(" not in source


def test_no_infinite_retry_or_silent_exception_swallowing_in_productive_code() -> None:
    # Developer inventory intentionally skips non-UTF-8 source candidates; it is
    # not a productive operation or recovery path.
    silent_allowlist = {"acd/tools/architecture_inventory.py"}
    for path in (ROOT / "acd").rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.While) and isinstance(node.test, ast.Constant):
                assert node.test.value is not True, f"infinite loop in {path}"
            if isinstance(node, ast.ExceptHandler):
                is_silent = len(node.body) == 1 and isinstance(node.body[0], ast.Pass)
                assert not is_silent or path.relative_to(ROOT).as_posix() in silent_allowlist, (
                    f"silent exception swallowing in {path}"
                )


def test_openai_disables_sdk_retry_and_uses_explicit_timeout_policy() -> None:
    source = (ROOT / "acd/infrastructure/ai/openai_structured_resume_provider.py").read_text(
        encoding="utf-8"
    )
    assert "max_retries=0" in source
    assert "execute_with_retry" in source
    assert "deadline_seconds=self._settings.timeout_seconds" in source


def test_only_official_long_running_executor_owns_qthread() -> None:
    owners = []
    for path in (ROOT / "acd/presentation").rglob("*.py"):
        if "QThread" in path.read_text(encoding="utf-8"):
            owners.append(path.relative_to(ROOT).as_posix())
    assert owners == ["acd/presentation/long_running_task_executor.py"]


def test_restore_validates_before_atomic_replace_and_backup_cleans_partial() -> None:
    source = (ROOT / "acd/infrastructure/database/sqlite_lifecycle.py").read_text(encoding="utf-8")
    assert source.index("self._validate(backup)") < source.index(
        "os.replace(temporary_path, destination)"
    )
    assert "destination.unlink()" in source
    assert '"restore.rolled_back"' in source
