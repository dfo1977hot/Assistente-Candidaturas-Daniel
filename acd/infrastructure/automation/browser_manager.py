from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BrowserManager:
    """Gerencia configuração básica do navegador para automação."""

    browser: str = "chromium"
    headless: bool = True
    timeout: int = 30000
    downloads_dir: str = "data/automation/downloads"
    screenshots_dir: str = "data/automation/screenshots"

    def create_context(self, *, headless: bool | None = None) -> dict[str, object]:
        """Cria um contexto de execução com opções básicas."""
        return {
            "browser": self.browser,
            "headless": headless if headless is not None else self.headless,
            "timeout": self.timeout,
            "downloads_dir": self.downloads_dir,
            "screenshots_dir": self.screenshots_dir,
        }
