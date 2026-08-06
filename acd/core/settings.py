from dataclasses import dataclass

from acd.version import get_version


@dataclass
class Settings:

    app_name: str = "Assistente de Candidaturas do Daniel"

    version: str = get_version()
