"""Log viewer widget."""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from acd.application.platform import PlatformUseCases

logger = logging.getLogger(__name__)


class LogViewer(QWidget):
    """Widget for viewing system logs."""

    def __init__(
        self,
        use_cases: PlatformUseCases,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize log viewer.

        Args:
            use_cases: Platform use cases.
            parent: Parent widget.
        """
        super().__init__(parent)
        self.use_cases = use_cases
        self.setup_ui()
        self.refresh()

    def setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout()

        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QComboBox())
        filter_layout.addWidget(QComboBox())

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Timestamp",
                "Level",
                "Module",
                "Operation",
                "Message",
                "Duration (ms)",
            ]
        )

        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch,
        )

        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh(self) -> None:
        """Refresh logs."""
        try:
            failed_ops = self.use_cases.get_failed_operations(hours=24)
            self.update_table(failed_ops)

        except Exception:
            logger.exception(
                "Unable to refresh log viewer."
            )

    def update_table(
        self,
        logs: list[dict[str, Any]],
    ) -> None:
        """Update logs table.

        Args:
            logs: List of log entries.
        """
        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            self.table.setItem(
                row,
                0,
                QTableWidgetItem(log.get("timestamp", "")),
            )

            self.table.setItem(
                row,
                1,
                QTableWidgetItem("ERROR"),
            )

            self.table.setItem(
                row,
                2,
                QTableWidgetItem(log.get("module", "")),
            )

            self.table.setItem(
                row,
                3,
                QTableWidgetItem(log.get("operation", "")),
            )

            self.table.setItem(
                row,
                4,
                QTableWidgetItem(log.get("message", "")),
            )

            self.table.setItem(
                row,
                5,
                QTableWidgetItem(""),
            )