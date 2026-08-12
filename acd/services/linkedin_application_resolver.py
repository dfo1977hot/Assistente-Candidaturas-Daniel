from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LinkedInApplicationResolution:
    """Resultado da resolução da ação de candidatura no LinkedIn."""

    url: str = ""
    application_type: str = ""
    accepting_applications: bool | None = True


class LinkedInApplicationResolver(Protocol):
    """Boundary used by Presentation to resolve LinkedIn application URLs."""

    def resolve_linkedin_application_url(
        self,
        job_url: str,
        progress: Callable[[object], None] | None = None,
    ) -> LinkedInApplicationResolution: ...


class UnavailableLinkedInApplicationResolver:
    """Fallback for isolated Presentation contexts without infrastructure wiring."""

    def resolve_linkedin_application_url(
        self,
        job_url: str,
        progress: Callable[[object], None] | None = None,
    ) -> LinkedInApplicationResolution:
        del job_url, progress
        raise RuntimeError(
            "O resolvedor de candidatura do LinkedIn não está disponível neste contexto."
        )
