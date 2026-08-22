from __future__ import annotations

import json
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from openai import OpenAI

from acd.services.settings_service import SettingsService


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
        web_search: bool = False,
    ) -> str: ...


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
        web_search: bool = False,
    ) -> str:
        del web_search
        return (
            f"Resposta mock do modelo {model} para o prompt '{prompt[:60]}' "
            f"em {language} com temperatura {temperature} e {max_tokens} tokens."
        )


class OllamaTextProvider:
    """Provedor textual local usando a API HTTP do Ollama."""

    def __init__(
        self,
        settings_service: SettingsService | None = None,
    ) -> None:
        self._settings_service = settings_service or SettingsService()

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
        web_search: bool = False,
    ) -> str:
        del model
        del language

        if web_search:
            raise RuntimeError(
                "O Ollama local não possui pesquisa web configurada para esta operação."
            )

        base_url = self._settings_service.ollama_base_url().rstrip("/")
        configured_model = self._settings_service.ai_model("ollama")

        payload = json.dumps(
            {
                "model": configured_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            }
        ).encode("utf-8")

        request = Request(
            f"{base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Ollama local indisponível em {base_url}: {exc}"
            ) from exc

        output_text = str(body.get("response", "") or "").strip()
        if not output_text:
            raise RuntimeError(
                "O Ollama não retornou conteúdo para a otimização do currículo."
            )
        return output_text


class GeminiTextProvider:
    """Provedor textual usando a Gemini API."""

    _BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(
        self,
        settings_service: SettingsService | None = None,
    ) -> None:
        self._settings_service = settings_service or SettingsService()

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
        web_search: bool = False,
    ) -> str:
        del model
        del language

        api_key = self._settings_service.get_api_key("gemini").strip()
        if not api_key:
            raise RuntimeError(
                "Chave do Gemini não configurada. "
                "Configure a chave em Configurações."
            )

        configured_model = self._settings_service.ai_model("gemini")
        model_path = quote(configured_model, safe="-._")
        endpoint = (
            f"{self._BASE_URL}/models/{model_path}:generateContent"
        )

        payload_body = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        if web_search:
            payload_body["tools"] = [{"google_search": {}}]
        payload = json.dumps(payload_body).encode("utf-8")

        request = Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": api_key,
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=120) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"Falha na Gemini API ({exc.code}): {detail}"
            ) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise RuntimeError(
                f"Não foi possível acessar a Gemini API: {exc}"
            ) from exc

        candidates = body.get("candidates") or []
        if not candidates:
            raise RuntimeError(
                "O Gemini não retornou candidatos de resposta."
            )

        parts = (
            candidates[0]
            .get("content", {})
            .get("parts", [])
        )
        output_text = "".join(
            str(part.get("text", "") or "")
            for part in parts
            if isinstance(part, dict)
        ).strip()

        if not output_text:
            raise RuntimeError(
                "O Gemini não retornou conteúdo para a otimização do currículo."
            )
        return output_text


class OpenAITextProvider:
    """Provedor textual produtivo usando a OpenAI Responses API."""

    def __init__(
        self,
        settings_service: SettingsService | None = None,
        *,
        model: str | None = None,
        client: OpenAI | None = None,
    ) -> None:
        self._settings_service = settings_service or SettingsService()
        self._api_key = self._settings_service.get_api_key("openai").strip()
        self._model = (
            model or self._settings_service.ai_model("openai")
        ).strip()
        self._client = client

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
        web_search: bool = False,
    ) -> str:
        del model
        del temperature
        del language

        if not self._api_key and self._client is None:
            raise RuntimeError(
                "Chave da OpenAI não configurada. "
                "Configure a chave em Configurações."
            )

        client = self._client or OpenAI(api_key=self._api_key)
        request_kwargs = {
            "model": self._model,
            "input": prompt,
            "max_output_tokens": max_tokens,
        }
        if web_search:
            request_kwargs["tools"] = [{"type": "web_search"}]
        response = client.responses.create(**request_kwargs)

        output_text = str(
            getattr(response, "output_text", "") or ""
        ).strip()
        if not output_text:
            raise RuntimeError(
                "A OpenAI não retornou conteúdo para a otimização do currículo."
            )
        return output_text


class SettingsConfiguredAIProvider:
    """Executa a cadeia de provedores configurada, com fallback automático."""

    _FACTORIES = {
        "ollama": OllamaTextProvider,
        "gemini": GeminiTextProvider,
        "openai": OpenAITextProvider,
    }

    def __init__(
        self,
        settings_service: SettingsService | None = None,
    ) -> None:
        self._settings_service = settings_service or SettingsService()

    def generate_text(
        self,
        *,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int,
        language: str,
        web_search: bool = False,
    ) -> str:
        errors: list[str] = []

        for provider_name in self._settings_service.ai_provider_order():
            factory = self._FACTORIES[provider_name]
            provider = factory(self._settings_service)
            try:
                return provider.generate_text(
                    prompt=prompt,
                    model=model,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    language=language,
                    web_search=web_search,
                )
            except Exception as exc:
                errors.append(
                    f"{provider_name}: {exc}"
                )

        raise RuntimeError(
            "Nenhum provedor de IA configurado conseguiu gerar a resposta. "
            + " | ".join(errors)
        )
