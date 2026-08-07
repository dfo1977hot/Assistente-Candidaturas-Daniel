# Event catalog

| Category | Stable events |
|---|---|
| application | `application.starting`, `application.started`, `application.shutdown`, `unhandled_exception` |
| database | `database.bootstrap.started/completed/failed`, `database.backup.started/completed/failed`, `database.restore.started/completed/rejected/failed` |
| task | `task.queued`, `task.started`, `task.completed`, `task.failed` |
| performance | `performance.queue.saturated` |
| workflow | `workflow.started`, `workflow.completed`, `workflow.failed` |
| diagnostics | `diagnostics.generated`, `diagnostics.exported` |

Names are technical contracts. Messages contain no domain object representation,
prompt, response, document content or personal identity. Durations are ms.
