from acd.services.login_provider_registry import LoginProviderRegistry


def test_registry_lists_terra_imap_without_matching_vacancy_urls() -> None:
    registry = LoginProviderRegistry()
    provider = registry.get("terra_imap")

    assert provider is not None
    assert provider.display_name == "Terra IMAP"
    assert provider.domains == ()
    assert registry.identify("https://renner.gupy.io/jobs/123").provider_id == "gupy"
