"""Tests for Certification entity."""

from __future__ import annotations

from acd.domain.entities.certification import Certification


def test_certification_creation() -> None:
    """Certification should be instantiated."""

    certification = Certification()

    assert certification is not None


def test_certification_assign_attributes() -> None:
    """Certification should store assigned attributes."""

    certification = Certification(
        name="Lean Six Sigma Green Belt",
        description="Professional certification.",
    )

    assert certification.name == "Lean Six Sigma Green Belt"
    assert certification.description == "Professional certification."


def test_certification_repr_without_id() -> None:
    """repr should support transient objects."""

    certification = Certification(
        name="PMP",
    )

    assert (
        repr(certification)
        == "Certification(id=None, name='PMP')"
    )


def test_certification_repr_with_id() -> None:
    """repr should expose identifier."""

    certification = Certification(
        name="PMP",
    )

    certification.id = 8

    assert (
        repr(certification)
        == "Certification(id=8, name='PMP')"
    )