from pathlib import Path


def source() -> str:
    return Path("acd/presentation/pages/letter_page.py").read_text(encoding="utf-8")


def test_letter_page_uses_real_background_executor_and_progress_bar() -> None:
    value = source()
    assert "LongRunningTaskExecutor" in value
    assert "QProgressBar" in value
    assert "execute_with_context(generation_task)" in value
    assert "QTimer" not in value


def test_conflicting_controls_are_disabled_but_cancel_stays_available() -> None:
    value = source()
    method = value.split("    def _set_generation_running", 1)[1]
    assert "self.generate_button" in method
    assert "self.save_button" in method
    assert "self.docx_button" in method
    assert "control.setEnabled(not running)" in method
    assert "self.cancel_button.setEnabled(running)" in method


def test_success_keeps_and_reselects_generated_record() -> None:
    value = source()
    method = value.split("    def _on_generation_succeeded", 1)[1].split(
        "    def _on_generation_failed", 1
    )[0]
    assert "self.current_letter_id = int(letter_id)" in method
    assert "self._select_row(self.current_letter_id)" in method
    assert "self._on_row_selected()" in method
    assert "self._clear()" not in method


def test_cancellation_does_not_delete_a_version_already_persisted() -> None:
    value = source()
    method = value.split("    def _on_generation_cancelled", 1)[1].split(
        "    def _on_generation_finished", 1
    )[0]
    assert "delete_letter" not in method
    assert "versão válida foi preservada" in method


def test_export_and_copy_do_not_change_version_or_database() -> None:
    value = source()
    copy_method = value.split("    def _copy", 1)[1].split("    def _export_docx", 1)[0]
    export_method = value.split("    def _export(self", 1)[1].split(
        "    def _select_row", 1
    )[0]
    assert "save_letter" not in copy_method
    assert "version_input.setText" not in copy_method
    assert "save_letter" not in export_method
    assert "version_input.setText" not in export_method


def test_presentation_does_not_import_infrastructure_or_construct_services() -> None:
    value = source()
    assert "acd.infrastructure" not in value
    assert "CoverLetterService()" not in value
    assert "JobService()" not in value
    assert "CurriculumService()" not in value
