from __future__ import annotations

from acd.infrastructure.ai.providers import SettingsConfiguredAIProvider


class _Settings:
    def ai_provider_order(self) -> tuple[str, ...]:
        return ("ollama", "gemini", "openai")


class _FailingProvider:
    def __init__(self, _settings: object) -> None:
        pass

    def generate_text(self, **_kwargs: object) -> str:
        raise RuntimeError("indisponível")


class _WorkingProvider:
    def __init__(self, _settings: object) -> None:
        pass

    def generate_text(self, **_kwargs: object) -> str:
        return "resposta gratuita"


def test_configured_provider_falls_back_to_next_provider(monkeypatch) -> None:
    monkeypatch.setattr(
        SettingsConfiguredAIProvider,
        "_FACTORIES",
        {
            "ollama": _FailingProvider,
            "gemini": _WorkingProvider,
            "openai": _FailingProvider,
        },
    )

    provider = SettingsConfiguredAIProvider(_Settings())  # type: ignore[arg-type]

    result = provider.generate_text(
        prompt="teste",
        model="ignorado",
        temperature=0.2,
        max_tokens=100,
        language="pt-BR",
    )

    assert result == "resposta gratuita"
