"""Task scheduler for agent tasks."""

from typing import Any
from datetime import datetime
from enum import Enum
import heapq


class TaskScheduler:
    """Scheduler for managing agent tasks with priorities."""

    def __init__(self) -> None:
        """Initialize task scheduler."""
        self._task_queue: list[tuple[int, int, dict[str, Any]]] = []  # (priority, id, task)
        self._task_counter = 0
        self._running_tasks: dict[int, dict[str, Any]] = {}  # task_id -> task
        self._completed_tasks: list[dict[str, Any]] = []
        self._failed_tasks: list[dict[str, Any]] = []

    def schedule_task(
        self,
        agent_id: int,
        task_type: str,
        priority: int = 5,  # 1-10, lower number = higher priority
        input_data: dict[str, Any] | None = None,
        depends_on: list[int] | None = None,
    ) -> int:
        """Schedule a new task.

        Args:
            agent_id: Agent to execute task
            task_type: Type of task
            priority: Priority (1-10)
            input_data: Input data for task
            depends_on: List of task IDs this depends on

        Returns:
            Task ID
        """
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
            "created_at": datetime.utcnow(),
            "started_at": None,
            "completed_at": None,
            "result": None,
            "error": None,
        }

        # Add to queue with priority (lower number = higher priority)
        heapq.heappush(self._task_queue, (priority, task_id, task))

        return task_id

    def get_next_task(self) -> dict[str, Any] | None:
        """Get next task from queue.

        Returns:
            Next task or None if queue is empty
        """
        while self._task_queue:
            priority, task_id, task = heapq.heappop(self._task_queue)

            # Check dependencies
            if self._has_unmet_dependencies(task):
                # Requeue task
                heapq.heappush(self._task_queue, (priority, task_id, task))
                continue

            task["status"] = "assigned"
            task["started_at"] = datetime.utcnow()
            self._running_tasks[task_id] = task
            return task

        return None

    def _has_unmet_dependencies(self, task: dict[str, Any]) -> bool:
        """Check if task has unmet dependencies.

        Args:
            task: Task to check

        Returns:
            True if has unmet dependencies
        """
        for dep_id in task["depends_on"]:
            # Check if dependency is completed
            is_completed = any(t["id"] == dep_id for t in self._completed_tasks)
            if not is_completed:
                return True
        return False

    def mark_completed(self, task_id: int, result: dict[str, Any] | None = None) -> bool:
        """Mark task as completed.

        Args:
            task_id: Task ID
            result: Task result

        Returns:
            True if successful
        """
        if task_id not in self._running_tasks:
            return False

        task = self._running_tasks[task_id]
        task["status"] = "completed"
        task["completed_at"] = datetime.utcnow()
        task["result"] = result or {}

        self._completed_tasks.append(task)
        del self._running_tasks[task_id]

        return True

    def mark_failed(self, task_id: int, error: str) -> bool:
        """Mark task as failed.

        Args:
            task_id: Task ID
            error: Error message

        Returns:
            True if successful
        """
        if task_id not in self._running_tasks:
            return False

        task = self._running_tasks[task_id]
        task["status"] = "failed"
        task["completed_at"] = datetime.utcnow()
        task["error"] = error

        self._failed_tasks.append(task)
        del self._running_tasks[task_id]

        return True

    def get_task_status(self, task_id: int) -> str | None:
        """Get status of a task.

        Args:
            task_id: Task ID

        Returns:
            Task status or None if not found
        """
        if task_id in self._running_tasks:
            return self._running_tasks[task_id]["status"]

        for task in self._completed_tasks:
            if task["id"] == task_id:
                return task["status"]

        for task in self._failed_tasks:
            if task["id"] == task_id:
                return task["status"]

        return None

    def get_queue_size(self) -> int:
        """Get current queue size.

        Returns:
            Number of pending tasks
        """
        return len(self._task_queue)

    def get_running_tasks(self) -> list[dict[str, Any]]:
        """Get running tasks.

        Returns:
            List of running tasks
        """
        return list(self._running_tasks.values())

    def get_completed_tasks(self) -> list[dict[str, Any]]:
        """Get completed tasks.

        Returns:
            List of completed tasks
        """
        return self._completed_tasks

    def get_failed_tasks(self) -> list[dict[str, Any]]:
        """Get failed tasks.

        Returns:
            List of failed tasks
        """
        return self._failed_tasks

    def get_statistics(self) -> dict[str, Any]:
        """Get scheduler statistics.

        Returns:
            Statistics dictionary
        """
        total_completed = len(self._completed_tasks)
        total_failed = len(self._failed_tasks)
        total = total_completed + total_failed

        return {
            "queue_size": self.get_queue_size(),
            "running_tasks": len(self._running_tasks),
            "completed_tasks": total_completed,
            "failed_tasks": total_failed,
            "total_processed": total,
            "success_rate": (total_completed / total * 100) if total > 0 else 0,
        }

    def clear_completed(self, older_than_hours: int = 24) -> int:
        """Clear old completed tasks.

        Args:
            older_than_hours: Remove completed tasks older than N hours

        Returns:
            Number of tasks removed
        """
        from datetime import timedelta

        cutoff = datetime.utcnow() - timedelta(hours=older_than_hours)

        original_count = len(self._completed_tasks)
        self._completed_tasks = [
            t for t in self._completed_tasks
            if (t.get("completed_at") or datetime.utcnow()) > cutoff
        ]

        return original_count - len(self._completed_tasks)
