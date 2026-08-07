from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
)

from acd.presentation.long_running_task_executor import LongRunningTaskExecutor
from acd.presentation.pages.base_page import BasePage
from acd.presentation.pages.company_lookup_dialog import CompanyLookupDialog
from acd.presentation.pages.company_lookup_worker import CompanyLookupGateway
from acd.services.company_service import CompanyService


class CompanyPage(BasePage):
    """Página de cadastro e gerenciamento de empresas."""

    def __init__(
        self,
        service: CompanyService,
        lookup_service_factory: Callable[[str], CompanyLookupGateway] | None = None,
    ) -> None:
        super().__init__("Empresas")

        self.service = service
        self.lookup_service_factory = lookup_service_factory
        self._lookup_executor = LongRunningTaskExecutor(self)
        self._lookup_executor.succeeded.connect(self._on_lookup_succeeded)
        self._lookup_executor.failed.connect(self._on_lookup_failed)
        self._lookup_executor.finished.connect(self._on_lookup_finished)
        self._settings = QSettings("ACD", "AssistenteCandidaturasDaniel")
        self._lookup_metadata = {}
        self.current_company_id: int | None = None

        self.name_input = QLineEdit()
        self.legal_name_input = QLineEdit()
        self.tax_id_input = QLineEdit()
        self.registration_status_input = QLineEdit()
        self.segment_input = QLineEdit()
        self.address_input = QLineEdit()
        self.postal_code_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.lookup_button = QPushButton("Buscar dados")
        self.lookup_button.clicked.connect(self._lookup_company)
        self.cancel_lookup_button = QPushButton("Cancelar")
        self.cancel_lookup_button.setEnabled(False)
        self.cancel_lookup_button.clicked.connect(self._cancel_lookup)
        self.force_refresh_checkbox = QCheckBox("Atualizar dados, ignorando cache")
        self.lookup_status = QLabel("")
        self.lookup_provider = QComboBox()
        self.lookup_provider.addItem("Híbrida: OpenAI + ReceitaWS", "hybrid")
        self.lookup_provider.addItem("OpenAI com pesquisa web", "openai")
        self.lookup_provider.addItem("Google Places", "google")
        saved_provider = str(self._settings.value("company_lookup/provider", "hybrid"))
        saved_index = self.lookup_provider.findData(saved_provider)
        if saved_index >= 0:
            self.lookup_provider.setCurrentIndex(saved_index)
        self.lookup_provider.currentIndexChanged.connect(self._save_lookup_provider)
        self.city_input = QLineEdit()
        self.state_input = QLineEdit()
        self.country_input = QLineEdit()
        self.company_size_input = QLineEdit()
        self.website_input = QLineEdit()
        self.linkedin_input = QLineEdit()
        self.notes_input = QTextEdit()
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Pesquisar")
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Empresa", "Segmento", "Cidade", "Porte", "Website", "Cadastro"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().hide()
        self.table.setCornerButtonEnabled(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        form = QFormLayout()
        name_row = QHBoxLayout()
        name_row.addWidget(self.name_input)
        name_row.addWidget(self.lookup_button)
        name_row.addWidget(self.cancel_lookup_button)
        form.addRow(QLabel("Nome"), name_row)
        form.addRow(QLabel("Fonte da busca"), self.lookup_provider)
        form.addRow(QLabel("Consulta"), self.force_refresh_checkbox)
        form.addRow(QLabel("Status"), self.lookup_status)
        form.addRow(QLabel("Razão social"), self.legal_name_input)
        form.addRow(QLabel("CNPJ"), self.tax_id_input)
        form.addRow(QLabel("Situação"), self.registration_status_input)
        form.addRow(QLabel("Segmento"), self.segment_input)
        form.addRow(QLabel("Endereço"), self.address_input)
        form.addRow(QLabel("Cidade"), self.city_input)
        form.addRow(QLabel("Estado"), self.state_input)
        form.addRow(QLabel("CEP"), self.postal_code_input)
        form.addRow(QLabel("Pais"), self.country_input)
        form.addRow(QLabel("Telefone"), self.phone_input)
        form.addRow(QLabel("Porte"), self.company_size_input)
        form.addRow(QLabel("Website"), self.website_input)
        form.addRow(QLabel("LinkedIn"), self.linkedin_input)
        form.addRow(QLabel("Observações"), self.notes_input)

        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        self.save_button.clicked.connect(self._save_company)
        self.delete_button.clicked.connect(self._delete_company)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Pesquisar"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        self.search_button.clicked.connect(self._search_companies)

        self.layout.addLayout(form)
        self.layout.addLayout(actions)
        self.layout.addLayout(search_layout)
        self.layout.addWidget(self.table)

        self._load_companies()

    def _lookup_company(self) -> None:
        name = self.name_input.text().strip()
        if len(name) < 2:
            QMessageBox.warning(
                self,
                "Buscar dados",
                "Informe pelo menos dois caracteres do nome da empresa.",
            )
            return
        if self._lookup_executor.is_running:
            return
        if self.lookup_service_factory is None:
            self.lookup_status.setText("Serviço de busca indisponível.")
            QMessageBox.warning(
                self,
                "Buscar dados",
                "O serviço de busca de empresas não está disponível.",
            )
            return

        provider_name = str(self.lookup_provider.currentData())
        force_refresh = self.force_refresh_checkbox.isChecked()
        service_factory = self.lookup_service_factory
        self._set_lookup_running(True)
        self.lookup_status.setText("Buscando dados...")

        def lookup_task() -> object:
            service = service_factory(provider_name)
            return service.search(name, force_refresh=force_refresh)

        self._lookup_executor.execute(lookup_task)

    def _cancel_lookup(self) -> None:
        if self._lookup_executor.cancel():
            self.lookup_status.setText(
                "Cancelamento solicitado. Aguardando a consulta encerrar..."
            )
            self.cancel_lookup_button.setEnabled(False)

    def _on_lookup_succeeded(self, results: object) -> None:
        typed_results = list(results) if isinstance(results, list) else []
        if not typed_results:
            self.lookup_status.setText("Nenhuma empresa encontrada.")
            QMessageBox.information(self, "Buscar dados", "Nenhuma empresa foi encontrada.")
            return
        self.lookup_status.setText(f"{len(typed_results)} resultado(s) encontrado(s).")
        dialog = CompanyLookupDialog(typed_results, self)
        if dialog.exec() != QDialog.Accepted:
            return
        result = dialog.selected_result()
        if result is None:
            return
        populated = any(
            widget.text().strip()
            for widget in (
                self.city_input,
                self.state_input,
                self.website_input,
                self.address_input,
            )
        )
        if populated:
            answer = QMessageBox.question(
                self,
                "Substituir dados",
                "Alguns campos já estão preenchidos. Deseja substituí-los pelos dados selecionados?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if answer != QMessageBox.Yes:
                return
        self._apply_lookup_result(result)

    def _apply_lookup_result(self, result) -> None:
        self.name_input.setText(result.name)
        self.legal_name_input.setText(result.legal_name)
        self.tax_id_input.setText(result.tax_id)
        self.registration_status_input.setText(result.registration_status)
        self.segment_input.setText(result.segment)
        self.address_input.setText(result.address)
        self.city_input.setText(result.city)
        self.state_input.setText(result.state)
        self.postal_code_input.setText(result.postal_code)
        self.country_input.setText(result.country or "Brasil")
        self.phone_input.setText(result.phone)
        self.website_input.setText(result.website)
        self._lookup_metadata = {
            "data_source": result.source,
            "source_reference": result.source_reference,
            "data_retrieved_at": result.retrieved_at,
        }
        QMessageBox.information(
            self,
            "Dados preenchidos",
            f"Fonte: {result.source or 'não informada'}\n"
            f"Confiança estimada: {result.confidence:.0%}\n\n"
            "Revise todos os campos antes de salvar.",
        )

    def _on_lookup_failed(self, error: object) -> None:
        self.lookup_status.setText("Falha na consulta.")
        QMessageBox.warning(self, "Buscar dados", str(error))

    def _on_lookup_finished(self) -> None:
        self._set_lookup_running(False)
        if self.lookup_status.text().startswith("Cancelamento"):
            self.lookup_status.setText("Consulta cancelada.")

    def _set_lookup_running(self, running: bool) -> None:
        self.lookup_button.setEnabled(not running)
        self.cancel_lookup_button.setEnabled(running)
        self.lookup_provider.setEnabled(not running)
        self.force_refresh_checkbox.setEnabled(not running)

    def _save_lookup_provider(self) -> None:
        self._settings.setValue("company_lookup/provider", str(self.lookup_provider.currentData()))

    def _save_company(self) -> None:
        try:
            name = self.name_input.text().strip()
            segment = self.segment_input.text().strip()
            city = self.city_input.text().strip()
            state = self.state_input.text().strip()
            country = self.country_input.text().strip()
            company_size = self.company_size_input.text().strip()
            website = self.website_input.text().strip()
            linkedin_url = self.linkedin_input.text().strip()

            notes = self.notes_input.toPlainText().strip()

            if self.current_company_id is None:
                self.service.create_company(
                    name=name,
                    segment=segment,
                    city=city,
                    state=state,
                    country=country,
                    company_size=company_size,
                    website=website,
                    linkedin_url=linkedin_url,
                    notes=notes,
                    legal_name=self.legal_name_input.text(),
                    tax_id=self.tax_id_input.text(),
                    registration_status=self.registration_status_input.text(),
                    address=self.address_input.text(),
                    postal_code=self.postal_code_input.text(),
                    phone=self.phone_input.text(),
                    data_source=self._lookup_metadata.get("data_source", ""),
                    source_reference=self._lookup_metadata.get("source_reference", ""),
                    data_retrieved_at=self._lookup_metadata.get("data_retrieved_at"),
                )
            else:
                self.service.update_company(
                    self.current_company_id,
                    name=name,
                    segment=segment,
                    city=city,
                    state=state,
                    country=country,
                    company_size=company_size,
                    website=website,
                    linkedin_url=linkedin_url,
                    notes=notes,
                    legal_name=self.legal_name_input.text(),
                    tax_id=self.tax_id_input.text(),
                    registration_status=self.registration_status_input.text(),
                    address=self.address_input.text(),
                    postal_code=self.postal_code_input.text(),
                    phone=self.phone_input.text(),
                    data_source=self._lookup_metadata.get("data_source", ""),
                    source_reference=self._lookup_metadata.get("source_reference", ""),
                    data_retrieved_at=self._lookup_metadata.get("data_retrieved_at"),
                )

            self._clear_form()
            self._load_companies()
        except ValueError as exc:
            QMessageBox.warning(self, "Dados inválidos", str(exc))
        except Exception as exc:  # pragma: no cover - defensive UI handling
            QMessageBox.critical(self, "Erro", str(exc))

    def _on_row_selected(self) -> None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        company_id = int(self.table.item(row, 0).text())
        company_name = self.table.item(row, 1).text()
        company_segment = self.table.item(row, 2).text()
        company_city = self.table.item(row, 3).text()
        company_size = self.table.item(row, 4).text()
        company_website = self.table.item(row, 5).text()

        company = self.service.repository.get_by_id(company_id)

        self.current_company_id = company_id
        self.legal_name_input.setText(company.legal_name if company else "")
        self.tax_id_input.setText(company.tax_id if company else "")
        self.registration_status_input.setText(company.registration_status if company else "")
        self.address_input.setText(company.address if company else "")
        self.postal_code_input.setText(company.postal_code if company else "")
        self.phone_input.setText(company.phone if company else "")
        self._lookup_metadata = {"data_source": company.data_source if company else "", "source_reference": company.source_reference if company else "", "data_retrieved_at": company.data_retrieved_at if company else None}
        self.name_input.setText(company_name)
        self.segment_input.setText(company_segment)
        self.city_input.setText(company_city)
        self.company_size_input.setText(company_size)
        self.website_input.setText(company_website)
        self.state_input.setText(company.state if company else "")
        self.country_input.setText(company.country if company else "")
        self.linkedin_input.setText(company.linkedin_url if company else "")
        self.notes_input.setPlainText(company.notes if company else "")

    def _delete_company(self) -> None:
        if self.current_company_id is None:
            QMessageBox.information(self, "Empresa", "Selecione uma empresa para excluir.")
            return

        confirmation = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta empresa?",
        )
        if confirmation != QMessageBox.Yes:
            return

        try:
            deleted = self.service.delete_company(self.current_company_id)
            if not deleted:
                QMessageBox.warning(self, "Empresa", "A empresa não pôde ser excluída.")
                return
            self._clear_form()
            self._load_companies()
        except Exception as exc:
            if not _is_integrity_error(exc):
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    f"Ocorreu um erro ao excluir a empresa:\n{exc}",
                )
                return
            cascade_confirmation = QMessageBox.question(
                self,
                "Registros vinculados",
                "Esta empresa possui vagas, candidaturas e demais registros vinculados.\n\n"
                "Deseja excluir também todos os registros vinculados? "
                "Esta operação não poderá ser desfeita.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if cascade_confirmation != QMessageBox.Yes:
                return
            try:
                deleted = self.service.delete_company(
                    self.current_company_id,
                    delete_linked=True,
                )
                if not deleted:
                    QMessageBox.warning(
                        self,
                        "Empresa",
                        "O registro não pôde ser excluído.",
                    )
                    return
                self._clear_form()
                self._load_companies()
            except Exception:
                QMessageBox.critical(
                    self,
                    "Não foi possível excluir",
                    "Não foi possível excluir o registro e seus vínculos.",
                )


    def _clear_form(self) -> None:
        self.current_company_id = None
        self.name_input.clear()
        self.legal_name_input.clear()
        self.tax_id_input.clear()
        self.registration_status_input.clear()
        self.address_input.clear()
        self.postal_code_input.clear()
        self.phone_input.clear()
        self._lookup_metadata = {}
        self.segment_input.clear()
        self.city_input.clear()
        self.state_input.clear()
        self.country_input.clear()
        self.company_size_input.clear()
        self.website_input.clear()
        self.linkedin_input.clear()
        self.notes_input.clear()

    def _load_companies(self) -> None:
        companies = self.service.list_companies()
        self.table.setRowCount(len(companies))
        for row, company in enumerate(companies):
            self.table.setItem(row, 0, QTableWidgetItem(str(company.id)))
            self.table.setItem(row, 1, QTableWidgetItem(company.name))
            self.table.setItem(row, 2, QTableWidgetItem(company.segment or ""))
            self.table.setItem(row, 3, QTableWidgetItem(company.city))
            self.table.setItem(row, 4, QTableWidgetItem(company.company_size or ""))
            self.table.setItem(row, 5, QTableWidgetItem(company.website or ""))
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(
                    company.created_at.strftime("%d/%m/%Y") if company.created_at else ""
                ),
            )
        self.table.resizeColumnsToContents()

    def _search_companies(self) -> None:
        query = self.search_input.text().strip()
        companies = self.service.search_companies(query) if query else self.service.list_companies()
        self.table.setRowCount(len(companies))
        for row, company in enumerate(companies):
            self.table.setItem(row, 0, QTableWidgetItem(str(company.id)))
            self.table.setItem(row, 1, QTableWidgetItem(company.name))
            self.table.setItem(row, 2, QTableWidgetItem(company.segment or ""))
            self.table.setItem(row, 3, QTableWidgetItem(company.city))
            self.table.setItem(row, 4, QTableWidgetItem(company.company_size or ""))
            self.table.setItem(row, 5, QTableWidgetItem(company.website or ""))
            self.table.setItem(
                row,
                6,
                QTableWidgetItem(
                    company.created_at.strftime("%d/%m/%Y") if company.created_at else ""
                ),
            )
        self.table.resizeColumnsToContents()


def _is_integrity_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if current.__class__.__name__ == "IntegrityError":
            return True
        current = current.__cause__ or current.__context__
    return False
