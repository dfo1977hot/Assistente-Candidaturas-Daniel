# OpenAI Structured Resume Provider

The concrete provider is an Infrastructure adapter for
`StructuredResumeGenerationPort`. It uses the official OpenAI Python SDK and
the Responses API `responses.parse` method with an Infrastructure-only
Pydantic response model. The application receives only the existing
`StructuredResumeSnapshot` after validation by `StructuredResumeSnapshotCodec`.

## Configuration

Set the following environment variables in the process that starts ACD:

| Variable | Required | Description |
| --- | --- | --- |
| `OPENAI_API_KEY` | Yes | API credential. Never store it in source control or logs. |
| `OPENAI_MODEL` | Yes | Explicit model identifier. There is no hard-coded default. |
| `OPENAI_TIMEOUT_SECONDS` | No | Positive request timeout; defaults to `30`. |
| `OPENAI_MAX_RETRIES` | No | Non-negative SDK retry count; defaults to `1`. |
| `OPENAI_BASE_URL` | No | Optional compatible OpenAI endpoint. |

If either required variable is absent or invalid, composition registers
`UnsupportedStructuredResumeGenerationProvider`; the desktop still starts and
no network call is attempted. The provider reports capabilities without probe
requests and does not persist, create versions, or render DOCX files.

## Operational behavior

The adapter passes timeout and retry settings to the SDK client, keeps the API
key out of diagnostics, and maps timeouts, authentication, provider failures,
refusals, incomplete results, and invalid parsed payloads to the existing
application result status. The only supported provider output is the typed
structured response; arbitrary text output is never parsed or repaired.
