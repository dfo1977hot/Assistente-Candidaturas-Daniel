from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_settings_page_has_requested_sections() -> None:
    source = _read("acd/presentation/pages/settings_page.py")

    assert 'QGroupBox("Inicialização")' in source
    assert 'QGroupBox("Navegador e automações")' in source
    assert 'QGroupBox("APIs e Inteligência Artificial")' in source
    assert 'QGroupBox("Cofre de Logins")' in source
    assert 'QGroupBox("Diagnóstico e sugestões")' in source
    assert '"OpenAI API Key"' in source
    assert '"Google API Key"' in source
    assert '"Testar OpenAI"' in source
    assert "Executar importação e detecção de links do LinkedIn em segundo plano" in source


def test_main_window_uses_configured_startup_mode() -> None:
    source = _read("acd/ui/main_window.py")

    assert 'self._settings_service.startup_mode() == "minimized"' in source
    assert "self.showMinimized" in source
    assert "self.showMaximized" in source
