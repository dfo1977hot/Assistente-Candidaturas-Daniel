from pathlib import Path


def test_company_lookup_uses_api_keys_saved_in_settings() -> None:
    source = Path("acd/services/company_lookup_service.py").read_text(
        encoding="utf-8"
    )
    assert "from acd.services.settings_service import SettingsService" in source
    assert 'settings.get_api_key("openai")' in source
    assert 'settings.get_api_key("google")' in source
    assert "settings_service=self.settings_service" in source


def test_composition_root_injects_settings_into_company_lookup() -> None:
    source = Path("acd/desktop_composition_root.py").read_text(encoding="utf-8")
    assert "CompanyLookupService(" in source
    assert "settings_service=settings_service" in source
