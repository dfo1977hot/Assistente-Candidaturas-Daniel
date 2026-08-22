from pathlib import Path


def test_linkedin_importer_uses_settings_configured_ai_provider() -> None:
    source = Path("acd/services/linkedin_job_import_service.py").read_text(
        encoding="utf-8"
    )

    assert (
        "from acd.infrastructure.ai.providers "
        "import AIProvider, SettingsConfiguredAIProvider"
        in source
    )
    assert "from acd.services.settings_service import SettingsService" in source
    assert "settings_service: SettingsService | None = None" in source
    assert "self._settings_service = settings_service or SettingsService()" in source
    assert "SettingsConfiguredAIProvider(" in source
    assert "self._settings_service" in source
    assert "Verifique e teste a chave na página Configurações." in source