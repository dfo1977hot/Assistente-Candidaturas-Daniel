from __future__ import annotations

import json
from pathlib import Path

from acd.services.candidate_profile_service import (
    CandidateProfile,
    CandidateProfileService,
)


def test_candidate_profile_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "candidate_profile.json"
    service = CandidateProfileService(path)

    saved = service.save(
        CandidateProfile(
            full_name="  Daniel Oliveira  ",
            email="  daniel@example.com ",
            phone=" 11999999999 ",
            city=" Guarulhos ",
            state=" SP ",
            linkedin_url=" https://www.linkedin.com/in/example ",
            target_role=" Coordenador de Logística ",
            google_account_email=" candidate@gmail.com ",
        )
    )

    assert saved.full_name == "Daniel Oliveira"
    assert saved.email == "daniel@example.com"
    assert service.load() == saved


def test_candidate_profile_defaults_when_file_missing(tmp_path: Path) -> None:
    service = CandidateProfileService(tmp_path / "missing.json")

    profile = service.load()

    assert profile == CandidateProfile()
    assert profile.country == "Brasil"


def test_candidate_profile_ignores_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "candidate_profile.json"
    path.write_text("{invalid", encoding="utf-8")

    assert CandidateProfileService(path).load() == CandidateProfile()


def test_candidate_profile_required_fields() -> None:
    profile = CandidateProfile(full_name="", email="")

    assert profile.missing_required_fields() == ("Nome completo", "E-mail")


def test_candidate_profile_file_contains_no_google_password(tmp_path: Path) -> None:
    path = tmp_path / "candidate_profile.json"
    service = CandidateProfileService(path)
    service.save(
        CandidateProfile(
            full_name="Daniel Oliveira",
            email="daniel@example.com",
            google_account_email="candidate@gmail.com",
        )
    )

    raw = json.loads(path.read_text(encoding="utf-8"))

    assert "google_account_email" in raw
    assert not any("password" in key.casefold() or "senha" in key.casefold() for key in raw)
