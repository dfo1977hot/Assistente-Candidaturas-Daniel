"""Supervisor service for multi-agent coordination."""

from datetime import UTC, datetime
from typing import Any

from acd.domain.agents.message import MessageType
from acd.infrastructure.agents.capability_service import CapabilityService
from acd.infrastructure.agents.context import ContextManager
from acd.infrastructure.agents.message_bus import MessageBus
from acd.infrastructure.agents.registry import AgentRegistry
from acd.infrastructure.agents.task_scheduler import TaskScheduler
from acd.infrastructure.repositories.agents.agent_repository import AgentRepository


class SupervisorService:
    """Supervisor service for coordinating multiple agents."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        message_bus: MessageBus | None = None,
        context_manager: ContextManager | None = None,
        task_scheduler: TaskScheduler | None = None,
        capability_service: CapabilityService | None = None,
        repository: AgentRepository | None = None,
    ) -> None:
        """Initialize supervisor.

        Args:
            registry: Agent registry
            message_bus: Message bus
            context_manager: Context manager
            task_scheduler: Task scheduler
            capability_service: Capability service
            repository: Agent repository
        """
        self.registry = registry or AgentRegistry()
        self.message_bus = message_bus or MessageBus()
        self.context_manager = context_manager or ContextManager()
        self.task_scheduler = task_scheduler or TaskScheduler()
        self.capability_service = capability_service or CapabilityService()
        self.repository = repository or AgentRepository()

        self._current_session_id: int | None = None
        self._execution_history: list[dict[str, Any]] = []

    def start_session(self, title: str, user_objective: str) -> int:
        """Start a new session.

        Args:
            title: Session title
            user_objective: User's objective

        Returns:
            Session ID
        """
        session = self.repository.create_session(
            title=title,
            session_type="multi_agent_execution",
            description=user_objective,
            context={"user_objective": user_objective},
        )

        self._current_session_id = session.id

        # Publish session started message
        self.message_bus.publish(
            message_type=MessageType.TASK_CREATED,
            sender_id=None,  # Supervisor
            receiver_id=None,  # Broadcast
            subject="Session Started",
            content=f"New session started: {title}",
            payload={"session_id": session.id, "objective": user_objective},
            session_id=session.id,
        )

        return session.id

    def process_user_request(
        self, user_request: str, session_id: int | None = None
    ) -> dict[str, Any]:
        """Process user request by distributing to agents.

        Args:
            user_request: User's request
            session_id: Optional session ID

        Returns:
            Processing result
        """
        if session_id is None:
            session_id = self._current_session_id

        if session_id is None:
            return {"success": False, "error": "No active session"}

        # Analyze request and determine which agents should handle it
        agents_to_involve = self._select_agents_for_request(user_request)

        if not agents_to_involve:
            return {"success": False, "error": "No suitable agents found"}
        task_ids = []
        for agent_dict in agents_to_involve:
            agent_id = agent_dict["id"]

            # Create context for agent
            self.context_manager.create_context(
                agent_id=agent_id,
                agent_name=agent_dict["name"],
                objective=user_request,
                session_id=session_id,
            )

            # Schedule task
            task_id = self.task_scheduler.schedule_task(
                agent_id=agent_id,
                task_type=f"process_request_{agent_dict['type']}",
                priority=1,  # High priority for user requests
                input_data={"user_request": user_request},
                session_id=session_id,
            )

            task_ids.append(task_id)

            # Publish task assignment
            self.message_bus.publish(
                message_type=MessageType.TASK_ASSIGNED,
                sender_id=None,  # Supervisor
                receiver_id=agent_id,
                subject="New Task Assignment",
                content=f"Process user request: {user_request[:100]}",
                payload={"task_id": task_id, "user_request": user_request},
                task_id=task_id,
                session_id=session_id,
            )

        return {
            "success": True,
            "session_id": session_id,
            "agents_involved": len(agents_to_involve),
            "tasks_created": task_ids,
        }

    def _select_agents_for_request(self, user_request: str) -> list[dict[str, Any]]:
        """Select agents suitable for handling request.

        Args:
            user_request: User request

        Returns:
            List of selected agents
        """
        # Simple keyword-based selection (can be enhanced with NLP)
        request_lower = user_request.lower()

        # Define keywords for each agent type
        agent_keywords = {
            "resume": ["resume", "currículo", "cv", "curriculum"],
            "ats": ["ats", "score", "aderência", "match"],
            "automation": ["candidatar", "apply", "submit", "automático"],
            "career": ["carreira", "planejamento", "evolução", "desenvolvimento"],
            "interview": ["entrevista", "simulação", "preparação", "interview"],
            "analytics": ["análise", "analytics", "relatório", "report", "kpi"],
            "workflow": ["workflow", "automação", "automação"],
        }

        # Find matching agents
        selected = []
        all_agents = self.registry.list_all_agents()

        for agent in all_agents:
            agent_type = agent.get("type", "").lower()

            # Check if agent type keywords match request
            keywords = agent_keywords.get(agent_type, [])
            if any(keyword in request_lower for keyword in keywords):
                selected.append(agent)

        # If no specific match, add resume agent as fallback
        if not selected:
            for agent in all_agents:
                if agent.get("type") == "resume":
                    selected.append(agent)
                    break

        return selected

    def handle_task_completion(self, task_id: int, result: dict[str, Any]) -> dict[str, Any]:
        """Handle task completion.

        Args:
            task_id: Completed task ID
            result: Task result

        Returns:
            Handling result
        """
        # Update task status
        task = self.repository.get_task(task_id)
        if task:
            self.repository.update_task_status(task_id, "completed", result)

            # Publish completion message
            self.message_bus.publish(
                message_type=MessageType.TASK_COMPLETED,
                sender_id=task.agent_id,
                receiver_id=None,  # Broadcast
                subject="Task Completed",
                content=f"Task {task_id} completed successfully",
                payload={"task_id": task_id, "result": result},
                task_id=task_id,
                session_id=task.session_id,
            )

            # Record execution
            self._execution_history.append(
                {
                    "task_id": task_id,
                    "status": "completed",
                    "timestamp": datetime.now(UTC),
                    "result": result,
                }
            )

            return {"success": True, "task_id": task_id}

        return {"success": False, "error": "Task not found"}

    def handle_task_failure(self, task_id: int, error: str) -> dict[str, Any]:
        """Handle task failure.

        Args:
            task_id: Failed task ID
            error: Error message

        Returns:
            Handling result
        """
        # Update task status
        task = self.repository.get_task(task_id)
        if task:
            self.repository.update_task_status(task_id, "failed")

            # Publish failure message
            self.message_bus.publish(
                message_type=MessageType.TASK_FAILED,
                sender_id=task.agent_id,
                receiver_id=None,  # Broadcast
                subject="Task Failed",
                content=f"Task {task_id} failed: {error}",
                payload={"task_id": task_id, "error": error},
                task_id=task_id,
                session_id=task.session_id,
            )

            # Record execution
            self._execution_history.append(
                {
                    "task_id": task_id,
                    "status": "failed",
                    "error": error,
                    "timestamp": datetime.now(UTC),
                }
            )

            return {"success": True, "task_id": task_id}

        return {"success": False, "error": "Task not found"}

    def request_agent_approval(
        self,
        agent_id: int,
        action: str,
        details: dict[str, Any],
        session_id: int | None = None,
    ) -> dict[str, Any]:
        """Request approval from user for agent action.

        Args:
            agent_id: Agent requesting approval
            action: Action to approve
            details: Action details
            session_id: Session ID

        Returns:
            Request result
        """
        if session_id is None:
            session_id = self._current_session_id

        # Publish approval request
        msg = self.message_bus.publish(
            message_type=MessageType.NEED_APPROVAL,
            sender_id=agent_id,
            receiver_id=None,  # Broadcast to user
            subject=f"Approval Needed: {action}",
            content=f"Agent {agent_id} requests approval for: {action}",
            payload={"agent_id": agent_id, "action": action, "details": details},
            session_id=session_id,
            requires_response=True,
        )

        return {"success": True, "message_id": msg["id"]}

    def get_session_status(self, session_id: int | None = None) -> dict[str, Any]:
        """Get status of current session.

        Args:
            session_id: Optional session ID

        Returns:
            Session status
        """
        if session_id is None:
            session_id = self._current_session_id

        if session_id is None:
            return {"success": False, "error": "No active session"}

        session = self.repository.get_session(session_id)
        if not session:
            return {"success": False, "error": "Session not found"}

        # Get messages
        messages = self.repository.get_messages_by_session(session_id)

        # Get scheduler stats
        scheduler_stats = self.task_scheduler.get_statistics()

        return {
            "success": True,
            "session_id": session_id,
            "title": session.title,
            "is_active": session.is_active,
            "created_at": session.created_at.isoformat(),
            "message_count": len(messages),
            "scheduler_stats": scheduler_stats,
            "execution_history_count": len(self._execution_history),
        }

    def end_session(self, session_id: int | None = None) -> dict[str, Any]:
        """End current session.

        Args:
            session_id: Optional session ID

        Returns:
            Result
        """
        if session_id is None:
            session_id = self._current_session_id

        if session_id is None:
            return {"success": False, "error": "No active session"}

        session = self.repository.close_session(session_id)

        if session:
            self._current_session_id = None
            return {
                "success": True,
                "session_id": session_id,
                "completed_at": session.completed_at.isoformat() if session.completed_at else None,
            }

        return {"success": False, "error": "Could not close session"}

    def get_supervisor_status(self) -> dict[str, Any]:
        """Get supervisor status.

        Returns:
            Supervisor status
        """
        agents = self.registry.list_all_agents()
        scheduler_stats = self.task_scheduler.get_statistics()

        return {
            "agents_registered": len(agents),
            "agents": [
                {
                    "id": a["id"],
                    "name": a["name"],
                    "type": a["type"],
                    "status": a["status"],
                }
                for a in agents
            ],
            "current_session_id": self._current_session_id,
            "scheduler_stats": scheduler_stats,
            "execution_history_count": len(self._execution_history),
        }
