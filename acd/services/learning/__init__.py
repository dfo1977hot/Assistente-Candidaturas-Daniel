"""Learning services package."""

from __future__ import annotations

from typing import Any

__all__ = [
    "LearningService",
    "ApprovalService",
    "KnowledgeReuseService",
]


def __getattr__(name: str) -> Any:
    """Lazy import of learning services.

    Avoids importing all services during package initialization,
    preventing circular imports and duplicate SQLAlchemy model
    registration while preserving the public API.
    """
    if name == "LearningService":
        from .learning_service import LearningService

        return LearningService

    if name == "ApprovalService":
        from .approval_service import ApprovalService

        return ApprovalService

    if name == "KnowledgeReuseService":
        from .knowledge_reuse_service import KnowledgeReuseService

        return KnowledgeReuseService

    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}"
    )