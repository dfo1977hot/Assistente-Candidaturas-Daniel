"""Semiautomatic application preparation with mandatory human review."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
from pathlib import Path
from urllib.parse import urlparse


@dataclass(frozen=True, slots=True)
class ApplicantProfile:
    full_name: str
    email: str
    phone: str = ""
    city: str = ""
    linkedin_url: str = ""


@dataclass(frozen=True, slots=True)
class AssistedApplicationResult:
    platform: str
    url: str
    fields_filled: int
    resume_attached: bool
    linkedin_restricted_mode: bool
    source_url_opened: bool = False


class ApplicantProfileStore:
    """Persist the user's own form data locally, outside the database schema."""

    def __init__(self, path: str | Path = "data/assisted_application_profile.json") -> None:
        self.path = Path(path)

    def load(self) -> ApplicantProfile | None:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return ApplicantProfile(
            full_name=str(data.get("full_name", "")).strip(),
            email=str(data.get("email", "")).strip(),
            phone=str(data.get("phone", "")).strip(),
            city=str(data.get("city", "")).strip(),
            linkedin_url=str(data.get("linkedin_url", "")).strip(),
        )

    def save(self, profile: ApplicantProfile) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(profile), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class AssistedApplicationService:
    """Prepare an application form without ever submitting it automatically."""

    def __init__(self, browser: object, profile_store: ApplicantProfileStore | None = None) -> None:
        self.browser = browser
        self.profile_store = profile_store or ApplicantProfileStore()


    def prepare(
        self,
        *,
        job_url: str,
        profile: ApplicantProfile,
        resume_path: str | Path | None,
        source_url: str | None = None,
        progress: Callable[[object], None] | None = None,
    ) -> AssistedApplicationResult:
        url = job_url.strip()
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise ValueError("A vaga não possui uma URL válida para candidatura.")
        if not profile.full_name or not profile.email:
            raise ValueError("Nome completo e e-mail são obrigatórios.")
        self.profile_store.save(profile)
        source = (source_url or "").strip()
        if source:
            parsed_source = urlparse(source)
            if parsed_source.scheme not in {"http", "https"} or not parsed_source.netloc:
                raise ValueError("A URL de origem da vaga é inválida.")
        callback = progress or (lambda _value: None)
        callback((10, "Abrindo a plataforma"))
        return self.browser.prepare(
            url=url,
            source_url=source or None,
            profile=profile,
            resume_path=None if resume_path is None else Path(resume_path),
            progress=callback,
        )
