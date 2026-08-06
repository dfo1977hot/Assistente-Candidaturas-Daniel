from __future__ import annotations

from acd.infrastructure.workflow.command import WorkflowCommand
from acd.infrastructure.workflow.command_dispatcher import (
    CommandDispatcher,
)


class DummyCommand(WorkflowCommand):
    """Dummy command used for dispatcher tests."""

    @classmethod
    def name(cls) -> str:
        return "dummy"

    def execute(self, context):
        return {"ok": True}

class ReplacementCommand(WorkflowCommand):
    """Replacement command used to validate overriding."""

    @classmethod
    def name(cls) -> str:
        return "replacement"

    def execute(self, context):
        return {"replacement": True}

def test_dispatcher_returns_builtin_command():
    """Dispatcher must instantiate built-in commands."""

    dispatcher = CommandDispatcher()

    command = dispatcher.dispatch("analyze_job")

    assert command is not None
    assert command.name() == "analyze_job"


def test_dispatcher_returns_none_for_unknown_command():
    """Unknown commands must return None."""

    dispatcher = CommandDispatcher()

    command = dispatcher.dispatch("unknown_command")

    assert command is None


def test_register_new_command():
    """Dispatcher must register new commands."""

    dispatcher = CommandDispatcher()

    dispatcher.register(
        "dummy",
        DummyCommand,
    )

    command = dispatcher.dispatch("dummy")

    assert command is not None
    assert isinstance(command, DummyCommand)


def test_register_normalizes_command_name():
    """Dispatcher must normalize command names."""

    dispatcher = CommandDispatcher()

    dispatcher.register(
        "  Dummy_Command  ",
        DummyCommand,
    )

    command = dispatcher.dispatch(
        "dummy_command",
    )

    assert isinstance(command, DummyCommand)


def test_dispatch_normalizes_lookup_name():
    """Dispatcher must normalize lookup names."""

    dispatcher = CommandDispatcher()

    dispatcher.register(
        "dummy",
        DummyCommand,
    )

    command = dispatcher.dispatch(
        "  DUMMY  ",
    )

    assert isinstance(command, DummyCommand)


def test_register_overrides_existing_command():
    """Register must replace an existing command."""

    dispatcher = CommandDispatcher()

    dispatcher.register(
        "analyze_job",
        ReplacementCommand,
    )

    command = dispatcher.dispatch("analyze_job")

    assert command is not None
    assert isinstance(command, ReplacementCommand)


def test_dispatch_returns_new_instance_every_time():
    """Dispatcher must instantiate a new command on each dispatch."""

    dispatcher = CommandDispatcher()

    dispatcher.register(
        "dummy",
        DummyCommand,
    )

    command1 = dispatcher.dispatch("dummy")
    command2 = dispatcher.dispatch("dummy")

    assert command1 is not command2