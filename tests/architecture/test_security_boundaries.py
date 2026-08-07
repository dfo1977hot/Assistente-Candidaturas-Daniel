from __future__ import annotations

import ast
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACD_ROOT = PROJECT_ROOT / "acd"


def _production_sources() -> list[Path]:
    return sorted(ACD_ROOT.rglob("*.py"))


def test_no_unsafe_execution_or_deserialization_primitives() -> None:
    forbidden = ("shell=True", "shell = True", "pickle.loads", "yaml.load(")
    violations: list[str] = []
    for path in _production_sources():
        source = path.read_text(encoding="utf-8")
        if any(token in source for token in forbidden):
            violations.append(str(path.relative_to(PROJECT_ROOT)))
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"eval", "exec"}
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}:{node.lineno}")
    assert not violations


def test_secret_environment_access_is_centralized_with_documented_exceptions() -> None:
    allowed = {
        Path("acd/security/secret_provider.py"),
        Path("acd/database/local_state.py"),
        Path("acd/infrastructure/platform/configuration_provider.py"),
    }
    violations = []
    for path in _production_sources():
        source = path.read_text(encoding="utf-8")
        if "os.environ" in source or "os.getenv" in source:
            relative = path.relative_to(PROJECT_ROOT)
            if relative not in allowed:
                violations.append(str(relative))
    assert not violations


def test_plugin_loader_has_explicit_deny_by_default_controls() -> None:
    source = (ACD_ROOT / "infrastructure/release/plugin_loader.py").read_text(
        encoding="utf-8"
    )
    assert "allowed_plugins" in source
    assert "PluginRejectedError" in source
    assert "AuthorizedPathPolicy" in source
    assert "sys.path" not in source
    assert "exec_module" in source


def test_presentation_does_not_read_secrets() -> None:
    violations = []
    for path in (ACD_ROOT / "presentation").rglob("*.py"):
        source = path.read_text(encoding="utf-8")
        forbidden = ("OPENAI_API_KEY", "SecretProvider", "os.environ", "os.getenv")
        if any(token in source for token in forbidden):
            violations.append(str(path.relative_to(PROJECT_ROOT)))
    assert not violations


def test_openai_adapter_uses_central_security_boundaries() -> None:
    source = (
        ACD_ROOT / "infrastructure/ai/openai_structured_resume_provider.py"
    ).read_text(encoding="utf-8")
    assert "EnvironmentSecretProvider" in source
    assert "bounded_untrusted_text" in source
    assert "validate_external_https_url" in source
    assert "os.environ" not in source


def test_example_environment_and_wheel_configuration_exclude_local_state() -> None:
    example = (PROJECT_ROOT / ".env.example").read_text(encoding="utf-8")
    entries = {
        line.partition("=")[0]: line.partition("=")[2].strip()
        for line in example.splitlines()
        if "=" in line
    }
    assert entries["OPENAI_API_KEY"] == ""
    assert entries["LINKEDIN_PASSWORD"] == ""
    pyproject = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'include = ["acd*"]' in pyproject
    assert 'acd = "acd.desktop:main"' in pyproject

