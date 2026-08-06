# Security governance

Sprint I defines local trust boundaries for secrets, external inputs,
filesystem access, plugins, network calls and AI integrations. Security is
deny-by-default at external boundaries, produces safe typed errors and never
claims process isolation that the desktop application does not provide.

The productive flow is: external input -> validation and normalization ->
authorized application operation -> controlled infrastructure -> sanitized
result -> sanitized observability/audit. No external telemetry is introduced.

