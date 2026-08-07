"""Tests for Publication entity."""

from __future__ import annotations

from acd.domain.entities.publication import Publication


def test_publication_creation() -> None:
    """Publication should be instantiated."""

    publication = Publication()

    assert publication is not None


def test_publication_assign_attributes() -> None:
    """Publication should store assigned attributes."""

    publication = Publication(
        profile_id=1,
        title="Improving Supply Chain Performance",
        url="https://doi.org/10.1000/example",
        description="Scientific publication about logistics optimization.",
    )

    assert publication.profile_id == 1
    assert publication.title == "Improving Supply Chain Performance"
    assert publication.url == "https://doi.org/10.1000/example"
    assert (
        publication.description
        == "Scientific publication about logistics optimization."
    )


def test_publication_repr_without_id() -> None:
    """repr should support transient objects."""

    publication = Publication(
        title="Lean Manufacturing",
    )

    assert (
        repr(publication)
        == "Publication(id=None, title='Lean Manufacturing')"
    )


def test_publication_repr_with_id() -> None:
    """repr should expose identifier."""

    publication = Publication(
        title="Lean Manufacturing",
    )

    publication.id = 21

    assert (
        repr(publication)
        == "Publication(id=21, title='Lean Manufacturing')"
    )