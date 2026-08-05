# Structured resume generation provider contract

`StructuredResumeGenerationPort` is separate from the textual AI provider. Its request contains a validated source snapshot, an Application-safe vacancy DTO, guidance, and language. Its immutable result contains only an explicit status, optional snapshot, safe explanation, and safe provider identifiers.

Generation eligibility requires a source snapshot, native structured-output support, JSON Schema support, and schema version 1 support. A legacy `ResumeContext` remains valid for textual flows but is not eligible for structured generation.

No method in this contract calls `generate_text`, parses arbitrary text, repairs JSON, persists a version, or adopts a generated version.
