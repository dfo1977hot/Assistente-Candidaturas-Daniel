"""
Assistente de Candidaturas do Daniel
Versionamento da aplicação
"""

from importlib.metadata import PackageNotFoundError, version


def get_version() -> str:
    """Return the installed ACD version or a clear source-tree sentinel."""

    try:
        return version("acd")
    except PackageNotFoundError:
        return "0+unknown"


__version__ = get_version()

APP_NAME = "Assistente de Candidaturas do Daniel"
