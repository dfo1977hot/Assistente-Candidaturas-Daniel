"""Platform presentation widgets."""

from acd.presentation.platform.widgets.health_card import HealthCard
from acd.presentation.platform.widgets.metrics_panel import MetricsPanel
from acd.presentation.platform.widgets.backup_panel import BackupPanel
from acd.presentation.platform.widgets.settings_panel import SettingsPanel
from acd.presentation.platform.widgets.log_viewer import LogViewer

__all__ = [
    "HealthCard",
    "MetricsPanel",
    "BackupPanel",
    "SettingsPanel",
    "LogViewer",
]
