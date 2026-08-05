"""Installed desktop entry point."""

from __future__ import annotations

import logging
import sys

from PySide6.QtWidgets import QApplication

from acd.core.theme_manager import ThemeManager
from acd.desktop_composition_root import DesktopCompositionRoot
from acd.observability import (
    close_logging,
    configure_logging,
    log_event,
    observed_operation,
)


def main() -> int:
    """Build and run the productive desktop application."""
    configure_logging()
    logger = logging.getLogger("acd.desktop")
    log_event(logger, logging.INFO, "application.starting", "Application starting", status="started")
    try:
        with observed_operation(logger, "application.startup", component="desktop"):
            application = QApplication(sys.argv)
            ThemeManager.load(application)
            window = DesktopCompositionRoot().build_main_window()
            window.show()
        log_event(logger, logging.INFO, "application.started", "Application started", status="completed")
        return application.exec()
    except Exception:
        logger.exception("Unhandled application exception")
        raise
    finally:
        log_event(logger, logging.INFO, "application.shutdown", "Application shutdown", status="completed")
        close_logging()
