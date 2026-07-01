"""Validate agent contract files against Agent SDK requirements."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED_HEADERS = [
    "## Mission",
    "## Responsibilities",
    "## Restrictions",
    "## Inputs",
    "## Outputs",
    "## Approval Criteria",
    "## Blocking Criteria",
    "## Checklist",
    "## Handoff",
]
REQUIRED_META = [
    r"^name:\s+.+$",
    r"^version:\s+\d+\.\d+\.\d+$",
    r"^api_version:\s+\d+$",
    r"^framework_version:\s+\d+$",
    r"^sdk_version:\s+\d+$",
]


def validate_text(text: str) -> list[str]:
    errors: list[str] = []

    for pattern in REQUIRED_META:
        if not re.search(pattern, text, flags=re.MULTILINE):
            errors.append(f"Missing or invalid metadata: {pattern}")

    for header in REQUIRED_HEADERS:
        if header not in text:
            errors.append(f"Missing section: {header}")

    return errors


def validate_capability_registry(registry_path: Path, agent_name: str) -> list[str]:
    errors: list[str] = []
    if not registry_path.exists():
        return [f"Capability registry not found: {registry_path}"]

    content = registry_path.read_text(encoding="utf-8")
    marker = f"  {agent_name}:"
    if marker not in content:
        errors.append(f"Agent '{agent_name}' not found in capability registry")

    return errors


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python validate_agent.py <agent-contract.md> <agent-name>")
        return 2

    contract_path = Path(sys.argv[1])
    agent_name = sys.argv[2]

    if not contract_path.exists():
        print(f"ERROR: file not found: {contract_path}")
        return 2

    text = contract_path.read_text(encoding="utf-8")
    errors = validate_text(text)

    registry = contract_path.parents[1] / "capability-registry.yaml"
    errors.extend(validate_capability_registry(registry, agent_name))

    if errors:
        print("AGENT: NOT CERTIFIED")
        for err in errors:
            print(f"- {err}")
        return 1

    print("AGENT: CERTIFIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
