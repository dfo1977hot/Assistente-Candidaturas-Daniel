"""Tests for SocialLink entity."""

from __future__ import annotations

from acd.domain.entities.social_link import SocialLink


def test_social_link_creation() -> None:
    """SocialLink should be instantiated."""

    social_link = SocialLink()

    assert social_link is not None


def test_social_link_assign_attributes() -> None:
    """SocialLink should store assigned attributes."""

    social_link = SocialLink(
        profile_id=1,
        name="LinkedIn",
        url="https://linkedin.com/in/johndoe",
    )

    assert social_link.profile_id == 1
    assert social_link.name == "LinkedIn"
    assert social_link.url == "https://linkedin.com/in/johndoe"


def test_social_link_repr_without_id() -> None:
    """repr should support transient objects."""

    social_link = SocialLink(
        name="GitHub",
        url="https://github.com/johndoe",
    )

    assert (
        repr(social_link)
        == "SocialLink(id=None, name='GitHub', url='https://github.com/johndoe')"
    )


def test_social_link_repr_with_id() -> None:
    """repr should expose identifier."""

    social_link = SocialLink(
        name="GitHub",
        url="https://github.com/johndoe",
    )

    social_link.id = 30

    assert (
        repr(social_link)
        == "SocialLink(id=30, name='GitHub', url='https://github.com/johndoe')"
    )