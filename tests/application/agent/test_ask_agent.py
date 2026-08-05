from unittest.mock import MagicMock, patch

from acd.application.agent.ask_agent import ask_agent


def test_ask_agent_default_dependencies():
    """Should create all default dependencies."""

    analysis = {
        "intent": "search",
        "confidence": 0.95,
        "next_action": "answer",
    }

    repository = MagicMock()

    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = analysis
    orchestrator.context_builder.build.return_value = {}

    with (
        patch(
            "acd.application.agent.ask_agent.AgentRepository",
            return_value=repository,
        ),
        patch(
            "acd.application.agent.ask_agent.AgentMemoryService",
            return_value=memory_service,
        ) as memory_cls,
        patch(
            "acd.application.agent.ask_agent.DefaultToolRegistry",
            return_value=MagicMock(),
        ),
        patch(
            "acd.application.agent.ask_agent.AIOrchestrator",
            return_value=orchestrator,
        ) as orchestrator_cls,
    ):
        result = ask_agent("hello")

    memory_cls.assert_called_once_with(repository)
    orchestrator_cls.assert_called_once()

    memory_service.save_conversation.assert_called_once_with(
        "hello",
        "search",
    )

    assert result["success"] is True
    assert result["intent"] == "search"
    assert result["confidence"] == 0.95
    assert result["next_action"] == "answer"
    assert result["context_available"] is False
    assert result["analysis"] == analysis

def test_ask_agent_uses_provided_repository():
    """Uses the provided repository and only creates the missing dependencies."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "search",
        "confidence": 0.9,
        "next_action": "answer",
    }
    orchestrator.context_builder.build.return_value = {}

    with (
        patch(
            "acd.application.agent.ask_agent.AgentMemoryService",
            return_value=memory_service,
        ) as memory_cls,
        patch(
            "acd.application.agent.ask_agent.DefaultToolRegistry",
            return_value=MagicMock(),
        ),
        patch(
            "acd.application.agent.ask_agent.AIOrchestrator",
            return_value=orchestrator,
        ),
    ):
        ask_agent(
            "hello",
            repository=repository,
        )

    memory_cls.assert_called_once_with(repository)

def test_ask_agent_uses_provided_memory_service():
    """Does not instantiate AgentMemoryService when one is supplied."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "chat",
        "confidence": 1.0,
        "next_action": "respond",
    }
    orchestrator.context_builder.build.return_value = {}

    with (
        patch(
            "acd.application.agent.ask_agent.AgentMemoryService",
        ) as memory_cls,
        patch(
            "acd.application.agent.ask_agent.DefaultToolRegistry",
            return_value=MagicMock(),
        ),
        patch(
            "acd.application.agent.ask_agent.AIOrchestrator",
            return_value=orchestrator,
        ),
    ):
        ask_agent(
            "question",
            repository=repository,
            memory_service=memory_service,
        )

    memory_cls.assert_not_called()

    memory_service.save_conversation.assert_called_once_with(
        "question",
        "chat",
    )

