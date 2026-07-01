from __future__ import annotations

from typing import Protocol


class AIProvider(Protocol):
    """Abstração para provedores de IA."""

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
    ) -> str:
        ...


class MockAIProvider:
    """Provedor mock para desenvolvimento e testes."""

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
    ) -> str:
        return (
            f"Resposta mock do modelo {model} para o prompt '{prompt[:60]}' "
            f"em {language} com temperatura {temperature} e {max_tokens} tokens."
        )
