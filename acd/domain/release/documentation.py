"""Documentation topic entity."""

from enum import Enum
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import DateTime, Text, JSON

from acd.models.base import Base


class DocumentationCategory(str, Enum):
    """Documentation categories."""

    GETTING_STARTED = "getting_started"
    INSTALLATION = "installation"
    CONFIGURATION = "configuration"
    USER_GUIDE = "user_guide"
    TROUBLESHOOTING = "troubleshooting"
    API_REFERENCE = "api_reference"
    FAQ = "faq"
    RELEASES = "releases"
    TUTORIALS = "tutorials"


class DocumentationTopic(Base):
    """Integrated documentation topics."""

    __tablename__ = "documentation_topics"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[str] = mapped_column(unique=True, index=True)  # getting_started_install
    title: Mapped[str]
    category: Mapped[str] = mapped_column(index=True)  # GETTING_STARTED, INSTALLATION, etc
    content: Mapped[str] = mapped_column(Text)  # Markdown format
    short_description: Mapped[str] = mapped_column(default="")
    keywords: Mapped[list[str]] = mapped_column(JSON, default=[])
    related_topics: Mapped[list[str]] = mapped_column(JSON, default=[])
    min_version: Mapped[str | None] = mapped_column(nullable=True)
    max_version: Mapped[str | None] = mapped_column(nullable=True)
    is_visible: Mapped[bool] = mapped_column(default=True, index=True)
    is_featured: Mapped[bool] = mapped_column(default=False)
    view_count: Mapped[int] = mapped_column(default=0)
    last_viewed: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.now,
        onupdate=datetime.now,
    )

    def is_relevant_for_version(self, version: str) -> bool:
        """Check if documentation is relevant for a version."""
        if self.min_version and version < self.min_version:
            return False
        if self.max_version and version > self.max_version:
            return False
        return self.is_visible

    def matches_search(self, query: str) -> bool:
        """Check if topic matches search query."""
        query_lower = query.lower()
        return (
            query_lower in self.title.lower()
            or query_lower in self.short_description.lower()
            or any(query_lower in kw.lower() for kw in self.keywords)
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "topic_id": self.topic_id,
            "title": self.title,
            "category": self.category,
            "short_description": self.short_description,
            "is_featured": self.is_featured,
            "view_count": self.view_count,
        }
