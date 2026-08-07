"""Safe structured generation implementations without a concrete external SDK."""

from __future__ import annotations

from acd.application.structured_resume_generation import (
    StructuredGenerationCapabilities,
    StructuredResumeGenerationPort,
    StructuredResumeProviderRequest,
    StructuredResumeProviderResult,
    StructuredResumeProviderStatus,
)


class UnsupportedStructuredResumeGenerationProvider(StructuredResumeGenerationPort):
    """Explicitly report that no configured provider supports native structured output."""

    def get_capabilities(self) -> StructuredGenerationCapabilities:
        """Return the absence of supported native structured generation."""
        return StructuredGenerationCapabilities(False, False, (), "unconfigured")

    def generate_structured_resume(
        self, request: StructuredResumeProviderRequest
    ) -> StructuredResumeProviderResult:
        """Return a functional unavailable result without attempting a network call."""
        del request
        return StructuredResumeProviderResult(
            StructuredResumeProviderStatus.UNSUPPORTED,
            provider_name="unconfigured",
            message="Nenhum provider com saída estruturada nativa está configurado.",
        )


class FakeStructuredResumeGenerationProvider(StructuredResumeGenerationPort):
    """Deterministic test double; it is never registered for production composition."""

    def __init__(
        self,
        result: StructuredResumeProviderResult,
        capabilities: StructuredGenerationCapabilities | None = None,
    ) -> None:
        self._result = result
        self._capabilities = capabilities or StructuredGenerationCapabilities(
            True, True, (1,), "fake", "fake-structured-model"
        )
        self.requests: list[StructuredResumeProviderRequest] = []

    def get_capabilities(self) -> StructuredGenerationCapabilities:
        """Return the configured deterministic capabilities."""
        return self._capabilities

    def generate_structured_resume(
        self, request: StructuredResumeProviderRequest
    ) -> StructuredResumeProviderResult:
        """Record exactly one structured request and return the configured result."""
        self.requests.append(request)
        return self._result
