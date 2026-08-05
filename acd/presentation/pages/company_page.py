from __future__ import annotations

from PySide6.QtWidgets import (
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

from acd.presentation.pages.base_page import BasePage
from acd.services.company_service import CompanyService


class CompanyPage(BasePage):
    """Página de cadastro e gerenciamento de empresas."""

    def __init__(self, service: CompanyService) -> None:
        super().__init__("Empresas")

        self.service = service
        self.current_company_id: int | None = None

        self.name_input = QLineEdit()
        self.segment_input = QLineEdit()
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
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        form = QFormLayout()
        form.addRow(QLabel("Nome"), self.name_input)
        form.addRow(QLabel("Segmento"), self.segment_input)
        form.addRow(QLabel("Cidade"), self.city_input)
        form.addRow(QLabel("Estado"), self.state_input)
        form.addRow(QLabel("Pais"), self.country_input)
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
            return

        confirmation = QMessageBox.question(
            self,
            "Confirmar exclusão",
            "Deseja excluir esta empresa?",
        )
        if confirmation != QMessageBox.Yes:
            return

        self.service.delete_company(self.current_company_id)
        self._clear_form()
        self._load_companies()

    def _clear_form(self) -> None:
        self.current_company_id = None
        self.name_input.clear()
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
