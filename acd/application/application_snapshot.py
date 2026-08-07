from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ApplicationSnapshot:
    """
    Representação somente leitura da sessão de candidatura.
    """

    company_name: str
    job_title: str
    job_url: str
    job_description: str

    is_analyzed: bool
    has_resume: bool
    is_registered: bool