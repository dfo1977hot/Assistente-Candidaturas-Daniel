from acd.presentation.dialogs.linkedin_saved_jobs_progress_dialog import (
    LinkedInSavedJobsProgressDialog,
)
from acd.services.linkedin_saved_jobs_import_service import SavedJobsProgress


def test_progress_dialog_updates(qtbot):
    dialog = LinkedInSavedJobsProgressDialog()
    qtbot.addWidget(dialog)
    dialog.update_progress(
        SavedJobsProgress(
            "importing",
            "Processando",
            current=2,
            total=5,
            title="Cargo",
            company_name="Empresa",
            imported=1,
        )
    )
    assert dialog.progress_bar.value() == 2
    assert "Cargo" in dialog.current_label.text()
    assert "Importadas: 1" in dialog.summary_label.text()
