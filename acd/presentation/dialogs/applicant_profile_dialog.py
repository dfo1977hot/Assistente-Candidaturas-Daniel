"""Dialog for applicant data used by assisted application preparation."""

from __future__ import annotations

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout

from acd.services.assisted_application_service import ApplicantProfile


class ApplicantProfileDialog(QDialog):
    def __init__(self, profile: ApplicantProfile | None = None, parent: object | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Dados para candidatura assistida")
        current = profile or ApplicantProfile(full_name="", email="")
        self.full_name = QLineEdit(current.full_name)
        self.email = QLineEdit(current.email)
        self.phone = QLineEdit(current.phone)
        self.city = QLineEdit(current.city)
        self.linkedin_url = QLineEdit(current.linkedin_url)
        form = QFormLayout()
        form.addRow("Nome completo*", self.full_name)
        form.addRow("E-mail*", self.email)
        form.addRow("Telefone", self.phone)
        form.addRow("Cidade", self.city)
        form.addRow("LinkedIn", self.linkedin_url)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def profile(self) -> ApplicantProfile:
        return ApplicantProfile(
            full_name=self.full_name.text().strip(),
            email=self.email.text().strip(),
            phone=self.phone.text().strip(),
            city=self.city.text().strip(),
            linkedin_url=self.linkedin_url.text().strip(),
        )
