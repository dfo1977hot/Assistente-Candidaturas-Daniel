from __future__ import annotations

from typing import Protocol

from acd.application.application_snapshot import ApplicationSnapshot


class ApplicationFacadeProtocol(Protocol):
    """
    Contrato mínimo que a interface gráfica utiliza.

    A UI depende deste protocolo, não da implementação concreta.
    """

    def start_application(
        self,
        *,
        company_name: str,
        job_title: str,
        job_description: str,
    ) -> object:
        ...

    def snapshot(self) -> ApplicationSnapshot:
        ...

    def clear(self) -> None:
        ...