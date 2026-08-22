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
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from acd.presentation.pages.base_page import BasePage
from acd.services.settings_service import LoginCredential, SettingsService


class SettingsPage(BasePage):
    """Centraliza preferências não sensíveis e segredos protegidos pelo keyring."""

    def __init__(
        self,
        service: SettingsService,
    ) -> None:
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
        self.startup_mode.addItem(
            "Maximizado",
            "maximized",
        )
        self.startup_mode.addItem(
            "Minimizado",
            "minimized",
        )

        layout.addRow(
            "Abrir aplicativo",
            self.startup_mode,
        )

        self.layout.addWidget(group)

    def _build_browser_section(self) -> None:
        group = QGroupBox(
            "Navegador e automações"
        )
        layout = QVBoxLayout(group)

        self.browser_headless = QCheckBox(
            "Executar importação e detecção de links "
            "do LinkedIn em segundo plano"
        )

        self.browser_headless.setToolTip(
            "Quando marcado, o Chrome/Chromium do "
            "Playwright roda sem janela visível. "
            "A candidatura manual continua abrindo "
            "o navegador normalmente."
        )

        layout.addWidget(
            self.browser_headless
        )

        self.layout.addWidget(group)

    def _build_api_section(self) -> None:
        group = QGroupBox(
            "APIs e Inteligência Artificial"
        )
        grid = QGridLayout(group)

        self.ai_provider_order = QComboBox()
        self.ai_provider_order.addItem(
            "Ollama → Gemini → OpenAI",
            ("ollama", "gemini", "openai"),
        )
        self.ai_provider_order.addItem(
            "Gemini → Ollama → OpenAI",
            ("gemini", "ollama", "openai"),
        )
        self.ai_provider_order.addItem(
            "OpenAI → Ollama → Gemini",
            ("openai", "ollama", "gemini"),
        )

        self.ollama_url = QLineEdit()
        self.ollama_url.setPlaceholderText(
            "http://localhost:11434"
        )
        self.ollama_model = QLineEdit()
        self.ollama_model.setPlaceholderText(
            "qwen3:8b"
        )
        self.test_ollama_button = QPushButton(
            "Testar Ollama"
        )

        self.gemini_key = QLineEdit()
        self.gemini_key.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.gemini_key.setPlaceholderText(
            "Chave da Gemini API"
        )
        self.gemini_model = QLineEdit()
        self.gemini_model.setPlaceholderText(
            "gemini-3.6-flash"
        )
        self.test_gemini_button = QPushButton(
            "Testar Gemini"
        )

        self.openai_key = QLineEdit()
        self.openai_key.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.openai_key.setPlaceholderText(
            "sk-..."
        )
        self.openai_model = QLineEdit()
        self.openai_model.setPlaceholderText(
            "gpt-5-mini"
        )
        self.test_openai_button = QPushButton(
            "Testar OpenAI"
        )

        self.google_key = QLineEdit()
        self.google_key.setEchoMode(
            QLineEdit.EchoMode.Password
        )
        self.google_key.setPlaceholderText(
            "Chave da API Google Places"
        )

        self.toggle_secrets_button = QPushButton(
            "Mostrar/Ocultar chaves"
        )

        self.api_status = QLabel(
            "Não testada"
        )
        self.api_status.setWordWrap(True)

        grid.addWidget(
            QLabel("Ordem dos provedores"),
            0,
            0,
        )
        grid.addWidget(
            self.ai_provider_order,
            0,
            1,
            1,
            3,
        )

        grid.addWidget(
            QLabel("Ollama URL"),
            1,
            0,
        )
        grid.addWidget(
            self.ollama_url,
            1,
            1,
        )
        grid.addWidget(
            QLabel("Modelo Ollama"),
            1,
            2,
        )
        grid.addWidget(
            self.ollama_model,
            1,
            3,
        )
        grid.addWidget(
            self.test_ollama_button,
            1,
            4,
        )

        grid.addWidget(
            QLabel("Gemini API Key"),
            2,
            0,
        )
        grid.addWidget(
            self.gemini_key,
            2,
            1,
        )
        grid.addWidget(
            QLabel("Modelo Gemini"),
            2,
            2,
        )
        grid.addWidget(
            self.gemini_model,
            2,
            3,
        )
        grid.addWidget(
            self.test_gemini_button,
            2,
            4,
        )

        grid.addWidget(
            QLabel("OpenAI API Key"),
            3,
            0,
        )
        grid.addWidget(
            self.openai_key,
            3,
            1,
        )
        grid.addWidget(
            QLabel("Modelo OpenAI"),
            3,
            2,
        )
        grid.addWidget(
            self.openai_model,
            3,
            3,
        )
        grid.addWidget(
            self.test_openai_button,
            3,
            4,
        )

        grid.addWidget(
            QLabel("Google Places API Key"),
            4,
            0,
        )
        grid.addWidget(
            self.google_key,
            4,
            1,
            1,
            3,
        )

        grid.addWidget(
            self.toggle_secrets_button,
            5,
            1,
        )

        grid.addWidget(
            self.api_status,
            6,
            0,
            1,
            5,
        )

        self.toggle_secrets_button.clicked.connect(
            self._toggle_secret_visibility
        )
        self.test_ollama_button.clicked.connect(
            self._test_ollama
        )
        self.test_gemini_button.clicked.connect(
            self._test_gemini
        )
        self.test_openai_button.clicked.connect(
            self._test_openai
        )

        self.layout.addWidget(group)

    def _build_login_section(self) -> None:
        group = QGroupBox(
            "Cofre de Logins"
        )
        outer = QVBoxLayout(group)

        explanation = QLabel(
            "Cadastre credenciais por serviço. Para Terra IMAP, informe o "
            "servidor, porta, segurança e pasta. A senha permanece protegida "
            "no cofre do sistema operacional."
        )
        explanation.setWordWrap(True)
        outer.addWidget(explanation)

        self.login_table = QTableWidget(
            0,
            4,
        )

        self.login_table.setHorizontalHeaderLabels(
            [
                "Serviço",
                "URL",
                "Usuário/E-mail",
                "Observações",
            ]
        )

        self.login_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )

        self.login_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )

        self.login_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )

        self.login_table.setMaximumHeight(
            180
        )

        self.login_table.itemSelectionChanged.connect(
            self._load_selected_login
        )

        outer.addWidget(
            self.login_table
        )

        columns = QHBoxLayout()

        left = QFormLayout()
        middle = QFormLayout()
        right = QFormLayout()

        self.login_service = QComboBox()
        self.login_service.setEditable(True)

        self._populate_login_providers()

        self.login_service.setToolTip(
            "Selecione um provedor conhecido ou digite "
            "outro serviço. Para a Gupy, use apenas Gupy."
        )

        if (
            self.login_service.lineEdit()
            is not None
        ):
            self.login_service.lineEdit().setPlaceholderText(
                "Selecione ou informe o serviço"
            )

        self.login_url = QLineEdit()
        self.login_url.setPlaceholderText(
            "Opcional — não necessário para a Gupy"
        )
        self.login_url.setToolTip(
            "A URL é opcional. Provedores reconhecidos "
            "são identificados automaticamente durante "
            "a candidatura."
        )

        self.login_username = QLineEdit()
        self.login_username.setPlaceholderText(
            "E-mail ou usuário"
        )

        self.login_password = QLineEdit()
        self.login_password.setEchoMode(
            QLineEdit.EchoMode.Password
        )

        self.login_server = QLineEdit()
        self.login_server.setPlaceholderText("Servidor IMAP")

        self.login_port = QSpinBox()
        self.login_port.setRange(1, 65535)
        self.login_port.setValue(993)

        self.login_security = QComboBox()
        self.login_security.addItems(
            ["SSL/TLS", "STARTTLS", "Nenhuma"]
        )

        self.login_folder = QLineEdit()
        self.login_folder.setPlaceholderText("INBOX")

        self.login_timeout = QSpinBox()
        self.login_timeout.setRange(5, 900)
        self.login_timeout.setValue(60)
        self.login_timeout.setSuffix(" s")

        self.login_notes = QTextEdit()
        self.login_notes.setMaximumHeight(
            70
        )

        left.addRow(
            "Serviço",
            self.login_service,
        )

        left.addRow(
            "URL (opcional)",
            self.login_url,
        )

        middle.addRow(
            "Usuário/E-mail",
            self.login_username,
        )

        middle.addRow(
            "Senha",
            self.login_password,
        )

        middle.addRow(
            "Servidor IMAP",
            self.login_server,
        )

        middle.addRow(
            "Porta IMAP",
            self.login_port,
        )

        right.addRow(
            "Segurança IMAP",
            self.login_security,
        )

        right.addRow(
            "Pasta IMAP",
            self.login_folder,
        )

        right.addRow(
            "Timeout",
            self.login_timeout,
        )

        right.addRow(
            "Observações",
            self.login_notes,
        )

        columns.addLayout(
            left,
            1,
        )

        columns.addLayout(
            middle,
            1,
        )

        columns.addLayout(
            right,
            1,
        )

        outer.addLayout(columns)

        actions = QGridLayout()

        self.save_login_button = QPushButton(
            "Salvar login"
        )

        self.new_login_button = QPushButton(
            "Novo/Limpar"
        )

        self.delete_login_button = QPushButton(
            "Excluir login"
        )

        self.test_imap_button = QPushButton(
            "Testar IMAP"
        )

        actions.addWidget(
            self.save_login_button,
            0,
            0,
        )

        actions.addWidget(
            self.new_login_button,
            0,
            1,
        )

        actions.addWidget(
            self.delete_login_button,
            0,
            2,
        )

        actions.addWidget(
            self.test_imap_button,
            0,
            3,
        )

        outer.addLayout(actions)

        self.save_login_button.clicked.connect(
            self._save_login
        )

        self.new_login_button.clicked.connect(
            self._clear_login_form
        )

        self.delete_login_button.clicked.connect(
            self._delete_login
        )

        self.test_imap_button.clicked.connect(
            self._test_imap_login
        )

        self.login_service.currentTextChanged.connect(
            self._update_login_fields
        )

        self.layout.addWidget(group)
        self._update_login_fields()

    def _populate_login_providers(
        self,
    ) -> None:
        """Populate canonical providers without removing custom-login support."""
        self.login_service.clear()

        registry = getattr(
            self._service,
            "login_provider_registry",
            None,
        )

        if registry is None:
            return

        providers = registry.list_providers()

        for provider in providers:
            self.login_service.addItem(
                provider.display_name,
                provider.provider_id,
            )

        self.login_service.setCurrentIndex(
            -1
        )

    def _build_diagnostics_section(
        self,
    ) -> None:
        group = QGroupBox(
            "Diagnóstico e sugestões"
        )
        layout = QVBoxLayout(group)

        self.diagnostics = QLabel()

        self.diagnostics.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.diagnostics.setWordWrap(True)

        layout.addWidget(
            self.diagnostics
        )

        layout.addWidget(
            QLabel(
                "Sugestões futuras: tema claro/escuro, "
                "página inicial, backup automático, "
                "limites de uso de IA, provedor/modelo "
                "padrão e diagnóstico do Playwright."
            )
        )

        self.layout.addWidget(group)

        self.save_settings_button = QPushButton(
            "Salvar configurações"
        )

        self.layout.addWidget(
            self.save_settings_button
        )

        self.save_settings_button.clicked.connect(
            self._save_settings
        )

    def refresh_reference_data(
        self,
    ) -> None:
        self._load_settings()

    def _load_settings(
        self,
    ) -> None:
        mode_index = self.startup_mode.findData(
            self._service.startup_mode()
        )

        self.startup_mode.setCurrentIndex(
            max(
                mode_index,
                0,
            )
        )

        self.browser_headless.setChecked(
            self._service.browser_headless()
        )

        provider_order = self._service.ai_provider_order()
        for index in range(self.ai_provider_order.count()):
            if tuple(self.ai_provider_order.itemData(index)) == provider_order:
                self.ai_provider_order.setCurrentIndex(index)
                break

        self.ollama_url.setText(
            self._service.ollama_base_url()
        )
        self.ollama_model.setText(
            self._service.ai_model("ollama")
        )

        self.gemini_key.setText(
            self._service.get_api_key(
                "gemini"
            )
        )
        self.gemini_model.setText(
            self._service.ai_model("gemini")
        )

        self.openai_key.setText(
            self._service.get_api_key(
                "openai"
            )
        )
        self.openai_model.setText(
            self._service.ai_model("openai")
        )

        self.google_key.setText(
            self._service.get_api_key(
                "google"
            )
        )

        self._refresh_logins()
        self._refresh_diagnostics()

    def _save_settings(
        self,
    ) -> None:
        try:
            self._service.set_startup_mode(
                str(
                    self.startup_mode.currentData()
                )
            )

            self._service.set_browser_headless(
                self.browser_headless.isChecked()
            )

            self._service.set_ai_provider_order(
                list(
                    self.ai_provider_order.currentData()
                )
            )
            self._service.set_ollama_base_url(
                self.ollama_url.text()
            )
            self._service.set_ai_model(
                "ollama",
                self.ollama_model.text(),
            )

            self._service.set_api_key(
                "gemini",
                self.gemini_key.text(),
            )
            self._service.set_ai_model(
                "gemini",
                self.gemini_model.text(),
            )

            self._service.set_api_key(
                "openai",
                self.openai_key.text(),
            )
            self._service.set_ai_model(
                "openai",
                self.openai_model.text(),
            )

            self._service.set_api_key(
                "google",
                self.google_key.text(),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Não foi possível salvar",
                str(exc),
            )
            return

        self._refresh_diagnostics()

        QMessageBox.information(
            self,
            "Configurações",
            "Configurações salvas com segurança.",
        )

    def _test_ollama(
        self,
    ) -> None:
        ok, message = self._service.test_ollama(
            self.ollama_url.text()
        )
        self.api_status.setText(message)

        if ok:
            QMessageBox.information(
                self,
                "Ollama",
                message,
            )
        else:
            QMessageBox.warning(
                self,
                "Ollama",
                message,
            )

    def _test_gemini(
        self,
    ) -> None:
        ok, message = self._service.test_gemini_key(
            self.gemini_key.text()
        )
        self.api_status.setText(message)

        if ok:
            QMessageBox.information(
                self,
                "Gemini",
                message,
            )
        else:
            QMessageBox.warning(
                self,
                "Gemini",
                message,
            )

    def _test_openai(
        self,
    ) -> None:
        key = self.openai_key.text().strip()

        ok, message = (
            self._service.test_openai_key(
                key
            )
        )

        self.api_status.setText(
            message
        )

        if ok:
            QMessageBox.information(
                self,
                "OpenAI",
                message,
            )
        else:
            QMessageBox.warning(
                self,
                "OpenAI",
                message,
            )

    def _toggle_secret_visibility(
        self,
    ) -> None:
        fields = (
            self.gemini_key,
            self.openai_key,
            self.google_key,
            self.login_password,
        )

        new_mode = (
            QLineEdit.EchoMode.Normal
            if self.openai_key.echoMode()
            == QLineEdit.EchoMode.Password
            else QLineEdit.EchoMode.Password
        )

        for field in fields:
            field.setEchoMode(
                new_mode
            )

    def _refresh_logins(
        self,
    ) -> None:
        logins = self._service.list_logins()

        self.login_table.setRowCount(
            len(logins)
        )

        for row, login in enumerate(
            logins
        ):
            values = (
                login.service,
                login.url,
                login.username,
                login.notes,
            )

            for column, value in enumerate(
                values
            ):
                self.login_table.setItem(
                    row,
                    column,
                    QTableWidgetItem(
                        value
                    ),
                )

    def _load_selected_login(
        self,
    ) -> None:
        row = self.login_table.currentRow()

        if row < 0:
            return

        service_item = (
            self.login_table.item(
                row,
                0,
            )
        )

        if service_item is None:
            return

        service_name = (
            service_item.text()
        )

        match = next(
            (
                item
                for item in self._service.list_logins()
                if item.service
                == service_name
            ),
            None,
        )

        if match is None:
            return

        self._selected_login_service = (
            match.service
        )

        self._set_login_service_text(
            match.service
        )

        self.login_url.setText(
            match.url
        )

        self.login_username.setText(
            match.username
        )

        self.login_password.setText(
            self._service.login_password(
                match.service
            )
        )

        self.login_server.setText(match.server)
        self.login_port.setValue(match.port or 993)
        security = match.security or "SSL/TLS"
        security_index = self.login_security.findText(
            security,
            Qt.MatchFlag.MatchFixedString,
        )
        self.login_security.setCurrentIndex(max(security_index, 0))
        self.login_folder.setText(match.folder)
        self.login_timeout.setValue(match.timeout_seconds or 60)

        self.login_notes.setPlainText(
            match.notes
        )
        self._update_login_fields()

    def _set_login_service_text(
        self,
        service: str,
    ) -> None:
        """Select a known provider or keep a custom service name."""
        target = service.strip()

        matching_index = (
            self.login_service.findText(
                target,
                Qt.MatchFlag.MatchFixedString,
            )
        )

        if matching_index >= 0:
            self.login_service.setCurrentIndex(
                matching_index
            )
            return

        self.login_service.setEditText(
            target
        )

    def _update_login_fields(self) -> None:
        is_imap = (
            self.login_service.currentText().strip().casefold()
            in {"terra imap", "terra_imap"}
        )
        for field in (
            self.login_server,
            self.login_port,
            self.login_security,
            self.login_folder,
            self.login_timeout,
            self.test_imap_button,
        ):
            field.setEnabled(is_imap)
        if is_imap:
            if not self.login_username.text().strip():
                self.login_username.setText("dfo1977@terra.com.br")
            current_folder = self.login_folder.text().strip()
            if not current_folder or current_folder.casefold() == "gupy":
                self.login_folder.setText("INBOX")
            if not self.login_server.text().strip():
                self.login_server.setText("imap.terra.com.br")
            if self.login_port.value() <= 0:
                self.login_port.setValue(993)
            if not self.login_security.currentText().strip():
                self.login_security.setCurrentText("SSL/TLS")
        else:
            self.login_server.clear()
            self.login_port.setValue(993)
            self.login_security.setCurrentText("SSL/TLS")
            self.login_folder.clear()
            self.login_timeout.setValue(60)

    def _test_imap_login(self) -> None:
        credential = LoginCredential(
            service=self.login_service.currentText(),
            url=self.login_url.text(),
            username=self.login_username.text(),
            notes=self.login_notes.toPlainText(),
            server=self.login_server.text(),
            port=self.login_port.value(),
            security=self.login_security.currentText(),
            folder=self.login_folder.text(),
            timeout_seconds=self.login_timeout.value(),
        )
        ok, message = self._service.test_imap_login(
            credential,
            self.login_password.text(),
        )

        if ok:
            QMessageBox.information(
                self,
                "Teste IMAP",
                message,
            )
        else:
            QMessageBox.warning(
                self,
                "Teste IMAP",
                message,
            )

    def _save_login(
        self,
    ) -> None:
        try:
            previous_service = (
                self._selected_login_service
            )

            credential = LoginCredential(
                service=(
                    self.login_service.currentText()
                ),
                url=self.login_url.text(),
                username=(
                    self.login_username.text()
                ),
                notes=(
                    self.login_notes.toPlainText()
                ),
                server=self.login_server.text(),
                port=self.login_port.value(),
                security=self.login_security.currentText(),
                folder=self.login_folder.text(),
                timeout_seconds=self.login_timeout.value(),
            )

            if (
                previous_service
                and previous_service.casefold()
                != credential.service.strip().casefold()
            ):
                self._service.delete_login(
                    previous_service
                )

            self._service.save_login(
                credential,
                self.login_password.text(),
            )

        except Exception as exc:
            QMessageBox.critical(
                self,
                "Não foi possível salvar o login",
                str(exc),
            )
            return

        saved = self._service.get_login(
            credential.service
        )

        self._selected_login_service = (
            saved.service
            if saved is not None
            else credential.service.strip()
        )

        if saved is not None:
            self._set_login_service_text(
                saved.service
            )

        self._refresh_logins()
        self._refresh_diagnostics()

        QMessageBox.information(
            self,
            "Cofre de Logins",
            "Login salvo com segurança.",
        )

    def _delete_login(
        self,
    ) -> None:
        service = (
            self._selected_login_service
            or self.login_service.currentText().strip()
        )

        if not service:
            return

        answer = QMessageBox.question(
            self,
            "Excluir login",
            f"Excluir o login de {service}?",
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            return

        self._service.delete_login(
            service
        )

        self._clear_login_form()
        self._refresh_logins()
        self._refresh_diagnostics()

    def _clear_login_form(
        self,
    ) -> None:
        self._selected_login_service = ""

        self.login_table.clearSelection()

        self.login_service.setCurrentIndex(
            -1
        )

        if (
            self.login_service.lineEdit()
            is not None
        ):
            self.login_service.lineEdit().clear()

        self.login_url.clear()
        self.login_username.clear()
        self.login_password.clear()
        self.login_server.clear()
        self.login_port.setValue(993)
        self.login_security.setCurrentText("SSL/TLS")
        self.login_folder.clear()
        self.login_timeout.setValue(60)
        self.login_notes.clear()

    def _refresh_diagnostics(
        self,
    ) -> None:
        snapshot = (
            self._service.diagnostic_snapshot()
        )

        self.diagnostics.setText(
            " | ".join(
                f"{key}: {value}"
                for key, value
                in snapshot.items()
            )
        )
