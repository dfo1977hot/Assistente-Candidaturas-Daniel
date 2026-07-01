"""Validate agent handoff artifacts against required contract."""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

ALLOWED_STATUS = {"approved", "blocked", "needs_changes"}
ALLOWED_RISK = {"very_low", "low", "medium", "high"}
REQUIRED_KEYS = {
    "from_agent",
    "to_agent",
    "status",
    "score",
    "risk",
    "artifacts",
    "issues",
    "next_agent",
    "approval",
    "timestamp",
}


def validate(payload: dict) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_KEYS.difference(payload)
    if missing:
        errors.append(f"Missing keys: {sorted(missing)}")

    status = payload.get("status")
    if status not in ALLOWED_STATUS:
        errors.append(f"Invalid status: {status}")

    score = payload.get("score")
    if not isinstance(score, int) or not (0 <= score <= 100):
        errors.append("score must be integer in range 0..100")

    risk = payload.get("risk")
    if risk not in ALLOWED_RISK:
        errors.append(f"Invalid risk: {risk}")

    if not isinstance(payload.get("artifacts"), list):
        errors.append("artifacts must be a list")

    if not isinstance(payload.get("issues"), list):
        errors.append("issues must be a list")

    if not isinstance(payload.get("approval"), bool):
        errors.append("approval must be boolean")

    timestamp = payload.get("timestamp")
    if isinstance(timestamp, str):
        try:
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            errors.append("timestamp must be valid ISO-8601")
    else:
        errors.append("timestamp must be string")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python validate_handoff.py <handoff.json>")
        return 2

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"ERROR: file not found: {path}")
        return 2

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}")
        return 2

    errors = validate(payload)
    if errors:
        print("HANDOFF: INVALID")
        for err in errors:
            print(f"- {err}")
        return 1

    print("HANDOFF: VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
