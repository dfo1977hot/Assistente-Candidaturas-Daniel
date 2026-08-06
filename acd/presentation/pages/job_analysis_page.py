from __future__ import annotations

from PySide6.QtWidgets import (
    QApplication,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.services.job_analysis_service import JobAnalysisService


class JobAnalysisPage(QWidget):
    """Página simples para analisar descrições de vagas."""

    def __init__(self, service: JobAnalysisService, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.job_id_input = QLineEdit()
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Cole a descrição da vaga...")
        form.addRow("ID da vaga", self.job_id_input)
        form.addRow("Descrição", self.description_input)
        layout.addLayout(form)
        self.analyze_button = QPushButton("Analisar vaga")
        self.analyze_button.clicked.connect(self.analyze)
        layout.addWidget(self.analyze_button)
        self.result_label = QLabel("Aguardando análise...")
        layout.addWidget(self.result_label)

    def analyze(self) -> None:
        try:
            job_id = int(self.job_id_input.text().strip())
        except ValueError:
            QMessageBox.warning(self, "Erro", "Informe um ID de vaga válido")
            return
        description = self.description_input.toPlainText().strip()
        if not description:
            QMessageBox.warning(self, "Erro", "Informe a descrição da vaga")
            return
        profile = self.service.analyze_job(job_id=job_id, raw_description=description)
        self.result_label.setText(f"Perfil criado com sucesso: {profile.id if profile else 'erro'}")


if __name__ == "__main__":
    app = QApplication([])
    window = JobAnalysisPage()
    window.show()
    app.exec()
