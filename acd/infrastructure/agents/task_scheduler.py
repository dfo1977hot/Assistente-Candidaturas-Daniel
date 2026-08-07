"""Task scheduler for agent tasks."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
import heapq
from typing import Any


class TaskScheduler:
    """Scheduler for managing agent tasks with priorities."""

    def __init__(self) -> None:
        """Initialize task scheduler."""
        self._task_queue: list[tuple[int, int, dict[str, Any]]] = []
        self._task_counter: int = 0
        self._running_tasks: dict[int, dict[str, Any]] = {}
        self._completed_tasks: list[dict[str, Any]] = []
        self._failed_tasks: list[dict[str, Any]] = []

    def schedule_task(
        self,
        agent_id: int,
        task_type: str,
        priority: int = 5,
        input_data: dict[str, Any] | None = None,
        depends_on: list[int] | None = None,
    ) -> int:
        """Schedule a new task."""
        self._task_counter += 1
        task_id = self._task_counter

        task = {
            "id": task_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "priority": priority,
            "input_data": input_data or {},
            "depends_on": depends_on or [],
            "status": "pending",
            "created_at": datetime.now(UTC),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }

        heapq.heappush(
            self._task_queue,
            (priority, task_id, task),
        )

        return task_id

    def get_next_task(self) -> dict[str, Any] | None:
        """Return the next executable task."""
        while self._task_queue:
            priority, task_id, task = heapq.heappop(self._task_queue)

            if self._has_unmet_dependencies(task):
                heapq.heappush(
                    self._task_queue,
                    (priority, task_id, task),
                )
                continue

            task["status"] = "assigned"
            task["started_at"] = datetime.now(UTC)
            self._running_tasks[task_id] = task
            return task

        return None

    def _has_unmet_dependencies(
        self,
        task: dict[str, Any],
    ) -> bool:
        """Return True if dependencies are not satisfied."""
        return any(
            not any(
                completed["id"] == dependency_id
                for completed in self._completed_tasks
            )
            for dependency_id in task["depends_on"]
        )

    def mark_completed(
        self,
        task_id: int,
        result: dict[str, Any] | None = None,
    ) -> bool:
        """Mark a task as completed."""
        task = self._running_tasks.get(task_id)

        if task is None:
            return False

        task["status"] = "completed"
        task["completed_at"] = datetime.now(UTC)
        task["result"] = result or {}

        self._completed_tasks.append(task)
        del self._running_tasks[task_id]

        return True

    def mark_failed(
        self,
        task_id: int,
        error: str,
    ) -> bool:
        """Mark a task as failed."""
        task = self._running_tasks.get(task_id)

        if task is None:
            return False

        task["status"] = "failed"
        task["completed_at"] = datetime.now(UTC)
        task["error"] = error

        self._failed_tasks.append(task)
        del self._running_tasks[task_id]

        return True

    def get_task_status(
        self,
        task_id: int,
    ) -> str | None:
        """Return task status."""

        if task_id in self._running_tasks:
            return self._running_tasks[task_id]["status"]

        for collection in (
            self._completed_tasks,
            self._failed_tasks,
        ):
            for task in collection:
                if task["id"] == task_id:
                    return task["status"]

        return None

    def get_queue_size(self) -> int:
        """Return queue size."""
        return len(self._task_queue)

    def get_running_tasks(self) -> list[dict[str, Any]]:
        """Return running tasks."""
        return list(self._running_tasks.values())

    def get_completed_tasks(self) -> list[dict[str, Any]]:
        """Return completed tasks."""
        return self._completed_tasks

    def get_failed_tasks(self) -> list[dict[str, Any]]:
        """Return failed tasks."""
        return self._failed_tasks

    def get_statistics(self) -> dict[str, Any]:
        """Return scheduler statistics."""

        completed = len(self._completed_tasks)
        failed = len(self._failed_tasks)
        total = completed + failed

        return {
            "queue_size": self.get_queue_size(),
            "running_tasks": len(self._running_tasks),
            "completed_tasks": completed,
            "failed_tasks": failed,
            "total_processed": total,
            "success_rate": (
                completed / total * 100
                if total
                else 0
            ),
        }

    def clear_completed(
        self,
        older_than_hours: int = 24,
    ) -> int:
        """Remove completed tasks older than the given age."""

        cutoff = datetime.now(UTC) - timedelta(
            hours=older_than_hours,
        )

        original_count = len(self._completed_tasks)

        self._completed_tasks = [
            task
            for task in self._completed_tasks
            if (
                task.get("completed_at")
                or datetime.now(UTC)
            ) > cutoff
        ]

        return original_count - len(
            self._completed_tasks
        )