from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_settings_page_has_requested_sections() -> None:
    source = _read("acd/presentation/pages/settings_page.py")

    assert '"Inicialização"' in source
    assert '"Navegador e automações"' in source
    assert '"APIs e Inteligência Artificial"' in source
    assert '"Cofre de Logins"' in source
    assert '"Diagnóstico e sugestões"' in source


def test_main_window_uses_configured_startup_mode() -> None:
    source = _read("acd/ui/main_window.py")

    assert 'self._settings_service.startup_mode() == "minimized"' in source
    assert "self.showMinimized" in source
    assert "self.showMaximized" in source


def test_settings_page_has_imap_fields_in_login_vault() -> None:
    source = _read("acd/presentation/pages/settings_page.py")

    assert '"Servidor IMAP"' in source
    assert '"Porta IMAP"' in source
    assert '"Segurança IMAP"' in source
    assert '"Pasta IMAP"' in source
    assert '"Timeout"' in source
    assert '"Testar IMAP"' in source
    assert '"dfo1977@terra.com.br"' in source


def test_settings_page_configures_multi_provider_ai() -> None:
    source = _read("acd/presentation/pages/settings_page.py")

    assert '"Ollama → Gemini → OpenAI"' in source
    assert '"Gemini API Key"' in source
    assert '"OpenAI API Key"' in source
    assert '"Ollama URL"' in source
    assert '"Modelo Ollama"' in source
    assert '"Modelo Gemini"' in source
    assert '"Modelo OpenAI"' in source
    assert '"Testar Ollama"' in source
    assert '"Testar Gemini"' in source
    assert '"Testar OpenAI"' in source
