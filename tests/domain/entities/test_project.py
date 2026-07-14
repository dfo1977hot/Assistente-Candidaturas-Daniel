"""Tests for Project entity."""

from __future__ import annotations

from acd.domain.entities.project import Project


def test_project_creation() -> None:
    """Project should be instantiated."""

    project = Project()

    assert project is not None


def test_project_assign_attributes() -> None:
    """Project should store assigned attributes."""

    project = Project(
        profile_id=1,
        name="Assistente de Candidaturas do Daniel",
        description="Sistema para automação de candidaturas.",
        url="https://github.com/danielfreitas/acd",
    )

    assert project.profile_id == 1
    assert project.name == "Assistente de Candidaturas do Daniel"
    assert (
        project.description
        == "Sistema para automação de candidaturas."
    )
    assert project.url == "https://github.com/danielfreitas/acd"


def test_project_repr_without_id() -> None:
    """repr should support transient objects."""

    project = Project(
        name="Projeto ACD",
    )

    assert (
        repr(project)
        == "Project(id=None, name='Projeto ACD')"
    )


def test_project_repr_with_id() -> None:
    """repr should expose identifier."""

    project = Project(
        name="Projeto ACD",
    )

    project.id = 42

    assert (
        repr(project)
        == "Project(id=42, name='Projeto ACD')"
    )