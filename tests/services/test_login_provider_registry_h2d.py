from __future__ import annotations

import pytest

from acd.services.login_provider_registry import LoginProviderRegistry


@pytest.fixture
def registry() -> LoginProviderRegistry:
    return LoginProviderRegistry()


@pytest.mark.parametrize(
    "url",
    (
        "https://empresa-a.gupy.io/jobs/12345",
        "https://empresa-b.gupy.io/candidates/signin",
        "https://portal.gupy.io/",
        "https://login.gupy.io/candidate",
        "empresa-c.gupy.io/jobs/987",
        "https://GUPY.IO/",
    ),
)
def test_identifies_gupy_from_changing_subdomains(
    registry: LoginProviderRegistry,
    url: str,
) -> None:
    provider = registry.identify(url)

    assert provider is not None
    assert provider.provider_id == "gupy"
    assert provider.display_name == "Gupy"


@pytest.mark.parametrize(
    "url",
    (
        "",
        "https://www.linkedin.com/jobs/view/123",
        "https://example.com/gupy.io/jobs/123",
        "https://notgupy.io/jobs/123",
    ),
)
def test_does_not_misclassify_unrelated_hosts(
    registry: LoginProviderRegistry,
    url: str,
) -> None:
    assert registry.identify(url) is None


def test_get_provider_by_stable_id(
    registry: LoginProviderRegistry,
) -> None:
    provider = registry.get("GUPY")

    assert provider is not None
    assert provider.provider_id == "gupy"


def test_lists_supported_providers(
    registry: LoginProviderRegistry,
) -> None:
    providers = registry.list_providers()

    assert tuple(
        provider.provider_id
        for provider in providers
    ) == ("gupy", "terra_imap")