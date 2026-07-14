"""Tests for Curriculum entity."""

from __future__ import annotations

from acd.domain.entities.curriculum import Curriculum


def test_curriculum_defaults() -> None:
    """Curriculum should initialize without persisted defaults."""

    curriculum = Curriculum()

    assert curriculum.name is None
    assert curriculum.description is None
    assert curriculum.version is None
    assert curriculum.language is None
    assert curriculum.is_default is None
    assert curriculum.status is None


def test_curriculum_assign_attributes() -> None:
    """Curriculum should store assigned attributes."""

    curriculum = Curriculum(
        name="Currículo Principal",
        description="Versão utilizada para vagas de logística.",
        version="v2.1",
        language="pt-BR",
        is_default=True,
        status="Ativo",
    )

    assert curriculum.name == "Currículo Principal"
    assert curriculum.description == (
        "Versão utilizada para vagas de logística."
    )
    assert curriculum.version == "v2.1"
    assert curriculum.language == "pt-BR"
    assert curriculum.is_default is True
    assert curriculum.status == "Ativo"


def test_curriculum_versions_relationship_defaults() -> None:
    """Relationship collection should be available."""

    curriculum = Curriculum()

    assert curriculum.versions is not None
    assert isinstance(curriculum.versions, list)
    assert len(curriculum.versions) == 0


def test_curriculum_repr_without_id() -> None:
    """repr should support transient objects."""

    curriculum = Curriculum(
        name="Currículo",
        version="v1.0",
    )

    assert (
        repr(curriculum)
        == "Curriculum(id=None, name='Currículo', version='v1.0')"
    )


def test_curriculum_repr_with_id() -> None:
    """repr should expose identifier."""

    curriculum = Curriculum(
        name="Currículo",
        version="v2.0",
    )

    curriculum.id = 15

    assert (
        repr(curriculum)
        == "Curriculum(id=15, name='Currículo', version='v2.0')"
    )