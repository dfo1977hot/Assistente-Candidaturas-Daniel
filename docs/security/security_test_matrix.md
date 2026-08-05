# Security test matrix

| Boundary | Positive | Rejection |
|---|---|---|
| secrets | synthetic allowlisted value | missing, unknown, control/oversized value |
| paths | normalized child of authorized root | traversal, absolute, UNC, drive, reserved/trailing/double extension |
| files | bounded DOCX/PDF/JSON/CSV/XML/image | bad signature, large input, unsafe XML/ZIP member |
| plugins | trusted root + allowlist + strict manifest | external root/name/entry point/manifest/unauthorized plugin |
| AI/network | strict response, HTTPS URL, timeout/retry bounds | prompt injection treated as data, invalid response/URL/config |
| observability | synthetic secret/control input | no secret/newline injection, bounded correlation ID, diagnostic allowlist |
| backup/restore | temporary verified SQLite | invalid external path/hash/schema/corruption |
| packaging | installed wheel works | no env, data, DB, logs, diagnostics, screenshots or Gate artifacts |

All sensitive fixtures are synthetic. No test opens the real database or makes
an external request.

