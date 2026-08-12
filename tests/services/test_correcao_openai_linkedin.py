from pathlib import Path


def test_linkedin_importer_uses_settings_api_key() -> None:
    source = Path("acd/services/linkedin_job_import_service.py").read_text(
        encoding="utf-8"
    )
    assert "from acd.services.settings_service import SettingsService" in source
    assert 'SettingsService().get_api_key("openai").strip()' in source
    assert '"Authorization": f"Bearer {api_key}"' in source
    assert "Verifique e teste a chave na página Configurações." in source
