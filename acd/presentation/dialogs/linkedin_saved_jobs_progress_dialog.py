"""Progress dialog for LinkedIn saved-jobs import."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from acd.services.linkedin_saved_jobs_import_service import (
    SavedJobsImportResult,
    SavedJobsProgress,
)


class LinkedInSavedJobsProgressDialog(QDialog):
    """Modal progress UI with cooperative cancellation."""

    cancel_requested = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Importar vagas salvas do LinkedIn")
        self.setModal(True)
        self.setMinimumWidth(620)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)

        self.status_label = QLabel("Preparando importação...")
        self.current_label = QLabel("")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.summary_label = QLabel("Importadas: 0 | Existentes: 0 | Falhas: 0 | Empresas: 0")
        self.details = QPlainTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumBlockCount(200)
        self.cancel_button = QPushButton("Cancelar")
        self.close_button = QPushButton("Fechar")
        self.close_button.setVisible(False)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.cancel_button)
        buttons.addWidget(self.close_button)

        layout = QVBoxLayout(self)
        layout.addWidget(self.status_label)
        layout.addWidget(self.current_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.details)
        layout.addLayout(buttons)

        self.cancel_button.clicked.connect(self._request_cancel)
        self.close_button.clicked.connect(self.accept)

    def update_progress(self, progress: SavedJobsProgress) -> None:
        self.status_label.setText(progress.message)
        if progress.total > 0:
            self.progress_bar.setRange(0, progress.total)
            self.progress_bar.setValue(progress.current)
            self.current_label.setText(
                f"{progress.current} de {progress.total} — "
                f"{progress.title or 'Vaga sem título'} — "
                f"{progress.company_name or 'Empresa não identificada'}"
            )
        else:
            self.progress_bar.setRange(0, 0)
            self.current_label.clear()
        self.summary_label.setText(
            f"Importadas: {progress.imported} | Existentes: {progress.existing} | "
            f"Falhas: {progress.failed} | Empresas: {progress.companies_created}"
        )
        self.details.appendPlainText(progress.message)

    def show_result(self, result: SavedJobsImportResult) -> None:
        self.progress_bar.setRange(0, max(1, result.found))
        self.progress_bar.setValue(result.found)
        self.status_label.setText("Importação concluída.")
        self.current_label.setText(f"{result.found} vaga(s) encontrada(s).")
        self.summary_label.setText(
            f"Importadas: {result.imported} | Existentes: {result.existing} | "
            f"Falhas: {result.failed} | Empresas: {result.companies_created}"
        )
        for error in result.errors:
            self.details.appendPlainText(f"Falha: {error}")
        self.cancel_button.setVisible(False)
        self.close_button.setVisible(True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)
        self.show()

    def show_failure(self, message: str) -> None:
        self.status_label.setText("Não foi possível concluir a importação.")
        self.details.appendPlainText(message)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setValue(0)
        self.cancel_button.setVisible(False)
        self.close_button.setVisible(True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)
        self.show()

    def show_cancelled(self) -> None:
        self.status_label.setText("Importação cancelada.")
        self.cancel_button.setVisible(False)
        self.close_button.setVisible(True)
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)
        self.show()

    def _request_cancel(self) -> None:
        self.cancel_button.setEnabled(False)
        self.cancel_button.setText("Cancelando...")
        self.cancel_requested.emit()
