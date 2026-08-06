import os

from PySide6.QtCore import QCoreApplication, QEvent
from PySide6.QtWidgets import QApplication
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qapp() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture(autouse=True)
def cleanup_qt_widgets(qapp: QApplication):
    """Dispose test-created top-level widgets before the next Qt test starts."""
    yield

    for widget in qapp.topLevelWidgets():
        widget.close()
        widget.deleteLater()

    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
    qapp.processEvents()
    QCoreApplication.sendPostedEvents(None, QEvent.DeferredDelete)
