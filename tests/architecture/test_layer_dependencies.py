"""
Architectural dependency tests.

These tests enforce the dependency rules adopted by the ACD project.

Allowed dependency direction:

    presentation
          │
          ▼
    application
          │
          ▼
      services
          │
          ▼
      domain
          │
          ▼
       models

Infrastructure is allowed to depend on domain/models/core but must
never depend on presentation.

These tests prevent architectural regressions.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACD_ROOT = PROJECT_ROOT / "acd"


# ==========================================================
# Rules
# ==========================================================

FORBIDDEN_IMPORTS: dict[str, tuple[str, ...]] = {
    "domain": (
        "acd.presentation",
        "acd.ui",
    ),
    "services": (
        "acd.presentation",
        "acd.ui",
    ),
    "models": (
        "acd.presentation",
        "acd.services",
    ),
    "database": (
        "acd.presentation",
    ),
    "infrastructure": (
        "acd.presentation",
        "acd.ui",
    ),
}


# ==========================================================
# Helpers
# ==========================================================


def iter_python_files(package: str):
    """
    Iterate over every Python file inside a package.
    """

    root = ACD_ROOT / package

    if not root.exists():
        return

    for file in root.rglob("*.py"):

        if "__pycache__" in file.parts:
            continue

        yield file


def imported_modules(file: Path) -> set[str]:
    """
    Return imported module names.
    """

    source = file.read_text(encoding="utf-8")

    tree = ast.parse(source)

    modules: set[str] = set()

    for node in ast.walk(tree):

        if isinstance(node, ast.Import):

            for alias in node.names:
                modules.add(alias.name)

        elif isinstance(node, ast.ImportFrom):

            if node.module:
                modules.add(node.module)

    return modules


# ==========================================================
# Tests
# ==========================================================


def test_architecture_dependencies() -> None:
    """
    Validate forbidden imports between layers.
    """

    violations: list[str] = []

    for package, forbidden in FORBIDDEN_IMPORTS.items():

        for file in iter_python_files(package):

            if file is None:
                continue

            imports = imported_modules(file)

            for module in imports:

                for forbidden_module in forbidden:

                    if module.startswith(forbidden_module):

                        relative = file.relative_to(PROJECT_ROOT)

                        violations.append(
                            f"{relative} -> {module}"
                        )

    assert not violations, (
        "\nForbidden architectural dependencies detected:\n\n"
        + "\n".join(sorted(violations))
    )


# ==========================================================
# Dependency direction
# ==========================================================


def test_domain_does_not_import_ui() -> None:
    """
    Domain must never import UI.
    """

    violations = []

    for file in iter_python_files("domain"):

        imports = imported_modules(file)

        for module in imports:

            if module.startswith("acd.ui"):

                violations.append(file.relative_to(PROJECT_ROOT))

    assert violations == []


def test_domain_does_not_import_presentation() -> None:
    """
    Domain must remain independent.
    """

    violations = []

    for file in iter_python_files("domain"):

        imports = imported_modules(file)

        for module in imports:

            if module.startswith("acd.presentation"):

                violations.append(file.relative_to(PROJECT_ROOT))

    assert violations == []


def test_services_do_not_import_ui() -> None:
    """
    Services should not depend on UI.
    """

    violations = []

    for file in iter_python_files("services"):

        imports = imported_modules(file)

        for module in imports:

            if module.startswith("acd.ui"):

                violations.append(file.relative_to(PROJECT_ROOT))

    assert violations == []


def test_infrastructure_does_not_import_presentation() -> None:
    """
    Infrastructure must remain presentation independent.
    """

    violations = []

    for file in iter_python_files("infrastructure"):

        imports = imported_modules(file)

        for module in imports:

            if module.startswith("acd.presentation"):

                violations.append(file.relative_to(PROJECT_ROOT))

    assert violations == []


# ==========================================================
# Sanity
# ==========================================================


def test_architecture_packages_exist() -> None:
    """
    Verify that expected packages exist.
    """

    expected = (
        "application",
        "core",
        "database",
        "domain",
        "infrastructure",
        "models",
        "presentation",
        "services",
    )

    missing = []

    for package in expected:

        if not (ACD_ROOT / package).exists():
            missing.append(package)

    assert not missing, (
        "Missing packages:\n"
        + "\n".join(sorted(missing))
    )