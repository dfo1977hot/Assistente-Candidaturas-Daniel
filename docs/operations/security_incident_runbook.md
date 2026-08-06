# Local security incident runbook

1. Stop the affected operation and disconnect networking if exfiltration is
   suspected; do not delete evidence or the database.
2. Record time, safe event/correlation IDs, application version and affected
   component. Never copy credentials, personal documents or raw logs into a
   ticket.
3. Revoke/rotate affected provider credentials outside ACD and restart the app.
4. Preserve relevant local files read-only; use the sanitized diagnostic export
   only. Back up SQLite through the verified lifecycle before recovery.
5. Disable plugins and external integrations. Do not execute received files.
6. Validate backup hash, manifest, integrity and schema before any restore.
7. Review sanitized logs for event types and error classes, not content.
8. After containment, document cause, scope, residual risk and a tested fix.

OS account compromise, malware, signed-plugin verification and provider-side
incidents require external operational response beyond this local runbook.

