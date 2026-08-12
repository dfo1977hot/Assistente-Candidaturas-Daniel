"""Página de configurações, APIs, credenciais e diagnóstico."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.settings_service import LoginCredential, SettingsService


class SettingsPage(BasePage):
    """Centraliza preferências não sensíveis e segredos protegidos pelo keyring."""

    def __init__(self, service: SettingsService) -> None:
        super().__init__("Configurações")
        self._service = service
        self._selected_login_service = ""

        self._build_startup_section()
        self._build_browser_section()
        self._build_api_section()
        self._build_login_section()
        self._build_diagnostics_section()
        self._load_settings()

    def _build_startup_section(self) -> None:
        group = QGroupBox("Inicialização")
        layout = QFormLayout(group)
        self.startup_mode = QComboBox()
        self.startup_mode.addItem("Maximizado", "maximized")
        self.startup_mode.addItem("Minimizado", "minimized")
        layout.addRow("Abrir aplicativo", self.startup_mode)
        self.layout.addWidget(group)

    def _build_browser_section(self) -> None:
        group = QGroupBox("Navegador e automações")
        layout = QVBoxLayout(group)
        self.browser_headless = QCheckBox(
            "Executar importação e detecção de links do LinkedIn em segundo plano"
        )
        self.browser_headless.setToolTip(
            "Quando marcado, o Chrome/Chromium do Playwright roda sem janela visível. "
            "A candidatura manual continua abrindo o navegador normalmente."
        )
        layout.addWidget(self.browser_headless)
        self.layout.addWidget(group)

    def _build_api_section(self) -> None:
        group = QGroupBox("APIs e Inteligência Artificial")
        grid = QGridLayout(group)

        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.openai_key.setPlaceholderText("sk-...")
        self.google_key = QLineEdit()
        self.google_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.google_key.setPlaceholderText("Chave da API Google")

        self.toggle_secrets_button = QPushButton("Mostrar/Ocultar")
        self.test_openai_button = QPushButton("Testar OpenAI")
        self.api_status = QLabel("Não testada")
        self.api_status.setWordWrap(True)

        grid.addWidget(QLabel("OpenAI API Key"), 0, 0)
        grid.addWidget(self.openai_key, 0, 1, 1, 3)
        grid.addWidget(QLabel("Google API Key"), 1, 0)
        grid.addWidget(self.google_key, 1, 1, 1, 3)
        grid.addWidget(self.toggle_secrets_button, 2, 1)
        grid.addWidget(self.test_openai_button, 2, 2)
        grid.addWidget(self.api_status, 3, 0, 1, 4)

        self.toggle_secrets_button.clicked.connect(self._toggle_secret_visibility)
        self.test_openai_button.clicked.connect(self._test_openai)
        self.layout.addWidget(group)

    def _build_login_section(self) -> None:
        group = QGroupBox("Cofre de Logins")
        outer = QVBoxLayout(group)

        self.login_table = QTableWidget(0, 4)
        self.login_table.setHorizontalHeaderLabels(["Serviço", "URL", "Usuário/E-mail", "Observações"])
        self.login_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.login_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.login_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.login_table.setMaximumHeight(180)
        self.login_table.itemSelectionChanged.connect(self._load_selected_login)
        outer.addWidget(self.login_table)

        columns = QHBoxLayout()
        left = QFormLayout()
        middle = QFormLayout()
        right = QFormLayout()

        self.login_service = QLineEdit()
        self.login_url = QLineEdit()
        self.login_username = QLineEdit()
        self.login_password = QLineEdit()
        self.login_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_notes = QTextEdit()
        self.login_notes.setMaximumHeight(70)

        left.addRow("Serviço", self.login_service)
        left.addRow("URL", self.login_url)
        middle.addRow("Usuário/E-mail", self.login_username)
        middle.addRow("Senha", self.login_password)
        right.addRow("Observações", self.login_notes)
        columns.addLayout(left, 1)
        columns.addLayout(middle, 1)
        columns.addLayout(right, 1)
        outer.addLayout(columns)

        actions = QGridLayout()
        self.save_login_button = QPushButton("Salvar login")
        self.new_login_button = QPushButton("Novo/Limpar")
        self.delete_login_button = QPushButton("Excluir login")
        actions.addWidget(self.save_login_button, 0, 0)
        actions.addWidget(self.new_login_button, 0, 1)
        actions.addWidget(self.delete_login_button, 0, 2)
        outer.addLayout(actions)

        self.save_login_button.clicked.connect(self._save_login)
        self.new_login_button.clicked.connect(self._clear_login_form)
        self.delete_login_button.clicked.connect(self._delete_login)
        self.layout.addWidget(group)

    def _build_diagnostics_section(self) -> None:
        group = QGroupBox("Diagnóstico e sugestões")
        layout = QVBoxLayout(group)
        self.diagnostics = QLabel()
        self.diagnostics.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.diagnostics.setWordWrap(True)
        layout.addWidget(self.diagnostics)
        layout.addWidget(
            QLabel(
                "Sugestões futuras: tema claro/escuro, página inicial, backup automático, "
                "limites de uso de IA, provedor/modelo padrão e diagnóstico do Playwright."
            )
        )
        self.layout.addWidget(group)

        self.save_settings_button = QPushButton("Salvar configurações")
        self.layout.addWidget(self.save_settings_button)
        self.save_settings_button.clicked.connect(self._save_settings)

    def refresh_reference_data(self) -> None:
        self._load_settings()

    def _load_settings(self) -> None:
        mode_index = self.startup_mode.findData(self._service.startup_mode())
        self.startup_mode.setCurrentIndex(max(mode_index, 0))
        self.browser_headless.setChecked(self._service.browser_headless())
        self.openai_key.setText(self._service.get_api_key("openai"))
        self.google_key.setText(self._service.get_api_key("google"))
        self._refresh_logins()
        self._refresh_diagnostics()

    def _save_settings(self) -> None:
        try:
            self._service.set_startup_mode(str(self.startup_mode.currentData()))
            self._service.set_browser_headless(self.browser_headless.isChecked())
            self._service.set_api_key("openai", self.openai_key.text())
            self._service.set_api_key("google", self.google_key.text())
        except Exception as exc:
            QMessageBox.critical(self, "Não foi possível salvar", str(exc))
            return
        self._refresh_diagnostics()
        QMessageBox.information(self, "Configurações", "Configurações salvas com segurança.")

    def _test_openai(self) -> None:
        key = self.openai_key.text().strip()
        ok, message = self._service.test_openai_key(key)
        self.api_status.setText(message)
        if ok:
            QMessageBox.information(self, "OpenAI", message)
        else:
            QMessageBox.warning(self, "OpenAI", message)

    def _toggle_secret_visibility(self) -> None:
        fields = (self.openai_key, self.google_key, self.login_password)
        new_mode = (
            QLineEdit.EchoMode.Normal
            if self.openai_key.echoMode() == QLineEdit.EchoMode.Password
            else QLineEdit.EchoMode.Password
        )
        for field in fields:
            field.setEchoMode(new_mode)

    def _refresh_logins(self) -> None:
        logins = self._service.list_logins()
        self.login_table.setRowCount(len(logins))
        for row, login in enumerate(logins):
            values = (login.service, login.url, login.username, login.notes)
            for column, value in enumerate(values):
                self.login_table.setItem(row, column, QTableWidgetItem(value))

    def _load_selected_login(self) -> None:
        row = self.login_table.currentRow()
        if row < 0:
            return
        service_item = self.login_table.item(row, 0)
        if service_item is None:
            return
        service_name = service_item.text()
        match = next(
            (item for item in self._service.list_logins() if item.service == service_name),
            None,
        )
        if match is None:
            return
        self._selected_login_service = match.service
        self.login_service.setText(match.service)
        self.login_url.setText(match.url)
        self.login_username.setText(match.username)
        self.login_password.setText(self._service.login_password(match.service))
        self.login_notes.setPlainText(match.notes)

    def _save_login(self) -> None:
        try:
            previous_service = self._selected_login_service
            credential = LoginCredential(
                service=self.login_service.text(),
                url=self.login_url.text(),
                username=self.login_username.text(),
                notes=self.login_notes.toPlainText(),
            )
            if previous_service and previous_service.casefold() != credential.service.strip().casefold():
                self._service.delete_login(previous_service)
            self._service.save_login(credential, self.login_password.text())
        except Exception as exc:
            QMessageBox.critical(self, "Não foi possível salvar o login", str(exc))
            return
        self._selected_login_service = credential.service.strip()
        self._refresh_logins()
        self._refresh_diagnostics()
        QMessageBox.information(self, "Cofre de Logins", "Login salvo com segurança.")

    def _delete_login(self) -> None:
        service = self._selected_login_service or self.login_service.text().strip()
        if not service:
            return
        answer = QMessageBox.question(
            self,
            "Excluir login",
            f"Excluir o login de {service}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._service.delete_login(service)
        self._clear_login_form()
        self._refresh_logins()
        self._refresh_diagnostics()

    def _clear_login_form(self) -> None:
        self._selected_login_service = ""
        self.login_table.clearSelection()
        self.login_service.clear()
        self.login_url.clear()
        self.login_username.clear()
        self.login_password.clear()
        self.login_notes.clear()

    def _refresh_diagnostics(self) -> None:
        snapshot = self._service.diagnostic_snapshot()
        self.diagnostics.setText(" | ".join(f"{key}: {value}" for key, value in snapshot.items()))
