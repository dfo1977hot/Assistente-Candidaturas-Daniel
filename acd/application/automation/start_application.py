from __future__ import annotations

from acd.services.automation_service import AutomationContext, AutomationService


def start_application(service: AutomationService, *, context: AutomationContext) -> dict[str, object]:
    """Aplicação para iniciar uma automação de candidatura."""
    return service.run(context)
