"""Health status card widget."""

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from acd.application.platform import PlatformUseCases


class HealthCard(QWidget):
    """Widget to display system health status."""

    def __init__(self, use_cases: PlatformUseCases, parent=None):
        """Initialize health card.

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

        # Status header
        header_layout = QHBoxLayout()
        self.status_label = QLabel("Status: Loading...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.status_label)

        self.run_button = QPushButton("Run Health Check")
        self.run_button.clicked.connect(self.run_checks)
        header_layout.addWidget(self.run_button)

        layout.addLayout(header_layout)

        # Results table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Check Type", "Status", "Message", "Response Time (ms)"]
        )
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh(self) -> None:
        """Refresh health status."""
        try:
            health = self.use_cases.get_system_health()
            self.update_display(health)
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def run_checks(self) -> None:
        """Run all health checks."""
        try:
            results = self.use_cases.run_health_check()
            self.table.setRowCount(len(results))

            for row, (check_name, result) in enumerate(results.items()):
                self.table.setItem(row, 0, QTableWidgetItem(check_name))
                self.table.setItem(row, 1, QTableWidgetItem(result.get("status", "Unknown")))
                self.table.setItem(row, 2, QTableWidgetItem(result.get("message", "")))
                response_time = result.get("response_time_ms", 0)
                self.table.setItem(row, 3, QTableWidgetItem(f"{response_time:.2f}"))
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")

    def update_display(self, health: dict) -> None:
        """Update display with health data.

        Args:
            health: Health data
        """
        overall_status = health.get("overall_status", "Unknown")
        self.status_label.setText(f"Status: {overall_status.upper()}")

        # Set color based on status
        if overall_status == "healthy":
            self.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif overall_status == "degraded":
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: red; font-weight: bold;")

        # Display checks
        checks = health.get("checks", {})
        self.table.setRowCount(len(checks))

        for row, (check_name, result) in enumerate(checks.items()):
            self.table.setItem(row, 0, QTableWidgetItem(check_name))

            status_item = QTableWidgetItem(result.get("status", "Unknown"))
            status = result.get("status", "Unknown")
            if status == "healthy":
                status_item.setForeground(QColor("green"))
            elif status == "degraded":
                status_item.setForeground(QColor("orange"))
            else:
                status_item.setForeground(QColor("red"))
            self.table.setItem(row, 1, status_item)

            self.table.setItem(row, 2, QTableWidgetItem(result.get("message", "")))
            response_time = result.get("response_time_ms", 0)
            self.table.setItem(row, 3, QTableWidgetItem(f"{response_time:.2f}"))
