# Versioned structured resume snapshot

The v1 snapshot is an immutable `StructuredResumeSnapshot` with `schema_version`, identity, contact, summary, skills, experiences, education, certifications, courses, languages, projects, and additional sections. Collections are tuples in the Application contract.

The codec accepts JSON only when every required structural field and value type is valid. Unknown fields are rejected. Serialization is deterministic UTF-8 JSON and preserves Unicode and list order.

`EffectiveApplicationResumeUseCase` keeps textual resolution unchanged and supplies the optional snapshot from exactly the selected source: original curriculum or adopted `ResumeVersion`. It never parses text, merges sources, uses the visually selected version, or uses the latest version as a fallback.

The structured availability values are `AVAILABLE`, `UNAVAILABLE`, `INVALID`, and `UNSUPPORTED_SCHEMA`. `UNAVAILABLE` is the normal legacy state.
