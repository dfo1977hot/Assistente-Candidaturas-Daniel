"""Block when structural changes are detected without ADR updates."""

from __future__ import annotations

import sys
from pathlib import Path

STRUCTURAL_PATH_HINTS = (
    "acd/domain/",
    "acd/infrastructure/",
    "acd/database/",
    "acd/models/",
    "acd/core/",
)
ADR_INDEX = Path("docs/architecture/adr/ADR-INDEX.md")


def has_structural_change(changed_paths: list[str]) -> bool:
    return any(path.startswith(STRUCTURAL_PATH_HINTS) for path in changed_paths)


def has_adr_update(changed_paths: list[str]) -> bool:
    return any(path.startswith("docs/architecture/adr/") for path in changed_paths)


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python validate_adr_requirement.py <changed-path> [<changed-path> ...]")
        return 2

    changed = sys.argv[1:]
    structural = has_structural_change(changed)
    adr_updated = has_adr_update(changed)

    if structural and not adr_updated:
        print("ADR CHECK: BLOCKED")
        print("- Structural change detected without ADR update")
        return 1

    if not ADR_INDEX.exists():
        print("ADR CHECK: BLOCKED")
        print("- Missing ADR index: docs/architecture/adr/ADR-INDEX.md")
        return 1

    print("ADR CHECK: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
