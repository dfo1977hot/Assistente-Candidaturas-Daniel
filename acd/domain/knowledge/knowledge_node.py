"""Domain projection for a node in the knowledge graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class KnowledgeNodeType(StrEnum):
    """Entity types represented by the knowledge graph."""

    CANDIDATE = "candidate"
    COMPANY = "company"
    JOB = "job"
    RESUME = "resume"
    RESUME_VERSION = "resume_version"
    SKILL = "skill"
    CERTIFICATION = "certification"
    LANGUAGE = "language"
    INTERVIEW = "interview"
    PLATFORM = "platform"
    CAREER_GOAL = "career_goal"
    LEARNING = "learning"
    DOCUMENT = "document"


@dataclass(frozen=True)
class KnowledgeNode:
    """Versioned semantic projection of an ACD domain entity."""

    node_id: str
    node_type: KnowledgeNodeType
    attributes: dict[str, Any] = field(default_factory=dict)
    version: int = 1
