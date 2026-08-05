# ADR-022: OpenAI Structured Resume Provider

## Status

Accepted.

## Context

ADR-021 established an application-owned port for native structured resume
generation but intentionally left production composition unconfigured. ACD
needs an optional concrete provider while preserving the absence-of-provider
behavior for local development and installations without credentials.

## Decision

Infrastructure provides an OpenAI adapter using the official Python SDK's
Responses API typed parsing interface. Pydantic response models are confined to
Infrastructure and map through `StructuredResumeSnapshotCodec` before an
application result is returned. Required API key and model configuration is
read from the environment; missing or invalid configuration selects the existing
unsupported provider in the composition root.

## Consequences

The Application layer remains provider-neutral and owns the output contract.
No resume version, database record, adoption decision, UI state, or document is
created by the provider. Installations that opt in must supply an explicit model
and protect the API key. A future generation use case can use the port without
changing this boundary.
