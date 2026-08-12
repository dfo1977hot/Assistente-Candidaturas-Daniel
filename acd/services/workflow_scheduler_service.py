from __future__ import annotations

from calendar import monthrange
from datetime import UTC, datetime, timedelta
from typing import Any

from acd.services.workflow_service import WorkflowService


class WorkflowSchedulerService:
    """Persistent in-process scheduler backed by workflow definition JSON."""

    RECURRENCES = ("Uma vez", "Diariamente", "Semanalmente", "Mensalmente")

    def __init__(self, workflow_service: WorkflowService) -> None:
        self.workflow_service = workflow_service

    @staticmethod
    def calculate_next_run(
        scheduled_at: datetime,
        recurrence: str,
        *,
        after: datetime | None = None,
    ) -> datetime | None:
        if recurrence == "Uma vez":
            return scheduled_at if after is None or scheduled_at > after else None
        reference = after or scheduled_at
        candidate = scheduled_at
        month_offset = 0
        while candidate <= reference:
            if recurrence == "Diariamente":
                candidate += timedelta(days=1)
            elif recurrence == "Semanalmente":
                candidate += timedelta(days=7)
            elif recurrence == "Mensalmente":
                month_offset += 1
                absolute_month = scheduled_at.month - 1 + month_offset
                year = scheduled_at.year + absolute_month // 12
                month = absolute_month % 12 + 1
                day = min(scheduled_at.day, monthrange(year, month)[1])
                candidate = scheduled_at.replace(year=year, month=month, day=day)
            else:
                raise ValueError(f"Recorrência inválida: {recurrence}")
        return candidate

    def list_active_schedules(self) -> list[tuple[Any, dict[str, Any]]]:
        schedules = []
        for workflow in self.workflow_service.list_workflows():
            definition = self.workflow_service.parse_definition(workflow)
            schedule = definition.get("schedule")
            if (
                workflow.active
                and definition["trigger"] == "Agendado"
                and isinstance(schedule, dict)
                and schedule.get("active", True)
            ):
                schedules.append((workflow, schedule))
        return schedules

    def due_schedules(self, now: datetime | None = None) -> list[tuple[Any, dict[str, Any]]]:
        current = now or datetime.now(UTC).replace(tzinfo=None)
        return [
            (workflow, schedule)
            for workflow, schedule in self.list_active_schedules()
            if self._parse_datetime(schedule.get("next_run_at")) <= current
        ]

    def run_due(self, now: datetime | None = None) -> list[dict[str, Any]]:
        current = now or datetime.now(UTC).replace(tzinfo=None)
        results = []
        for workflow, schedule in self.due_schedules(current):
            occurrence = str(schedule["next_run_at"])
            key = f"{workflow.id}:scheduled:{workflow.id}:{occurrence}"
            if not self.workflow_service.has_idempotency_key(key):
                results.append(
                    self.workflow_service.execute_assisted(
                        workflow.id,
                        context={
                            "trigger_origin": "agendada",
                            "trigger": "Agendado",
                            "idempotency_key": key,
                        },
                    )
                )
            schedule["last_run_at"] = current.isoformat()
            scheduled_at = self._parse_datetime(schedule["scheduled_at"])
            next_run = self.calculate_next_run(
                scheduled_at,
                str(schedule["recurrence"]),
                after=current,
            )
            schedule["next_run_at"] = next_run.isoformat() if next_run else None
            schedule["active"] = next_run is not None
            definition = self.workflow_service.parse_definition(workflow)
            self.workflow_service.save_workflow(
                workflow.id,
                name=workflow.name,
                description=workflow.description,
                trigger=definition["trigger"],
                steps=definition["steps"],
                active=workflow.active,
                version=workflow.version,
                schedule=schedule,
                target_status=definition.get("target_status", ""),
            )
        return results

    def next_scheduled_run(self) -> datetime | None:
        values = [
            self._parse_datetime(schedule.get("next_run_at"))
            for _, schedule in self.list_active_schedules()
            if schedule.get("next_run_at")
        ]
        return min(values) if values else None

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if not value:
            return datetime.max
        return datetime.fromisoformat(str(value)).replace(tzinfo=None)
