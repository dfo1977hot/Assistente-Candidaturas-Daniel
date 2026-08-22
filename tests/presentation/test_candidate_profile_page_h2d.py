from __future__ import annotations

import os
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QMessageBox

from acd.presentation.pages.candidate_profile_page import CandidateProfilePage
from acd.services.candidate_profile_service import (
    CandidateProfile,
    CandidateProfileService,
)


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_candidate_profile_page_loads_saved_profile(tmp_path: Path) -> None:
    _app()
    service = CandidateProfileService(tmp_path / "profile.json")
    service.save(
        CandidateProfile(
            full_name="Daniel Oliveira",
            email="daniel@example.com",
            city="Guarulhos",
            state="SP",
            google_account_email="candidate@gmail.com",
        )
    )

    page = CandidateProfilePage(service)

    assert page.full_name.text() == "Daniel Oliveira"
    assert page.email.text() == "daniel@example.com"
    assert page.city.text() == "Guarulhos"
    assert page.state.text() == "SP"
    assert page.google_account_email.text() == "candidate@gmail.com"


def test_candidate_profile_page_saves_form(
    tmp_path: Path,
    monkeypatch,
) -> None:
    _app()
    service = CandidateProfileService(tmp_path / "profile.json")
    page = CandidateProfilePage(service)

    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)

    page.full_name.setText("Daniel Oliveira")
    page.email.setText("daniel@example.com")
    page.phone.setText("11999999999")
    page.city.setText("Guarulhos")
    page.state.setText("SP")
    page.target_role.setText("Coordenador de Logística")
    page.google_account_email.setText("candidate@gmail.com")

    page._save_profile()

    saved = service.load()
    assert saved.full_name == "Daniel Oliveira"
    assert saved.email == "daniel@example.com"
    assert saved.target_role == "Coordenador de Logística"
    assert saved.google_account_email == "candidate@gmail.com"
