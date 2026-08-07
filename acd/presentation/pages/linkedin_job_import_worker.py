from __future__ import annotations

from PySide6.QtCore import QObject, Signal, Slot

from acd.services.linkedin_job_import_service import (
    ImportedLinkedInJob,
    LinkedInJobImportError,
    LinkedInJobImportService,
)


class LinkedInJobImportWorker(QObject):
    """Executa a importação sem bloquear a interface gráfica."""

    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(self, service: LinkedInJobImportService, url: str) -> None:
        super().__init__()
        self._service = service
        self._url = url

    @Slot()
    def run(self) -> None:
        try:
            result: ImportedLinkedInJob = self._service.import_from_url(self._url)
            self.succeeded.emit(result)
        except LinkedInJobImportError as exc:
            self.failed.emit(str(exc))
        except Exception as exc:  # pragma: no cover - defensive worker boundary
            self.failed.emit(f"Falha inesperada ao importar a vaga: {exc}")
        finally:
            self.finished.emit()
