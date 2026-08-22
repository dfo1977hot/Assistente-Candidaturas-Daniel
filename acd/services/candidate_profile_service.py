"""Persisted candidate profile used by assisted applications."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any


@dataclass(frozen=True, slots=True)
class CandidateProfile:
    """Single source of truth for recurring candidate data."""

    full_name: str = ""
    email: str = ""
    phone: str = ""
    city: str = ""
    state: str = ""
    country: str = "Brasil"
    linkedin_url: str = ""
    target_role: str = ""
    salary_expectation: str = ""
    availability: str = ""
    work_model: str = ""
    google_account_email: str = ""

    def normalized(self) -> CandidateProfile:
        return CandidateProfile(
            full_name=self.full_name.strip(),
            email=self.email.strip(),
            phone=self.phone.strip(),
            city=self.city.strip(),
            state=self.state.strip(),
            country=self.country.strip() or "Brasil",
            linkedin_url=self.linkedin_url.strip(),
            target_role=self.target_role.strip(),
            salary_expectation=self.salary_expectation.strip(),
            availability=self.availability.strip(),
            work_model=self.work_model.strip(),
            google_account_email=self.google_account_email.strip(),
        )

    def missing_required_fields(self) -> tuple[str, ...]:
        missing: list[str] = []
        if not self.full_name.strip():
            missing.append("Nome completo")
        if not self.email.strip():
            missing.append("E-mail")
        return tuple(missing)


class CandidateProfileService:
    """Load and save candidate profile data without storing account passwords."""

    DEFAULT_PATH = Path("data/settings/candidate_profile.json")

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or self.DEFAULT_PATH

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> CandidateProfile:
        if not self._path.exists():
            return CandidateProfile()

        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return CandidateProfile()

        if not isinstance(raw, dict):
            return CandidateProfile()

        allowed = CandidateProfile.__dataclass_fields__.keys()
        values: dict[str, Any] = {
            key: str(raw.get(key, "") or "")
            for key in allowed
        }
        return CandidateProfile(**values).normalized()

    def save(self, profile: CandidateProfile) -> CandidateProfile:
        normalized = profile.normalized()
        self._path.parent.mkdir(parents=True, exist_ok=True)

        payload = json.dumps(
            asdict(normalized),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self._path.parent,
            prefix=f"{self._path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temp:
            temp.write(payload)
            temp.write("\n")
            temp_path = Path(temp.name)

        temp_path.replace(self._path)
        return normalized

    def clear(self) -> None:
        try:
            self._path.unlink()
        except FileNotFoundError:
            return
