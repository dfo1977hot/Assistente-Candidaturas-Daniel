"""
Architectural tests for the ACD project structure.

These tests verify that the expected directory structure of the
project remains intact.

The goal is to detect accidental renames, deletions or moves of
critical packages before they break the application.
"""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def exists(relative: str) -> bool:
    """Return True if a path exists."""

    return (PROJECT_ROOT / relative).exists()


def test_project_root_exists() -> None:
    assert PROJECT_ROOT.exists()


# ==========================================================
# Root files
# ==========================================================


def test_pyproject_exists() -> None:
    assert exists("pyproject.toml")


def test_acd_package_exists() -> None:
    assert exists("acd")


def test_tests_package_exists() -> None:
    assert exists("tests")


# ==========================================================
# Core
# ==========================================================


def test_core_package_exists() -> None:
    assert exists("acd/core")


def test_database_package_exists() -> None:
    assert exists("acd/database")


def test_models_package_exists() -> None:
    assert exists("acd/models")


# ==========================================================
# Application
# ==========================================================


def test_application_package_exists() -> None:
    assert exists("acd/application")


# ==========================================================
# Domain
# ==========================================================


def test_domain_package_exists() -> None:
    assert exists("acd/domain")


def test_entities_package_exists() -> None:
    assert exists("acd/domain/entities")


def test_agents_package_exists() -> None:
    assert exists("acd/domain/agents")


def test_agent_package_exists() -> None:
    assert exists("acd/domain/agent")


# ==========================================================
# Infrastructure
# ==========================================================


def test_infrastructure_package_exists() -> None:
    assert exists("acd/infrastructure")


def test_repository_package_exists() -> None:
    assert exists("acd/infrastructure/repositories")


# ==========================================================
# Services
# ==========================================================


def test_services_package_exists() -> None:
    assert exists("acd/services")


# ==========================================================
# Presentation
# ==========================================================


def test_presentation_package_exists() -> None:
    assert exists("acd/presentation")


def test_ui_package_exists() -> None:
    assert exists("acd/ui")


# ==========================================================
# Templates
# ==========================================================


def test_templates_package_exists() -> None:
    assert exists("acd/templates")


# ==========================================================
# Tests
# ==========================================================


def test_architecture_directory_exists() -> None:
    assert exists("tests")


# ==========================================================
# __init__.py validation
# ==========================================================


def test_every_python_package_contains_init() -> None:
    """
    Every package inside the production code must contain an
    __init__.py file.

    Namespace packages are intentionally not used.
    """

    ignored = {
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".git",
        ".venv",
        "venv",
    }

    acd_root = PROJECT_ROOT / "acd"

    for directory in acd_root.rglob("*"):

        if not directory.is_dir():
            continue

        if any(part in ignored for part in directory.parts):
            continue

        has_python = any(
            child.is_file() and child.suffix == ".py"
            for child in directory.iterdir()
        )

        if not has_python:
            continue

        init_file = directory / "__init__.py"

        assert init_file.exists(), (
            f"Missing __init__.py in package:\n{directory}"
        )


# ==========================================================
# Duplicate module names
# ==========================================================


def test_no_duplicate_module_names() -> None:
    """
    Detect duplicate module names inside the production code.

    Test modules, tools, documentation and legacy files are ignored.
    """

    ignored = {
        "__init__.py",
    }

    modules: dict[str, list[Path]] = {}

    acd_root = PROJECT_ROOT / "acd"

    for file in acd_root.rglob("*.py"):

        if any(
            part in {
                "__pycache__",
                ".git",
                ".venv",
                ".pytest_cache",
                ".ruff_cache",
            }
            for part in file.parts
        ):
            continue

        if file.name in ignored:
            continue

        modules.setdefault(file.name, []).append(file)

    duplicates = {
        name: files
        for name, files in modules.items()
        if len(files) > 1
    }

    allowed_duplicates = {
        "settings.py",
        "logger.py",
        "constants.py",
        "recommendation_engine.py",
        "planner_score_engine.py",
        "company_repository.py",
        "project_metrics.py",
        "rule_engine.py",
        "migration_service.py",
        "metrics_service.py",
        "session.py",
        "recommendation.py",
        "skill_gap.py",
        "agent_repository.py",
        "generate_recommendations.py",
    }

    duplicates = {
        name: paths
        for name, paths in duplicates.items()
        if name not in allowed_duplicates
    }

    assert not duplicates, (
        "Unexpected duplicate module names detected:\n"
        + "\n".join(
            f"{name}:\n"
            + "\n".join(f"  - {path}" for path in paths)
            for name, paths in duplicates.items()
        )
    )


# ==========================================================
# Empty directories
# ==========================================================


def test_no_empty_python_packages() -> None:
    """
    Every production package must contain at least one implementation
    module or one child package.

    Reserved extension packages are allowed.
    """

    ignored = {
        "__pycache__",
        ".git",
        ".venv",
        "venv",
    }

    allowed_empty_packages = {
        "automation",
        "ai",
        "plugins",
        "kernel",
        "utils",
    }

    acd_root = PROJECT_ROOT / "acd"

    for directory in acd_root.rglob("*"):

        if not directory.is_dir():
            continue

        if any(part in ignored for part in directory.parts):
            continue

        if directory.name in allowed_empty_packages:
            continue

        init_file = directory / "__init__.py"

        if not init_file.exists():
            continue

        python_modules = [
            item
            for item in directory.iterdir()
            if (
                item.is_file()
                and item.suffix == ".py"
                and item.name != "__init__.py"
            )
        ]

        child_packages = [
            item
            for item in directory.iterdir()
            if (
                item.is_dir()
                and item.name != "__pycache__"
            )
        ]

        if python_modules or child_packages:
            continue

        doc = init_file.read_text(
            encoding="utf-8"
        ).strip()

        assert doc, (
            "Reserved package must contain at least "
            "a module docstring:\n"
            f"{directory}"
        )