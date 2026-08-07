"""Platform presentation layer."""

from acd.presentation.platform.pages import SystemPage
from acd.presentation.platform.widgets import (
    BackupPanel,
    HealthCard,
    LogViewer,
    MetricsPanel,
    SettingsPanel,
)

__all__ = [
    "SystemPage",
    "HealthCard",
    "MetricsPanel",
    "BackupPanel",
    "SettingsPanel",
    "LogViewer",
]
