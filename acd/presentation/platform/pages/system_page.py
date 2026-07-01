"""System status page for platform monitoring."""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QTabWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from acd.application.platform import PlatformUseCases
from acd.presentation.platform.widgets.health_card import HealthCard
from acd.presentation.platform.widgets.metrics_panel import MetricsPanel
from acd.presentation.platform.widgets.backup_panel import BackupPanel
from acd.presentation.platform.widgets.settings_panel import SettingsPanel
from acd.presentation.platform.widgets.log_viewer import LogViewer


class SystemPage(QWidget):
    """System status and monitoring page."""

    def __init__(self, use_cases: PlatformUseCases, parent=None):
        """Initialize system page.

        Args:
            use_cases: Platform use cases
            parent: Parent widget
        """
        super().__init__(parent)
        self.use_cases = use_cases
        self.setup_ui()
        self.setup_timers()

    def setup_ui(self) -> None:
        """Setup UI."""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()
        title = QLabel("System Status")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Tabs
        self.tabs = QTabWidget()

        # Health check tab
        self.health_card = HealthCard(self.use_cases)
        self.tabs.addTab(self.health_card, "Health Check")

        # Metrics tab
        self.metrics_panel = MetricsPanel(self.use_cases)
        self.tabs.addTab(self.metrics_panel, "Metrics")

        # Backup tab
        self.backup_panel = BackupPanel(self.use_cases)
        self.tabs.addTab(self.backup_panel, "Backups")

        # Settings tab
        self.settings_panel = SettingsPanel(self.use_cases)
        self.tabs.addTab(self.settings_panel, "Settings")

        # Logs tab
        self.log_viewer = LogViewer(self.use_cases)
        self.tabs.addTab(self.log_viewer, "Logs")

        layout.addWidget(self.tabs)

        self.setLayout(layout)

    def setup_timers(self) -> None:
        """Setup auto-refresh timers."""
        # Health check timer - every 30 seconds
        self.health_timer = QTimer()
        self.health_timer.timeout.connect(self.health_card.refresh)
        self.health_timer.start(30000)

        # Metrics timer - every 60 seconds
        self.metrics_timer = QTimer()
        self.metrics_timer.timeout.connect(self.metrics_panel.refresh)
        self.metrics_timer.start(60000)

    def refresh(self) -> None:
        """Refresh all panels."""
        self.health_card.refresh()
        self.metrics_panel.refresh()
        self.backup_panel.refresh()
        self.log_viewer.refresh()

    def closeEvent(self, event) -> None:
        """Handle close event."""
        self.health_timer.stop()
        self.metrics_timer.stop()
        super().closeEvent(event)
