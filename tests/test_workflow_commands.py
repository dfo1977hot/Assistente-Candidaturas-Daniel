from __future__ import annotations

import pytest

from acd.domain.workflow.execution_context import ExecutionContext
from acd.infrastructure.workflow.commands import (
    AnalyzeJobCommand,
    ApplyToJobCommand,
    GenerateCoverLetterCommand,
    GenerateResumeCommand,
    RegisterApplicationCommand,
    RunATSCommand,
)


@pytest.fixture
def context() -> ExecutionContext:
    """Execution context used by command tests."""

    return ExecutionContext(
        workflow_execution_id=1,
        workflow_id=1,
    )


def test_analyze_job_command(context: ExecutionContext):
    """AnalyzeJobCommand should analyze a job."""

    command = AnalyzeJobCommand()

    result = command.execute(context)

    assert command.name() == "analyze_job"
    assert result["status"] == "success"
    assert context.get_data("job_analysis") == {
        "analyzed": True,
    }


def test_generate_resume_command(context: ExecutionContext):
    """GenerateResumeCommand should generate a resume."""

    command = GenerateResumeCommand()

    result = command.execute(context)

    assert command.name() == "generate_resume"
    assert result["status"] == "success"
    assert context.get_data("resume") == {
        "generated": True,
    }


def test_generate_cover_letter_command(context: ExecutionContext):
    """GenerateCoverLetterCommand should generate a cover letter."""

    command = GenerateCoverLetterCommand()

    result = command.execute(context)

    assert command.name() == "generate_cover_letter"
    assert result["status"] == "success"
    assert context.get_data("cover_letter") == {
        "generated": True,
    }


def test_run_ats_command(context: ExecutionContext):
    """RunATSCommand should generate an ATS score."""

    command = RunATSCommand()

    result = command.execute(context)

    assert command.name() == "run_ats"
    assert result["status"] == "success"
    assert context.get_data("ats_score") == {
        "score": 85,
    }


def test_apply_to_job_command(context: ExecutionContext):
    """ApplyToJobCommand should submit an application."""

    command = ApplyToJobCommand()

    result = command.execute(context)

    assert command.name() == "apply_to_job"
    assert result["status"] == "success"
    assert context.get_data("application") == {
        "applied": True,
    }


def test_register_application_command(context: ExecutionContext):
    """RegisterApplicationCommand should register an application."""

    command = RegisterApplicationCommand()

    result = command.execute(context)

    assert command.name() == "register_application"
    assert result["status"] == "success"
    assert context.get_data("crm_registered") is True


@pytest.mark.parametrize(
    ("command_class", "expected_name"),
    [
        (AnalyzeJobCommand, "analyze_job"),
        (GenerateResumeCommand, "generate_resume"),
        (GenerateCoverLetterCommand, "generate_cover_letter"),
        (RunATSCommand, "run_ats"),
        (ApplyToJobCommand, "apply_to_job"),
        (RegisterApplicationCommand, "register_application"),
    ],
)
def test_command_names_are_unique(command_class, expected_name):
    """Each command should expose its canonical name."""

    command = command_class()

    assert command.name() == expected_name