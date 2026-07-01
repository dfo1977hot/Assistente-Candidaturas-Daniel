# Handoff Template

Use este template para transferir execucao entre agentes.

## Markdown formato padrao
- From Agent:
- To Agent:
- Status: approved | blocked | needs_changes
- Score: 0-100
- Risk: very_low | low | medium | high
- Release Ready: YES | NO
- Summary:
- Blocking Issues:
- Required Actions:
- Evidence:
- Timestamp:

## JSON formato padrao
```json
{
  "from_agent": "Architecture",
  "to_agent": "Implementation",
  "status": "approved",
  "score": 98,
  "risk": "low",
  "release_ready": "YES",
  "summary": "Architecture gate approved",
  "blocking_issues": [],
  "required_actions": [],
  "evidence": [
    "docs/architecture/decisions/architecture-inventory-report.md"
  ],
  "timestamp": "2026-07-01T00:00:00Z"
}
```
