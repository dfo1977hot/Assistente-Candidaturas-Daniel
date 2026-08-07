"""Tests for Language entity."""

from __future__ import annotations

from acd.domain.entities.language import Language


def test_language_defaults() -> None:
    """Language should initialize without persisted defaults."""

    language = Language()

    assert language.profile_id is None
    assert language.name is None
    assert language.proficiency is None


def test_language_assign_attributes() -> None:
    """Language should store assigned attributes."""

    language = Language(
        profile_id=1,
        name="English",
        proficiency="Advanced",
    )

    assert language.profile_id == 1
    assert language.name == "English"
    assert language.proficiency == "Advanced"