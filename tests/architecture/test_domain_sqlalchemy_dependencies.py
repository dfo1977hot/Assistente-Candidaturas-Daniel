"""Monotonic guard for the temporary domain SQLAlchemy exception."""

from __future__ import annotations

import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "quality" / "domain-sqlalchemy-baseline.json"


def _imports_sqlalchemy(path: Path) -> bool:
    """Return whether a module imports SQLAlchemy directly."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            if any(
                alias.name == "sqlalchemy" or alias.name.startswith("sqlalchemy.")
                for alias in node.names
            ):
                return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "sqlalchemy" or node.module.startswith("sqlalchemy."):
                return True
    return False


def _current_modules() -> set[str]:
    """Return normalized paths for domain modules importing SQLAlchemy."""
    domain_root = ROOT / "acd" / "domain"
    return {
        path.relative_to(ROOT).as_posix()
        for path in domain_root.rglob("*.py")
        if _imports_sqlalchemy(path)
    }


def test_domain_sqlalchemy_dependencies_do_not_increase() -> None:
    """Permit only the ADR-028 baseline and require its monotonic decrease."""
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    allowed = set(baseline["allowed_existing_modules"])
    current = _current_modules()

    assert baseline["policy"] == "monotonic-decrease"
    assert baseline["target"] == 0
    assert baseline["adr"] == "ADR-028"
    assert baseline["module_count"] == len(allowed), (
        "The domain SQLAlchemy baseline module_count does not match its allowlist."
    )
    assert len(current) <= baseline["module_count"], (
        "Domain SQLAlchemy imports increased from the approved baseline: "
        f"baseline={baseline['module_count']}, current={len(current)}"
    )
    assert not current - allowed, (
        "New domain modules import SQLAlchemy outside the ADR-028 baseline:\n"
        + "\n".join(sorted(current - allowed))
    )
