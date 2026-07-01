"""Metrics display panel widget."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtGui import QFont

from acd.application.platform import PlatformUseCases


class MetricsPanel(QWidget):
    """Widget to display system metrics."""

    def __init__(self, use_cases: PlatformUseCases, parent=None):
        """Initialize metrics panel.

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

        # Summary section
        summary_layout = QHBoxLayout()
        summary_layout.addWidget(QLabel("System Summary:"))

        self.memory_label = QLabel("Memory: --")
        summary_layout.addWidget(self.memory_label)

        self.cpu_label = QLabel("CPU: --")
        summary_layout.addWidget(self.cpu_label)

        self.disk_label = QLabel("Disk: --")
        summary_layout.addWidget(self.disk_label)

        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Metrics table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Metric", "Value", "Unit", "Module", "Status"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.table)

        self.setLayout(layout)

    def refresh(self) -> None:
        """Refresh metrics display."""
        try:
            summary = self.use_cases.get_metrics_summary()
            self.update_summary(summary)

            metrics = self.use_cases.get_metrics(hours_back=1)
            self.update_metrics_table(metrics)
        except Exception as e:
            self.memory_label.setText(f"Error: {str(e)}")

    def update_summary(self, summary: dict) -> None:
        """Update summary display.

        Args:
            summary: Summary data
        """
        current = summary.get("current", {})
        averages = summary.get("averages", {})

        memory = current.get("memory_mb", 0)
        cpu = current.get("cpu_percent", 0)
        disk = current.get("disk_usage_percent", 0)

        self.memory_label.setText(f"Memory: {memory:.1f}MB")
        self.cpu_label.setText(f"CPU: {cpu:.1f}%")
        self.disk_label.setText(f"Disk: {disk:.1f}%")

    def update_metrics_table(self, metrics: list) -> None:
        """Update metrics table.

        Args:
            metrics: Metrics list
        """
        self.table.setRowCount(len(metrics))

        for row, metric in enumerate(metrics):
            self.table.setItem(row, 0, QTableWidgetItem(metric.get("metric_name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(f"{metric.get('value', 0):.2f}"))
            self.table.setItem(row, 2, QTableWidgetItem(metric.get("unit", "")))
            self.table.setItem(row, 3, QTableWidgetItem(metric.get("module", "")))
            self.table.setItem(row, 4, QTableWidgetItem(metric.get("status", "normal")))
