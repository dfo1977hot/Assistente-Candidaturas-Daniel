"""Platform presentation layer."""

from acd.presentation.platform.pages import SystemPage
from acd.presentation.platform.widgets import (
    HealthCard,
    MetricsPanel,
    BackupPanel,
    SettingsPanel,
    LogViewer,
)

__all__ = [
    "SystemPage",
    "HealthCard",
    "MetricsPanel",
    "BackupPanel",
    "SettingsPanel",
    "LogViewer",
]
