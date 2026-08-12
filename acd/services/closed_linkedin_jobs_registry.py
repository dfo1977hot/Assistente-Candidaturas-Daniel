"""Persistent registry for LinkedIn vacancies with closed applications."""

from __future__ import annotations

import json
from pathlib import Path
import re
from threading import RLock


class ClosedLinkedInJobsRegistry:
    """Store closed LinkedIn job identifiers so they are never reimported."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or (Path.home() / ".acd" / "closed_linkedin_jobs.json")
        self._lock = RLock()

    def ids(self) -> set[str]:
        with self._lock:
            if not self._path.exists():
                return set()
            try:
                payload = json.loads(self._path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                return set()
            values = payload.get("linkedin_job_ids", [])
            return {str(value).strip() for value in values if str(value).strip()}

    def contains(self, linkedin_job_id: str) -> bool:
        normalized = linkedin_job_id.strip()
        return bool(normalized) and normalized in self.ids()

    def mark_closed(self, linkedin_job_id: str) -> None:
        normalized = linkedin_job_id.strip()
        if not normalized:
            return
        with self._lock:
            values = self.ids()
            if normalized in values:
                return
            values.add(normalized)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self._path.with_suffix(self._path.suffix + ".tmp")
            temporary.write_text(
                json.dumps(
                    {"linkedin_job_ids": sorted(values)},
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            temporary.replace(self._path)

    @staticmethod
    def job_id_from_url(url: str) -> str:
        match = re.search(
            r"(?:currentJobId=|/jobs/view/(?:[^/?]+-)?)(\d{6,})",
            url or "",
        )
        return match.group(1) if match else ""
