"""Repository for multi-agent persistence."""

from typing import Any

from acd.database import database as database_module
from acd.domain.agents.agent import Agent, AgentStatus
from acd.domain.agents.task import AgentTask, TaskStatus, TaskPriority
from acd.domain.agents.message import AgentMessage, MessageType
from acd.domain.agents.capability import AgentCapability
from acd.domain.agents.tool import AgentTool
from acd.domain.agents.session import AgentSession
from acd.domain.agents.memory import AgentMemory, MemoryType


class AgentRepository:
    """Repository for agent persistence."""

    # Agent methods
    def create_agent(
        self,
        name: str,
        agent_type: str,
        description: str,
        max_parallel_tasks: int = 1,
        timeout_seconds: int = 300,
        retry_count: int = 3,
        config: dict[str, Any] | None = None,
    ) -> Agent:
        """Create a new agent.

        Args:
            name: Agent name
            agent_type: Agent type
            description: Description
            max_parallel_tasks: Max parallel tasks
            timeout_seconds: Timeout in seconds
            retry_count: Retry count
            config: Configuration

        Returns:
            Created agent
        """
        with database_module.SessionLocal() as session:
            agent = Agent(
                name=name,
                agent_type=agent_type,
                description=description,
                max_parallel_tasks=max_parallel_tasks,
                timeout_seconds=timeout_seconds,
                retry_count=retry_count,
                config=config or {},
            )
            session.add(agent)
            session.commit()
            session.refresh(agent)
            return agent

    def get_agent(self, agent_id: int) -> Agent | None:
        """Get agent by ID.

        Args:
            agent_id: Agent ID

        Returns:
            Agent or None
        """
        with database_module.SessionLocal() as session:
            return session.query(Agent).filter(Agent.id == agent_id).first()

    def get_agent_by_name(self, name: str) -> Agent | None:
        """Get agent by name.

        Args:
            name: Agent name

        Returns:
            Agent or None
        """
        with database_module.SessionLocal() as session:
            return session.query(Agent).filter(Agent.name == name).first()

    def list_agents_by_type(self, agent_type: str) -> list[Agent]:
        """List agents by type.

        Args:
            agent_type: Agent type

        Returns:
            List of agents
        """
        with database_module.SessionLocal() as session:
            return session.query(Agent).filter(Agent.agent_type == agent_type).all()

    def update_agent_status(self, agent_id: int, status: AgentStatus) -> Agent | None:
        """Update agent status.

        Args:
            agent_id: Agent ID
            status: New status

        Returns:
            Updated agent or None
        """
        with database_module.SessionLocal() as session:
            agent = session.query(Agent).filter(Agent.id == agent_id).first()
            if agent:
                agent.status = status
                session.commit()
                session.refresh(agent)
            return agent

    # Task methods
    def create_task(
        self,
        agent_id: int,
        task_type: str,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        input_data: dict[str, Any] | None = None,
        estimated_duration_seconds: int = 0,
        depends_on: list[int] | None = None,
        session_id: int | None = None,
    ) -> AgentTask:
        """Create a new task.

        Args:
            agent_id: Agent ID
            task_type: Task type
            description: Description
            priority: Priority
            input_data: Input data
            estimated_duration_seconds: Estimated duration
            depends_on: Dependencies
            session_id: Session ID

        Returns:
            Created task
        """
        with database_module.SessionLocal() as session:
            task = AgentTask(
                agent_id=agent_id,
                task_type=task_type,
                description=description,
                priority=priority,
                input_data=input_data or {},
                estimated_duration_seconds=estimated_duration_seconds,
                depends_on=depends_on or [],
                session_id=session_id,
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task

    def get_task(self, task_id: int) -> AgentTask | None:
        """Get task by ID.

        Args:
            task_id: Task ID

        Returns:
            Task or None
        """
        with database_module.SessionLocal() as session:
            return session.query(AgentTask).filter(AgentTask.id == task_id).first()

    def list_tasks_by_agent(self, agent_id: int, status: TaskStatus | None = None) -> list[AgentTask]:
        """List tasks for agent.

        Args:
            agent_id: Agent ID
            status: Optional filter by status

        Returns:
            List of tasks
        """
        with database_module.SessionLocal() as session:
            query = session.query(AgentTask).filter(AgentTask.agent_id == agent_id)
            if status:
                query = query.filter(AgentTask.status == status)
            return query.all()

    def update_task_status(self, task_id: int, status: TaskStatus, result: dict[str, Any] | None = None) -> AgentTask | None:
        """Update task status.

        Args:
            task_id: Task ID
            status: New status
            result: Result data

        Returns:
            Updated task or None
        """
        with database_module.SessionLocal() as session:
            task = session.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.status = status
                if result:
                    task.result = result
                session.commit()
                session.refresh(task)
            return task

    # Message methods
    def create_message(
        self,
        message_type: MessageType,
        subject: str,
        content: str,
        sender_id: int | None = None,
        receiver_id: int | None = None,
        payload: dict[str, Any] | None = None,
        task_id: int | None = None,
        session_id: int | None = None,
    ) -> AgentMessage:
        """Create a message.

        Args:
            message_type: Message type
            subject: Subject
            content: Content
            sender_id: Sender agent ID
            receiver_id: Receiver agent ID
            payload: Payload
            task_id: Related task ID
            session_id: Session ID

        Returns:
            Created message
        """
        with database_module.SessionLocal() as session:
            msg = AgentMessage(
                message_type=message_type,
                subject=subject,
                content=content,
                sender_id=sender_id,
                receiver_id=receiver_id,
                payload=payload or {},
                task_id=task_id,
                session_id=session_id,
            )
            session.add(msg)
            session.commit()
            session.refresh(msg)
            return msg

    def get_messages_by_session(self, session_id: int) -> list[AgentMessage]:
        """Get messages for session.

        Args:
            session_id: Session ID

        Returns:
            List of messages
        """
        with database_module.SessionLocal() as session:
            return session.query(AgentMessage).filter(AgentMessage.session_id == session_id).all()

    # Session methods
    def create_session(
        self,
        title: str,
        session_type: str,
        description: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> AgentSession:
        """Create a session.

        Args:
            title: Session title
            session_type: Session type
            description: Description
            context: Context data

        Returns:
            Created session
        """
        with database_module.SessionLocal() as session:
            agent_session = AgentSession(
                title=title,
                session_type=session_type,
                description=description,
                context=context or {},
            )
            session.add(agent_session)
            session.commit()
            session.refresh(agent_session)
            return agent_session

    def get_session(self, session_id: int) -> AgentSession | None:
        """Get session by ID.

        Args:
            session_id: Session ID

        Returns:
            Session or None
        """
        with database_module.SessionLocal() as session:
            return session.query(AgentSession).filter(AgentSession.id == session_id).first()

    def close_session(self, session_id: int) -> AgentSession | None:
        """Close a session.

        Args:
            session_id: Session ID

        Returns:
            Updated session or None
        """
        with database_module.SessionLocal() as session:
            agent_session = session.query(AgentSession).filter(AgentSession.id == session_id).first()
            if agent_session:
                agent_session.is_active = False
                session.commit()
                session.refresh(agent_session)
            return agent_session

    # Memory methods
    def save_memory(
        self,
        agent_id: int,
        memory_type: MemoryType,
        key: str,
        value: dict[str, Any],
        session_id: int | None = None,
    ) -> AgentMemory:
        """Save agent memory.

        Args:
            agent_id: Agent ID
            memory_type: Memory type
            key: Memory key
            value: Memory value
            session_id: Optional session ID

        Returns:
            Created memory
        """
        with database_module.SessionLocal() as session:
            memory = AgentMemory(
                agent_id=agent_id,
                memory_type=memory_type,
                key=key,
                value=value,
                session_id=session_id,
            )
            session.add(memory)
            session.commit()
            session.refresh(memory)
            return memory

    def get_memory(self, agent_id: int, key: str) -> AgentMemory | None:
        """Get memory by key.

        Args:
            agent_id: Agent ID
            key: Memory key

        Returns:
            Memory or None
        """
        with database_module.SessionLocal() as session:
            return session.query(AgentMemory).filter(
                AgentMemory.agent_id == agent_id,
                AgentMemory.key == key,
            ).first()

    # Capability methods
    def add_capability(
        self,
        agent_id: int,
        name: str,
        capability_type: str,
        description: str,
        requires_approval: bool = False,
    ) -> AgentCapability:
        """Add capability to agent.

        Args:
            agent_id: Agent ID
            name: Capability name
            capability_type: Type
            description: Description
            requires_approval: Requires approval

        Returns:
            Created capability
        """
        with database_module.SessionLocal() as session:
            cap = AgentCapability(
                agent_id=agent_id,
                name=name,
                capability_type=capability_type,
                description=description,
                requires_approval=requires_approval,
            )
            session.add(cap)
            session.commit()
            session.refresh(cap)
            return cap

    def get_agent_capabilities(self, agent_id: int) -> list[AgentCapability]:
        """Get capabilities for agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of capabilities
        """
        with database_module.SessionLocal() as session:
            return session.query(AgentCapability).filter(AgentCapability.agent_id == agent_id).all()

    # Tool methods
    def authorize_tool(
        self,
        agent_id: int,
        tool_name: str,
        category: str,
        description: str,
        requires_approval: bool = False,
    ) -> AgentTool:
        """Authorize tool for agent.

        Args:
            agent_id: Agent ID
            tool_name: Tool name
            category: Category
            description: Description
            requires_approval: Requires approval

        Returns:
            Created tool authorization
        """
        with database_module.SessionLocal() as session:
            tool = AgentTool(
                agent_id=agent_id,
                tool_name=tool_name,
                category=category,
                description=description,
                requires_approval=requires_approval,
            )
            session.add(tool)
            session.commit()
            session.refresh(tool)
            return tool

    def get_agent_tools(self, agent_id: int) -> list[AgentTool]:
        """Get authorized tools for agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of tools
        """
        with database_module.SessionLocal() as session:
            return session.query(AgentTool).filter(AgentTool.agent_id == agent_id).all()
