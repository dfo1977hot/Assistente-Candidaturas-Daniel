"""Tests for Profile entity."""

from __future__ import annotations

from acd.domain.entities.profile import Profile


def test_profile_defaults() -> None:
    """Profile should initialize without persisted defaults."""

    profile = Profile()

    assert profile.full_name is None
    assert profile.preferred_name is None
    assert profile.email is None
    assert profile.phone is None
    assert profile.linkedin_url is None
    assert profile.github_url is None
    assert profile.portfolio_url is None
    assert profile.summary is None
    assert profile.location is None


def test_profile_assign_attributes() -> None:
    """Profile should store assigned attributes."""

    profile = Profile(
        full_name="Daniel Freitas Oliveira",
        preferred_name="Daniel",
        email="daniel@email.com",
        phone="11999999999",
        linkedin_url="https://linkedin.com/in/danielfreitas",
        github_url="https://github.com/danielfreitas",
        portfolio_url="https://portfolio.com/daniel",
        summary="Engenheiro de Produção com experiência em Supply Chain.",
        location="Guarulhos/SP",
    )

    assert profile.full_name == "Daniel Freitas Oliveira"
    assert profile.preferred_name == "Daniel"
    assert profile.email == "daniel@email.com"
    assert profile.phone == "11999999999"
    assert profile.linkedin_url == "https://linkedin.com/in/danielfreitas"
    assert profile.github_url == "https://github.com/danielfreitas"
    assert profile.portfolio_url == "https://portfolio.com/daniel"
    assert (
        profile.summary
        == "Engenheiro de Produção com experiência em Supply Chain."
    )
    assert profile.location == "Guarulhos/SP"


def test_profile_repr_without_id() -> None:
    """repr should support transient objects."""

    profile = Profile(
        full_name="Daniel Freitas Oliveira",
        email="daniel@email.com",
    )

    assert (
        repr(profile)
        == "Profile(id=None, full_name='Daniel Freitas Oliveira', "
        "email='daniel@email.com')"
    )


def test_profile_repr_with_id() -> None:
    """repr should expose identifier."""

    profile = Profile(
        full_name="Daniel Freitas Oliveira",
        email="daniel@email.com",
    )

    profile.id = 7

    assert (
        repr(profile)
        == "Profile(id=7, full_name='Daniel Freitas Oliveira', "
        "email='daniel@email.com')"
    )