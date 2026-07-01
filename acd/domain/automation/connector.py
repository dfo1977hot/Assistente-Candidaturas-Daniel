from __future__ import annotations

from typing import Protocol


class Connector(Protocol):
    """Interface base para conectores de plataformas de recrutamento."""

    def login(self) -> bool:
        ...

    def open_job(self, url: str) -> bool:
        ...

    def fill_form(self) -> bool:
        ...

    def upload_resume(self, path: str) -> bool:
        ...

    def upload_cover_letter(self, path: str) -> bool:
        ...

    def submit(self) -> bool:
        ...

    def capture_result(self) -> dict[str, object]:
        ...

    def close(self) -> None:
        ...
