"""Agent Console page for multi-agent platform."""

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from acd.application.multi_agent.session import (
    initialize_multi_agent_platform,
    process_user_request,
    start_session,
)
from acd.infrastructure.agents.capability_service import CapabilityService
from acd.infrastructure.agents.context import ContextManager
from acd.infrastructure.agents.message_bus import MessageBus
from acd.infrastructure.agents.registry import AgentRegistry
from acd.infrastructure.agents.task_scheduler import TaskScheduler
from acd.infrastructure.repositories.agents.agent_repository import AgentRepository
from acd.presentation.pages.base_page import BasePage
from acd.services.agents.supervisor_service import SupervisorService


class AgentConsolePage(BasePage):
    """Agent Console page for multi-agent platform visualization and control."""

    def __init__(self) -> None:
        super().__init__("Console de Agentes")

        # Initialize multi-agent infrastructure
        self.registry = AgentRegistry()
        self.message_bus = MessageBus()
        self.context_manager = ContextManager()
        self.task_scheduler = TaskScheduler()
        self.capability_service = CapabilityService()
        self.repository = AgentRepository()

        self.supervisor = SupervisorService(
            registry=self.registry,
            message_bus=self.message_bus,
            context_manager=self.context_manager,
            task_scheduler=self.task_scheduler,
            capability_service=self.capability_service,
            repository=self.repository,
        )

        self._current_session_id: int | None = None
        self.setup_ui()

    def setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("🤖 Multi-Agent Platform")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # Main content with tabs
        tabs = QTabWidget()

        # Tab 1: Supervisor Control
        supervisor_tab = self._create_supervisor_tab()
        tabs.addTab(supervisor_tab, "Supervisor")

        # Tab 2: Agents Status
        agents_tab = self._create_agents_tab()
        tabs.addTab(agents_tab, "Agents")

        # Tab 3: Task Queue
        tasks_tab = self._create_tasks_tab()
        tabs.addTab(tasks_tab, "Tasks")

        # Tab 4: Messages
        messages_tab = self._create_messages_tab()
        tabs.addTab(messages_tab, "Messages")

        layout.addWidget(tabs, stretch=1)

        self.setLayout(layout)

    def _create_supervisor_tab(self) -> QWidget:
        """Create supervisor control tab."""
        widget = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Status panel
        self.status_label = QLabel("Initializing multi-agent platform...")
        self.status_label.setStyleSheet("color: #666; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Control buttons
        buttons_layout = QHBoxLayout()

        init_btn = QPushButton("Initialize Platform")
        init_btn.setStyleSheet("background-color: #0066cc; color: white; padding: 8px;")
        init_btn.clicked.connect(self._on_initialize)
        buttons_layout.addWidget(init_btn)

        start_btn = QPushButton("Start Session")
        start_btn.setStyleSheet("background-color: #28a745; color: white; padding: 8px;")
        start_btn.clicked.connect(self._on_start_session)
        buttons_layout.addWidget(start_btn)

        end_btn = QPushButton("End Session")
        end_btn.setStyleSheet("background-color: #dc3545; color: white; padding: 8px;")
        end_btn.clicked.connect(self._on_end_session)
        buttons_layout.addWidget(end_btn)

        layout.addLayout(buttons_layout)

        # Supervisor info
        info_label = QLabel("Platform Information")
        info_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(info_label)

        self.supervisor_info = QTextEdit()
        self.supervisor_info.setReadOnly(True)
        self.supervisor_info.setMaximumHeight(250)
        layout.addWidget(self.supervisor_info)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_agents_tab(self) -> QWidget:
        """Create agents status tab."""
        widget = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        label = QLabel("Registered Agents")
        label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label)

        self.agents_list = QListWidget()
        layout.addWidget(self.agents_list)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_tasks_tab(self) -> QWidget:
        """Create task queue tab."""
        widget = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        label = QLabel("Task Queue and Execution")
        label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label)

        # Queue info
        self.queue_info = QLabel("Queue Size: 0 | Running: 0 | Completed: 0 | Failed: 0")
        layout.addWidget(self.queue_info)

        # Task list
        self.tasks_list = QListWidget()
        layout.addWidget(self.tasks_list)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_messages_tab(self) -> QWidget:
        """Create messages tab."""
        widget = QFrame()
        layout = QVBoxLayout()
        layout.setSpacing(12)

        label = QLabel("Message Bus Communication")
        label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(label)

        # Message input
        input_layout = QHBoxLayout()
        self.message_input = QTextEdit()
        self.message_input.setPlaceholderText("Enter user request...")
        self.message_input.setMaximumHeight(60)
        input_layout.addWidget(self.message_input)

        send_btn = QPushButton("Process")
        send_btn.setStyleSheet(
            "background-color: #0066cc; color: white; padding: 8px; width: 80px;"
        )
        send_btn.clicked.connect(self._on_process_request)
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        # Message display
        self.messages_list = QListWidget()
        layout.addWidget(self.messages_list)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _on_initialize(self) -> None:
        """Initialize platform."""
        result = initialize_multi_agent_platform(self.supervisor, self.registry)

        if result.get("success"):
            self.status_label.setText("✅ Platform initialized successfully")
            self._update_agents_list()
            self._update_supervisor_info()

    def _on_start_session(self) -> None:
        """Start session."""
        result = start_session(
            title="AI-Powered Job Search",
            user_objective="Find and apply for suitable positions",
            supervisor_service=self.supervisor,
        )

        if result.get("success"):
            self._current_session_id = result.get("session_id")
            self.status_label.setText(f"✅ Session started (ID: {self._current_session_id})")

    def _on_end_session(self) -> None:
        """End session."""
        if self._current_session_id:
            result = self.supervisor.end_session(self._current_session_id)
            if result.get("success"):
                self.status_label.setText("✅ Session ended")
                self._current_session_id = None

    def _on_process_request(self) -> None:
        """Process user request."""
        if not self._current_session_id:
            self.status_label.setText("❌ No active session")
            return

        request = self.message_input.toPlainText().strip()
        if not request:
            return

        self.message_input.clear()

        # Process request
        result = process_user_request(
            user_request=request,
            session_id=self._current_session_id,
            supervisor_service=self.supervisor,
        )

        if result.get("success"):
            # Add to message display
            msg_text = f"📤 User: {request}\n"
            msg_text += f"   → Agents involved: {result.get('agents_involved')}\n"
            msg_text += f"   → Tasks created: {len(result.get('tasks_created', []))}"

            item = QListWidgetItem(msg_text)
            self.messages_list.addItem(item)

            # Update task info
            self._update_queue_info()

    def _update_agents_list(self) -> None:
        """Update agents list display."""
        self.agents_list.clear()

        agents = self.registry.list_all_agents()
        for agent in agents:
            item_text = f"🤖 {agent['name']} ({agent['type']}) - {agent['status']}"
            item = QListWidgetItem(item_text)
            self.agents_list.addItem(item)

    def _update_supervisor_info(self) -> None:
        """Update supervisor info display."""
        status = self.supervisor.get_supervisor_status()

        info_text = f"Agents Registered: {status.get('agents_registered')}\n"
        info_text += f"Current Session: {status.get('current_session_id', 'None')}\n\n"

        scheduler_stats = status.get("scheduler_stats", {})
        info_text += f"Queue Size: {scheduler_stats.get('queue_size', 0)}\n"
        info_text += f"Running: {scheduler_stats.get('running_tasks', 0)}\n"
        info_text += f"Completed: {scheduler_stats.get('completed_tasks', 0)}\n"
        info_text += f"Failed: {scheduler_stats.get('failed_tasks', 0)}\n"
        info_text += f"Success Rate: {scheduler_stats.get('success_rate', 0):.1f}%"

        self.supervisor_info.setText(info_text)

    def _update_queue_info(self) -> None:
        """Update task queue info."""
        stats = self.task_scheduler.get_statistics()

        info_text = (
            f"Queue Size: {stats.get('queue_size', 0)} | "
            f"Running: {stats.get('running_tasks', 0)} | "
            f"Completed: {stats.get('completed_tasks', 0)} | "
            f"Failed: {stats.get('failed_tasks', 0)}"
        )

        self.queue_info.setText(info_text)
