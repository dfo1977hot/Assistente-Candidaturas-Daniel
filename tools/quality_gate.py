"""
ACD Quality Gate

Runs every quality verification used by the project.

Checks:

- Ruff
- Black
- Pytest
- Coverage
- Architecture tests

Exit code:

0 -> success

1 -> failure
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ==========================================================
# Helpers
# ==========================================================


def command_exists(command: str) -> bool:
    """
    Return True if command exists.
    """

    return shutil.which(command) is not None


def run_step(title: str, command: list[str]) -> bool:
    """
    Execute one quality step.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        check=False,
    )

    if result.returncode == 0:

        print(f"PASS - {title}")

        return True

    print(f"FAIL - {title}")

    return False


# ==========================================================
# Main
# ==========================================================


def main() -> int:

    print()
    print("=" * 70)
    print("ACD QUALITY GATE")
    print("=" * 70)

    if not command_exists("ruff"):

        print("ruff not installed.")

        return 1

    if not command_exists("black"):

        print("black not installed.")

        return 1

    ok = True

    ok &= run_step(
        "Ruff",
        [
            "ruff",
            "check",
            ".",
        ],
    )

    ok &= run_step(
        "Black",
        [
            "black",
            "--check",
            ".",
        ],
    )

    ok &= run_step(
        "Architecture Tests",
        [
            "pytest",
            "tests/architecture",
            "-v",
        ],
    )

    ok &= run_step(
        "Unit Tests",
        [
            "pytest",
            "-v",
        ],
    )

    ok &= run_step(
        "Coverage",
        [
            "pytest",
            "--cov=acd",
            "--cov-report=term-missing",
        ],
    )

    print()
    print("=" * 70)

    if ok:

        print("QUALITY GATE PASSED")

        return 0

    print("QUALITY GATE FAILED")

    return 1


if __name__ == "__main__":

    sys.exit(main())