def test_ask_agent_uses_provided_orchestrator():
    """Does not instantiate AIOrchestrator when one is supplied."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "plan",
        "confidence": 0.8,
        "next_action": "execute",
    }
    orchestrator.context_builder.build.return_value = {
        "memory": True,
    }

    result = ask_agent(
        "create plan",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    assert result["success"] is True
    assert result["intent"] == "plan"
    assert result["confidence"] == 0.8
    assert result["next_action"] == "execute"
    assert result["context_available"] is True


def test_ask_agent_defaults_to_unknown_intent():
    """Uses 'unknown' when the orchestrator does not return an intent."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {}
    orchestrator.context_builder.build.return_value = {}

    result = ask_agent(
        "question",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    memory_service.save_conversation.assert_called_once_with(
        "question",
        "unknown",
    )

    assert result["success"] is True
    assert result["intent"] is None
    assert result["confidence"] is None
    assert result["next_action"] is None
    assert result["context_available"] is False
    assert result["analysis"] == {}


def test_ask_agent_context_available_with_non_empty_context():
    """Returns context_available=True when the context builder returns data."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "analysis",
    }
    orchestrator.context_builder.build.return_value = {
        "history": ["item1"],
    }

    result = ask_agent(
        "question",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    assert result["context_available"] is True


def test_ask_agent_calls_dependencies_once():
    """Invokes each collaborator exactly once."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "chat",
    }
    orchestrator.context_builder.build.return_value = {}

    ask_agent(
        "hello",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    orchestrator.analyze_request.assert_called_once_with("hello")
    orchestrator.context_builder.build.assert_called_once_with()
    memory_service.save_conversation.assert_called_once_with(
        "hello",
        "chat",
    )


def test_ask_agent_creates_default_repository():
    """Creates a default AgentRepository when none is provided."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {"intent": "chat"}
    orchestrator.context_builder.build.return_value = {}

    with (
        patch(
            "acd.application.agent.ask_agent.AgentRepository",
            return_value=repository,
        ) as repository_cls,
        patch(
            "acd.application.agent.ask_agent.AgentMemoryService",
            return_value=memory_service,
        ),
        patch(
            "acd.application.agent.ask_agent.DefaultToolRegistry",
            return_value=MagicMock(),
        ),
        patch(
            "acd.application.agent.ask_agent.AIOrchestrator",
            return_value=orchestrator,
        ),
    ):
        ask_agent("hello")

    repository_cls.assert_called_once_with()


def test_ask_agent_creates_default_orchestrator():
    """Creates the default AIOrchestrator with a DefaultToolRegistry."""

    repository = MagicMock()
    memory_service = MagicMock()

    registry = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {"intent": "chat"}
    orchestrator.context_builder.build.return_value = {}

    with (
        patch(
            "acd.application.agent.ask_agent.DefaultToolRegistry",
            return_value=registry,
        ) as registry_cls,
        patch(
            "acd.application.agent.ask_agent.AIOrchestrator",
            return_value=orchestrator,
        ) as orchestrator_cls,
    ):
        ask_agent(
            "hello",
            repository=repository,
            memory_service=memory_service,
        )

    registry_cls.assert_called_once_with()
    orchestrator_cls.assert_called_once_with(tool_registry=registry)


def test_ask_agent_returns_complete_analysis_dictionary():
    """Returns the complete analysis dictionary unchanged."""

    repository = MagicMock()
    memory_service = MagicMock()

    analysis = {
        "intent": "analysis",
        "confidence": 0.73,
        "next_action": "continue",
        "custom_field": {"value": 123},
    }

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = analysis
    orchestrator.context_builder.build.return_value = {}

    result = ask_agent(
        "question",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    assert result["analysis"] is analysis


def test_ask_agent_returns_none_fields_when_analysis_contains_none():
    """Preserves None values returned by the orchestrator."""

    repository = MagicMock()
    memory_service = MagicMock()

    analysis = {
        "intent": None,
        "confidence": None,
        "next_action": None,
    }

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = analysis
    orchestrator.context_builder.build.return_value = {}

    result = ask_agent(
        "question",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    memory_service.save_conversation.assert_called_once_with(
        "question",
        None,
    )

    assert result["intent"] is None
    assert result["confidence"] is None
    assert result["next_action"] is None
    assert result["analysis"] == analysis


def test_ask_agent_context_available_for_non_empty_list():
    """Any non-empty context object should evaluate to True."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "chat",
    }
    orchestrator.context_builder.build.return_value = ["previous conversation"]

    result = ask_agent(
        "hello",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    assert result["context_available"] is True


def test_ask_agent_context_available_for_empty_list():
    """An empty context object should evaluate to False."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "chat",
    }
    orchestrator.context_builder.build.return_value = []

    result = ask_agent(
        "hello",
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    assert result["context_available"] is False


def test_ask_agent_passes_original_question_to_orchestrator():
    """The original user question must be forwarded unchanged."""

    repository = MagicMock()
    memory_service = MagicMock()

    orchestrator = MagicMock()
    orchestrator.analyze_request.return_value = {
        "intent": "analysis",
    }
    orchestrator.context_builder.build.return_value = {}

    question = "How can I optimize the production schedule?"

    ask_agent(
        question,
        repository=repository,
        memory_service=memory_service,
        orchestrator=orchestrator,
    )

    orchestrator.analyze_request.assert_called_once_with(question)