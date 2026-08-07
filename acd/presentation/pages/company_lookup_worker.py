from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from PySide6.QtCore import QObject, Signal, Slot

from acd.services.company_lookup_service import CompanyLookupError


class CompanyLookupGateway(Protocol):
    def search(self, name: str, *, force_refresh: bool = False) -> list[object]: ...


class CompanyLookupWorker(QObject):
    succeeded = Signal(object)
    failed = Signal(str)
    finished = Signal()

    def __init__(
        self,
        *,
        service_factory: Callable[[str], CompanyLookupGateway],
        name: str,
        provider_name: str,
        force_refresh: bool,
    ) -> None:
        super().__init__()
        self._name = name
        self._service_factory = service_factory
        self._provider_name = provider_name
        self._force_refresh = force_refresh
        self._cancelled = False

    @Slot()
    def run(self) -> None:
        try:
            service = self._service_factory(self._provider_name)
            results = service.search(
                self._name,
                force_refresh=self._force_refresh,
            )
            if not self._cancelled:
                self.succeeded.emit(results)
        except (ValueError, CompanyLookupError) as exc:
            if not self._cancelled:
                self.failed.emit(str(exc))
        except Exception:
            if not self._cancelled:
                self.failed.emit("Não foi possível concluir a busca de empresas.")
        finally:
            self.finished.emit()

    @Slot()
    def cancel(self) -> None:
        self._cancelled = True
