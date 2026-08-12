from pathlib import Path


def test_save_button_uses_keep_record_handler() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert "self.save_button.clicked.connect(self._save_current_job)" in source
    assert "def _save_current_job(self) -> None:" in source
    assert "self._save_job(clear_after=False, show_success=False)" in source


def test_save_button_shows_confirmation_popup() -> None:
    source = Path("acd/presentation/pages/job_page.py").read_text(encoding="utf-8")

    assert 'QMessageBox.information(' in source
    assert '"Registro salvo"' in source
    assert '"O registro foi salvo"' in source
