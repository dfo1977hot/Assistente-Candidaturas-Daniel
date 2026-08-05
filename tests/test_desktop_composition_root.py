"""Architecture tests for the sole productive desktop composition path."""

from __future__ import annotations

import ast
from pathlib import Path
import sys

import acd.desktop as desktop_module
from acd.desktop_composition_root import DesktopCompositionRoot
from acd.ui.main_window import MainWindow

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _imports_from(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        imported
        for node in ast.walk(tree)
        for imported in (
            [node.module or ""]
            if isinstance(node, ast.ImportFrom)
            else [alias.name for alias in node.names]
            if isinstance(node, ast.Import)
            else []
        )
    }


def test_desktop_composition_root_builds_the_official_runtime(qapp) -> None:
    window = DesktopCompositionRoot().build_main_window()

    assert isinstance(window, MainWindow)
    assert window.stack.count() == 14
    assert window.router.pages["applications"] is window.application_page
    assert "new_application" not in window.router.pages
    assert "applications/new" not in window.router.pages


def test_experimental_wizard_is_not_composed_by_the_productive_runtime() -> None:
    root_source = (PROJECT_ROOT / "acd" / "desktop_composition_root.py").read_text(
        encoding="utf-8"
    )

    assert "NewApplicationPage" not in root_source
    assert "ApplicationWizard" not in root_source
    assert "ApplicationFacade" not in root_source


def test_app_uses_only_the_desktop_composition_root() -> None:
    app_source = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
    desktop_source = (PROJECT_ROOT / "acd" / "desktop.py").read_text(encoding="utf-8")

    assert "from acd.desktop import main" in app_source
    assert "DesktopCompositionRoot().build_main_window()" in desktop_source
    assert "from acd.desktop_composition_root import DesktopCompositionRoot" in desktop_source
    forbidden_in_compatibility_launcher = (
        "DesktopCompositionRoot",
        "create_database",
        "create_engine",
        "SessionLocal",
        "MainWindow",
    )
    assert not any(token in app_source for token in forbidden_in_compatibility_launcher)


def test_desktop_main_builds_shows_and_returns_the_event_loop_code(monkeypatch) -> None:
    events: list[object] = []

    class Application:
        def __init__(self, arguments: list[str]) -> None:
            events.append(("application", arguments))

        def exec(self) -> int:
            events.append("exec")
            return 17

    class Window:
        def show(self) -> None:
            events.append("show")

    class CompositionRoot:
        def build_main_window(self) -> Window:
            events.append("build")
            return Window()

    class Theme:
        @staticmethod
        def load(application: Application) -> None:
            events.append(("theme", application))

    monkeypatch.setattr(desktop_module, "QApplication", Application)
    monkeypatch.setattr(desktop_module, "DesktopCompositionRoot", CompositionRoot)
    monkeypatch.setattr(desktop_module, "ThemeManager", Theme)

    assert desktop_module.main() == 17
    assert events[0] == ("application", sys.argv)
    assert [event if isinstance(event, str) else event[0] for event in events] == [
        "application",
        "theme",
        "build",
        "show",
        "exec",
    ]


def test_presentation_does_not_import_infrastructure_or_sqlalchemy() -> None:
    forbidden = ("acd.infrastructure", "acd.database", "sqlalchemy")
    violations = [
        path
        for directory in (PROJECT_ROOT / "acd" / "presentation", PROJECT_ROOT / "acd" / "ui")
        for path in directory.rglob("*.py")
        if any(module.startswith(forbidden) for module in _imports_from(path))
    ]

    assert violations == []


def test_presentation_does_not_construct_services_or_repositories() -> None:
    forbidden = ("Service(", "Repository(", "SessionLocal(")
    violations = [
        path
        for directory in (PROJECT_ROOT / "acd" / "presentation", PROJECT_ROOT / "acd" / "ui")
        for path in directory.rglob("*.py")
        if any(token in path.read_text(encoding="utf-8") for token in forbidden)
    ]

    assert violations == []


def test_productive_runtime_does_not_initialize_kernel_or_bootstrap() -> None:
    source = (PROJECT_ROOT / "acd" / "desktop_composition_root.py").read_text(encoding="utf-8")

    assert "Bootstrap(" not in source
    assert "Kernel(" not in source
    assert "DependencyContainer" not in source


def test_productive_runtime_does_not_import_isolated_legacy_components() -> None:
    """The launcher and root must not reactivate legacy or experimental paths."""
    isolated_prefixes = (
        "acd.core.kernel",
        "acd.repositories",
        "acd.application.application_facade",
        "acd.presentation.pages.application_wizard",
        "acd.presentation.pages.new_application",
        "acd.presentation.pages.new_application_view_model",
    )
    runtime_paths = (
        PROJECT_ROOT / "app.py",
        PROJECT_ROOT / "acd" / "desktop.py",
        PROJECT_ROOT / "acd" / "desktop_composition_root.py",
    )

    violations = {
        path.relative_to(PROJECT_ROOT): module
        for path in runtime_paths
        for module in _imports_from(path)
        if module.startswith(isolated_prefixes)
    }

    assert violations == {}


def test_parallel_agent_domains_are_distinct_registered_bounded_contexts() -> None:
    from acd.database.model_registry import EXPECTED_ORM_TABLES
    from acd.domain.agent.agent_goal import AgentGoal
    from acd.domain.agents.agent import Agent
    from acd.domain.agents.task import AgentTask

    assert AgentGoal.__table__.name == "agent_goals"
    assert Agent.__table__.name == "agents"
    assert AgentTask.__table__.name == "multi_agent_tasks"
    assert len({AgentGoal.__table__, Agent.__table__, AgentTask.__table__}) == 3
    assert {"agent_goals", "agents", "multi_agent_tasks"} <= EXPECTED_ORM_TABLES
