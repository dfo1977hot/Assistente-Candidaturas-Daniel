# MVP Operational Flow

This document maps the real productive flow currently available in the desktop runtime.

## Scope

- Productive runtime: desktop launcher, main window, sidebar, dashboard, and the official CRUD pages.
- Non-productive or absent surfaces: contact management, legacy wizard, facade-based flow, kernel/container runtime, and agent tasks as MVP work items.

## Flow matrix

| Etapa | Página | Serviço | Repository | Tabela | Persistência | Status |
|---|---|---|---|---|---|---|
| Start app | `app.py` / desktop | `DatabaseBootstrap` | n/a | SQLite schema | yes | funcional |
| Open dashboard | `Dashboard` | `CompanyService`, `JobService`, `ApplicationService`, `InterviewService`, `CurriculumService` | respective repositories | `companies`, `jobs`, `applications`, `interviews`, `curricula` | yes | funcional |
| Create company | `CompanyPage` | `CompanyService` | `CompanyRepository` | `companies` | yes | funcional |
| Create contact | n/a | n/a | n/a | n/a | no | ausente |
| Create vacancy | `JobPage` | `JobService` | `JobRepository` | `jobs` | yes | funcional |
| Create curriculum | `CurriculumPage` | `CurriculumService` | `CurriculumRepository` | `curricula`, `resume_versions` | yes | funcional |
| Create application | `ApplicationPage` | `ApplicationService` | `ApplicationRepository` | `applications`, `timeline_events` | yes | funcional |
| Change status and history | `ApplicationPage` | `ApplicationService` | `ApplicationRepository` | `applications`, `timeline_events` | yes | funcional |
| Create interview | `InterviewPage` | `InterviewService` | `InterviewRepository` | `interviews`, `timeline_events` | yes | funcional |
| Search and filter | all list pages | page-specific services | page-specific repositories | respective tables | yes | funcional |
| Backup and restore | lifecycle contract | `SQLiteDatabaseLifecycle` | file-backed SQLite | database file | yes | funcional |
| Reopen and recover | launcher + pages | productive services | productive repositories | same database file | yes | funcional |

## Notes

- The MVP currently covers companies, vacancies, curricula, applications, interviews, dashboard metrics, search, filtering, persistence, backup, restore, and reopen.
- Contact is intentionally recorded as absent rather than assumed.
- Tasks and other agent-console features remain outside the productive MVP flow.
