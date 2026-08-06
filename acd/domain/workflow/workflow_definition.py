"""Domain model for declarative workflow definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from acd.domain.workflow.workflow_stage import WorkflowStep


class WorkflowCategory(StrEnum):
    """Business categories supported by workflow definitions."""

    APPLICATION = "application"
    INTERVIEW = "interview"
    CAREER = "career"
    RESUME = "resume"
    ATS = "ats"
    CUSTOM = "custom"


@dataclass(frozen=True)
class WorkflowDefinition:
    """Describes the business structure of a workflow without executing it."""

    workflow_id: str
    name: str
    description: str
    version: str
    category: WorkflowCategory
    steps: tuple[str | WorkflowStep, ...]
    dependencies: dict[str, tuple[str, ...]] = field(default_factory=dict)
    events: tuple[str, ...] = ()
    conditions: dict[str, str] = field(default_factory=dict)
