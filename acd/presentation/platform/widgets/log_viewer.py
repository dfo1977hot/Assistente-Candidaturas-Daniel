"""Log viewer widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)

from acd.application.platform import PlatformUseCases


class LogViewer(QWidget):
    """Widget for viewing system logs."""

    def __init__(self, use_cases: PlatformUseCases, parent=None):
        """Initialize log viewer.

        Args:
            use_cases: Platform use cases
            parent: Parent widget
        """
        super().__init__(parent)
        self.use_cases = use_cases
        self.setup_ui()
        self.refresh()

    def setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout()

        # Filters
        filter_layout = QHBoxLayout()

        filter_layout.addWidget(QComboBox())  # Module filter placeholder
        filter_layout.addWidget(QComboBox())  # Level filter placeholder

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        filter_layout.addWidget(refresh_btn)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Logs table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Timestamp", "Level", "Module", "Operation", "Message", "Duration (ms)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh(self) -> None:
        """Refresh logs."""
        try:
            from acd.infrastructure.repositories.platform import PlatformRepository
            from sqlalchemy import create_engine
            from sqlalchemy.orm import Session

            # Get logs (will be populated by service)
            failed_ops = self.use_cases.get_failed_operations(hours=24)
            self.update_table(failed_ops)
        except Exception as e:
            pass  # Handle gracefully

    def update_table(self, logs: list) -> None:
        """Update logs table.

        Args:
            logs: List of log entries
        """
        self.table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            self.table.setItem(row, 0, QTableWidgetItem(log.get("timestamp", "")))
            self.table.setItem(row, 1, QTableWidgetItem("ERROR"))
            self.table.setItem(row, 2, QTableWidgetItem(log.get("module", "")))
            self.table.setItem(row, 3, QTableWidgetItem(log.get("operation", "")))
            self.table.setItem(row, 4, QTableWidgetItem(log.get("message", "")))
            self.table.setItem(row, 5, QTableWidgetItem(""))
