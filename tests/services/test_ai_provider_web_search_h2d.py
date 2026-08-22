import json

import pytest

from acd.infrastructure.ai import providers as module


class _Settings:
    def ai_provider_order(self) -> tuple[str, ...]:
        return ("ollama", "gemini", "openai")

    def ollama_base_url(self) -> str:
        return "http://localhost:11434"

    def ai_model(self, provider: str) -> str:
        return {"ollama": "qwen3:8b", "gemini": "gemini-3.6-flash", "openai": "gpt-5-mini"}[provider]

    def get_api_key(self, provider: str) -> str:
        return "key" if provider in {"gemini", "openai"} else ""


def test_ollama_web_search_declines_capability() -> None:
    provider = module.OllamaTextProvider(_Settings())
    with pytest.raises(RuntimeError, match="não possui pesquisa web"):
        provider.generate_text(
            prompt="x", model="x", temperature=0, max_tokens=10, language="pt-BR", web_search=True
        )


def test_gemini_web_search_adds_google_search_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}

    class _Response:
        def read(self) -> bytes:
            return json.dumps({"candidates": [{"content": {"parts": [{"text": "ok"}]}}]}).encode()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False

    def fake_urlopen(request, timeout=0):
        captured["body"] = json.loads(request.data.decode())
        return _Response()

    monkeypatch.setattr(module, "urlopen", fake_urlopen)
    provider = module.GeminiTextProvider(_Settings())
    assert provider.generate_text(
        prompt="x", model="x", temperature=0, max_tokens=10, language="pt-BR", web_search=True
    ) == "ok"
    assert captured["body"]["tools"] == [{"google_search": {}}]
