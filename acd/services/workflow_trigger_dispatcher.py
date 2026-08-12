from __future__ import annotations

import logging
from typing import Any

from acd.services.workflow_service import WorkflowService

logger = logging.getLogger(__name__)


class WorkflowTriggerDispatcher:
    """Dispatch productive service events to compatible active workflows."""

    EVENT_TRIGGERS = {
        "job.created": "Vaga criada manualmente",
        "job.imported": "Vaga importada",
        "application.created": "Candidatura criada",
        "application.status_changed": "Mudança de status",
    }

    def __init__(self, workflow_service: WorkflowService) -> None:
        self.workflow_service = workflow_service

    def dispatch(self, event_type: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
        trigger = self.EVENT_TRIGGERS.get(event_type)
        if trigger is None:
            return []
        occurrence = str(payload.get("occurrence_id") or payload.get("event_id") or "")
        entity_id = payload.get("entity_id") or payload.get("job_id") or payload.get(
            "application_id"
        )
        results = []
        for workflow in self.workflow_service.list_workflows():
            definition = self.workflow_service.parse_definition(workflow)
            if not workflow.active or definition["trigger"] != trigger:
                continue
            if trigger == "Mudança de status":
                target = str(definition.get("target_status") or "")
                if target and target != str(payload.get("application_status") or ""):
                    continue
            key = f"{workflow.id}:{event_type}:{entity_id}:{occurrence}"
            if self.workflow_service.has_idempotency_key(key):
                continue
            context = dict(payload)
            context.update(
                {
                    "trigger_origin": "evento",
                    "trigger": trigger,
                    "event_type": event_type,
                    "idempotency_key": key,
                }
            )
            try:
                results.append(
                    self.workflow_service.execute_assisted(workflow.id, context=context)
                )
            except Exception:
                logger.exception(
                    "Automatic workflow dispatch failed: workflow=%s event=%s entity=%s",
                    workflow.id,
                    event_type,
                    entity_id,
                )
        return results
