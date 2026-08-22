"""Candidate profile page used as the source of recurring application data."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.candidate_profile_service import (
    CandidateProfile,
    CandidateProfileService,
)
from acd.services.chrome_profile_service import ChromeProfileService


class CandidateProfilePage(BasePage):
    """Edit candidate identity, professional defaults, and browser identity."""

    def __init__(
        self,
        service: CandidateProfileService,
        chrome_profile_service: ChromeProfileService | None = None,
    ) -> None:
        super().__init__("Perfil do Candidato")
        self._service = service
        self._chrome_profile_service = chrome_profile_service

        self._build_personal_section()
        self._build_professional_section()
        self._build_browser_identity_section()
        self._build_actions()
        self._load_profile()

    def _build_personal_section(self) -> None:
        group = QGroupBox("Dados pessoais")
        form = QFormLayout(group)

        self.full_name = QLineEdit()
        self.email = QLineEdit()
        self.phone = QLineEdit()
        self.city = QLineEdit()
        self.state = QLineEdit()
        self.country = QLineEdit()
        self.linkedin_url = QLineEdit()

        form.addRow("Nome completo*", self.full_name)
        form.addRow("E-mail principal*", self.email)
        form.addRow("Telefone", self.phone)
        form.addRow("Cidade", self.city)
        form.addRow("Estado", self.state)
        form.addRow("País", self.country)
        form.addRow("LinkedIn", self.linkedin_url)

        self.layout.addWidget(group)

    def _build_professional_section(self) -> None:
        group = QGroupBox("Dados profissionais")
        form = QFormLayout(group)

        self.target_role = QLineEdit()
        self.salary_expectation = QLineEdit()
        self.availability = QLineEdit()
        self.work_model = QComboBox()
        self.work_model.setEditable(True)
        self.work_model.addItems(
            ["", "Presencial", "Híbrido", "Remoto", "Presencial / Híbrido", "Híbrido / Remoto", "Flexível"]
        )

        form.addRow("Cargo-alvo", self.target_role)
        form.addRow("Pretensão salarial", self.salary_expectation)
        form.addRow("Disponibilidade", self.availability)
        form.addRow("Modelo de trabalho", self.work_model)

        self.layout.addWidget(group)

    def _build_browser_identity_section(self) -> None:
        group = QGroupBox("Identidade de navegação")
        layout = QVBoxLayout(group)
        form = QFormLayout()

        self.google_account_email = QLineEdit()
        self.google_account_email.setPlaceholderText(
            "Conta Google usada no perfil Chrome do ACD"
        )
        form.addRow("Conta Google", self.google_account_email)
        layout.addLayout(form)

        note = QLabel(
            "A senha do Google não é armazenada pelo ACD. "
            "A autenticação será feita diretamente no Google Chrome e a sessão "
            "será preservada em um perfil exclusivo do ACD."
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        self.browser_status = QLabel("Chrome ACD: verificando perfil...")
        self.browser_status.setWordWrap(True)
        layout.addWidget(self.browser_status)

        self.open_chrome_button = QPushButton("Abrir Chrome para autenticação Google")
        self.open_chrome_button.clicked.connect(self._open_chrome_for_authentication)
        layout.addWidget(self.open_chrome_button)

        self.layout.addWidget(group)

    def _build_actions(self) -> None:
        self.save_button = QPushButton("Salvar perfil")
        self.reload_button = QPushButton("Recarregar")

        self.save_button.clicked.connect(self._save_profile)
        self.reload_button.clicked.connect(self._load_profile)

        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.reload_button)

    def refresh_reference_data(self) -> None:
        self._load_profile()

    def _profile_from_form(self) -> CandidateProfile:
        return CandidateProfile(
            full_name=self.full_name.text(),
            email=self.email.text(),
            phone=self.phone.text(),
            city=self.city.text(),
            state=self.state.text(),
            country=self.country.text(),
            linkedin_url=self.linkedin_url.text(),
            target_role=self.target_role.text(),
            salary_expectation=self.salary_expectation.text(),
            availability=self.availability.text(),
            work_model=self.work_model.currentText(),
            google_account_email=self.google_account_email.text(),
        ).normalized()

    def _load_profile(self) -> None:
        profile = self._service.load()

        self.full_name.setText(profile.full_name)
        self.email.setText(profile.email)
        self.phone.setText(profile.phone)
        self.city.setText(profile.city)
        self.state.setText(profile.state)
        self.country.setText(profile.country)
        self.linkedin_url.setText(profile.linkedin_url)
        self.target_role.setText(profile.target_role)
        self.salary_expectation.setText(profile.salary_expectation)
        self.availability.setText(profile.availability)
        self.work_model.setCurrentText(profile.work_model)
        self.google_account_email.setText(profile.google_account_email)
        self._refresh_browser_status()

    def _refresh_browser_status(self) -> None:
        service = self._chrome_profile_service
        if service is None:
            self.browser_status.setText("Chrome ACD: serviço não configurado.")
            self.open_chrome_button.setEnabled(False)
            return

        status = service.status()
        if not status.available:
            self.browser_status.setText(
                "Chrome ACD: Google Chrome não encontrado neste computador."
            )
            self.open_chrome_button.setEnabled(False)
            return

        state = "perfil inicializado" if status.initialized else "aguardando autenticação"
        self.browser_status.setText(
            f"Chrome ACD: {state}. Perfil: {status.profile_dir}"
        )
        self.open_chrome_button.setEnabled(True)

    def _open_chrome_for_authentication(self) -> None:
        service = self._chrome_profile_service
        if service is None:
            QMessageBox.warning(
                self,
                "Chrome ACD",
                "Serviço do Google Chrome não configurado.",
            )
            return

        try:
            service.open_for_google_authentication()
        except Exception as exc:
            QMessageBox.critical(self, "Chrome ACD", str(exc))
            return

        self._refresh_browser_status()
        QMessageBox.information(
            self,
            "Chrome ACD",
            "O Google Chrome foi aberto com o perfil exclusivo do ACD. "
            "Entre na sua conta Google e, ao terminar, feche todas as janelas "
            "desse Chrome antes de iniciar uma candidatura assistida.",
        )

    def _save_profile(self) -> None:
        profile = self._profile_from_form()
        missing = profile.missing_required_fields()
        if missing:
            QMessageBox.warning(
                self,
                "Perfil do Candidato",
                "Preencha os campos obrigatórios: " + ", ".join(missing) + ".",
            )
            return

        saved = self._service.save(profile)
        self._load_profile()
        QMessageBox.information(
            self,
            "Perfil do Candidato",
            f"Perfil de {saved.full_name} salvo com sucesso.",
        )
