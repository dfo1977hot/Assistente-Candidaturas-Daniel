from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from acd.services.company_lookup_service import CompanyLookupResult


class CompanyLookupDialog(QDialog):
    def __init__(self, results: list[CompanyLookupResult], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Selecionar empresa")
        self.resize(900, 420)
        self._results = results
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Selecione a empresa correta. Nenhum dado será salvo automaticamente."))
        self.table = QTableWidget(len(results), 7)
        self.table.setHorizontalHeaderLabels(
            ["Empresa", "Cidade", "UF", "Endereço", "Site", "Fonte", "Confiança"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        for row, result in enumerate(results):
            for column, value in enumerate(
                (
                    result.name,
                    result.city,
                    result.state,
                    result.address,
                    result.website,
                    result.source,
                    f"{result.confidence:.0%}",
                )
            ):
                item = QTableWidgetItem(value)
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, column, item)
        self.table.resizeColumnsToContents()
        self.table.doubleClicked.connect(self.accept)
        layout.addWidget(self.table)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        if results:
            self.table.selectRow(0)

    def selected_result(self) -> CompanyLookupResult | None:
        rows = self.table.selectionModel().selectedRows()
        return self._results[rows[0].row()] if rows else None
