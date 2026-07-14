"""Tests for CurriculumVersion entity."""

from __future__ import annotations

from acd.domain.entities.curriculum_version import CurriculumVersion


def test_curriculum_version_defaults() -> None:
    """CurriculumVersion should initialize without persisted defaults."""

    version = CurriculumVersion()

    assert version.file_name is None
    assert version.file_path is None
    assert version.file_type is None
    assert version.checksum is None


def test_curriculum_version_assign_attributes() -> None:
    """CurriculumVersion should store assigned attributes."""

    version = CurriculumVersion(
        curriculum_id=10,
        version="v2.1",
        file_name="curriculum_v2.docx",
        file_path="/curricula/curriculum_v2.docx",
        file_type="docx",
        checksum="ABC123XYZ",
    )

    assert version.curriculum_id == 10
    assert version.version == "v2.1"
    assert version.file_name == "curriculum_v2.docx"
    assert version.file_path == "/curricula/curriculum_v2.docx"
    assert version.file_type == "docx"
    assert version.checksum == "ABC123XYZ"


def test_curriculum_version_repr_without_id() -> None:
    """repr should support transient objects."""

    version = CurriculumVersion(version="v1.0")

    assert (
        repr(version)
        == "CurriculumVersion(id=None, version='v1.0')"
    )


def test_curriculum_version_repr_with_id() -> None:
    """repr should expose identifier."""

    version = CurriculumVersion(version="v3.0")
    version.id = 15

    assert (
        repr(version)
        == "CurriculumVersion(id=15, version='v3.0')"
    )


def test_curriculum_relationship_collection() -> None:
    """Relationship attribute should exist."""

    version = CurriculumVersion()

    assert version.curriculum is None