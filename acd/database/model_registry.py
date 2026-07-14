"""
Registro centralizado automático dos modelos ORM do ACD.

Este módulo deve ser importado antes de qualquer chamada a:

    Base.metadata.create_all(...)

Sua única responsabilidade é garantir que todos os modelos SQLAlchemy
sejam importados e registrados no Base.metadata.

Não é necessário adicionar novos imports manualmente. Qualquer novo
modelo criado em:

    acd.domain.agent
    acd.domain.agents
    acd.domain.entities

será registrado automaticamente.
"""

from __future__ import annotations

import importlib
import logging
import pkgutil

logger = logging.getLogger(__name__)

_PACKAGES: tuple[str, ...] = (
    "acd.domain.agent",
    "acd.domain.agents",
    "acd.domain.entities",
)


def _import_package(package_name: str) -> None:
    """
    Importa automaticamente todos os módulos públicos de um pacote.

    Ignora:

    - __init__.py
    - módulos iniciados por "_"

    Parameters
    ----------
    package_name:
        Nome completo do pacote.
    """

    package = importlib.import_module(package_name)

    if not hasattr(package, "__path__"):
        return

    for module in pkgutil.iter_modules(package.__path__):

        module_name = module.name

        if module_name.startswith("_"):
            continue

        full_name = f"{package_name}.{module_name}"

        try:
            importlib.import_module(full_name)

        except Exception as exc:  # pragma: no cover
            logger.exception(
                "Erro ao importar módulo ORM '%s': %s",
                full_name,
                exc,
            )
            raise


def load_models() -> None:
    """
    Importa todos os modelos ORM do projeto.
    """

    for package in _PACKAGES:
        _import_package(package)


#
# Carrega automaticamente os modelos quando este módulo é importado.
#

load_models()