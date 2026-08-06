# Structured resume provider integration

No production structured provider is configured. `UnsupportedStructuredResumeGenerationProvider` is registered in composition and reports its capability explicitly without network access. `FakeStructuredResumeGenerationProvider` is a deterministic test double and is not registered for production.

A real adapter requires a separately approved SDK, secure environment-based configuration, native JSON Schema/structured-output enforcement, and tests without live network calls. It must implement the Application port and must not expose raw responses, headers, credentials, or chain-of-thought.
