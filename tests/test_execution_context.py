from __future__ import annotations

from acd.domain.workflow.execution_context import ExecutionContext


def test_context_creation():
    """ExecutionContext should initialize correctly."""

    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=2,
    )

    assert context.workflow_execution_id == 1
    assert context.workflow_id == 2
    assert context.application_id is None
    assert context.job_id is None
    assert context.profile_id is None
    assert context.current_step == 0
    assert context.data == {}
    assert context.errors == []


def test_set_and_get_data():
    """Context should store arbitrary values."""

    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    context.set_data("answer", 42)

    assert context.get_data("answer") == 42


def test_get_data_returns_default():
    """Unknown keys should return the provided default."""

    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    assert context.get_data("missing") is None
    assert context.get_data("missing", "default") == "default"


def test_set_data_overwrites_previous_value():
    """set_data should overwrite existing values."""

    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    context.set_data("key", "A")
    context.set_data("key", "B")

    assert context.get_data("key") == "B"


def test_add_error():
    """Errors should be accumulated."""

    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    context.add_error("Error 1")
    context.add_error("Error 2")

    assert context.errors == [
        "Error 1",
        "Error 2",
    ]


def test_multiple_data_entries():
    """Context should store multiple values."""

    context = ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )

    context.set_data("a", 1)
    context.set_data("b", 2)
    context.set_data("c", 3)

    assert context.data == {
        "a": 1,
        "b": 2,
        "c": 3,
    }


def test_optional_fields():
    """Optional identifiers should be preserved."""

    context = ExecutionContext(
        workflow_execution_id=10,
        workflow_id=20,
        application_id=30,
        job_id=40,
        profile_id=50,
        current_step=3,
    )

    assert context.application_id == 30
    assert context.job_id == 40
    assert context.profile_id == 50
    assert context.current_step == 3