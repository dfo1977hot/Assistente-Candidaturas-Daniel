from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
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
    QVBoxLayout,
    QWidget,
)

from acd.application.company.create_company import create_company
from acd.application.company.delete_company import delete_company
from acd.application.company.list_company import list_companies
from acd.application.company.update_company import update_company
from acd.infrastructure.repositories.company_repository import CompanyRepository
from acd.presentation.pages.base_page import BasePage


class CompanyPage(BasePage):
    """Página de cadastro e gerenciamento de empresas."""

    def __init__(self) -> None:
        super().__init__("Empresas")

        self.repository = CompanyRepository()
        self.current_company_id: Optional[int] = None

        self.name_input = QLineEdit()
        self.city_input = QLineEdit()
        self.website_input = QLineEdit()
        self.save_button = QPushButton("Salvar")
        self.delete_button = QPushButton("Excluir")
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Empresa", "Cidade", "Website"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.itemSelectionChanged.connect(self._on_row_selected)

        form = QFormLayout()
        form.addRow(QLabel("Nome"), self.name_input)
        form.addRow(QLabel("Cidade"), self.city_input)
        form.addRow(QLabel("Website"), self.website_input)

        actions = QHBoxLayout()
        actions.addWidget(self.save_button)
        actions.addWidget(self.delete_button)
        actions.addStretch()
        self.save_button.clicked.connect(self._save_company)
        self.delete_button.clicked.connect(self._delete_company)

        self.layout.addLayout(form)
        self.layout.addLayout(actions)
        self.layout.addWidget(self.table)

        self._load_companies()

    def _save_company(self) -> None:
        try:
            name = self.name_input.text().strip()
            city = self.city_input.text().strip()
            website = self.website_input.text().strip()

            if self.current_company_id is None:
                create_company(
                    self.repository,
                    name=name,
                    city=city,
                    website=website,
                )
            else:
                update_company(
                    self.repository,
                    self.current_company_id,
                    name=name,
                    city=city,
                    website=website,
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
        company_city = self.table.item(row, 2).text()
        company_website = self.table.item(row, 3).text()

        self.current_company_id = company_id
        self.name_input.setText(company_name)
        self.city_input.setText(company_city)
        self.website_input.setText(company_website)

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

        delete_company(self.repository, self.current_company_id)
        self._clear_form()
        self._load_companies()

    def _clear_form(self) -> None:
        self.current_company_id = None
        self.name_input.clear()
        self.city_input.clear()
        self.website_input.clear()

    def _load_companies(self) -> None:
        companies = list_companies(self.repository)
        self.table.setRowCount(len(companies))
        for row, company in enumerate(companies):
            self.table.setItem(row, 0, QTableWidgetItem(str(company.id)))
            self.table.setItem(row, 1, QTableWidgetItem(company.name))
            self.table.setItem(row, 2, QTableWidgetItem(company.city))
            self.table.setItem(row, 3, QTableWidgetItem(company.website or ""))
        self.table.resizeColumnsToContents()
