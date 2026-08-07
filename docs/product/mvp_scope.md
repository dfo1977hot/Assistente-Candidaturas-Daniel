# MVP Scope

## Mandatory for MVP

| Feature | Classification | Notes |
|---|---|---|
| Dashboard | obrigatoria para MVP | KPI cards and refresh are part of the productive shell |
| Company CRUD | obrigatoria para MVP | first-class entity |
| Vacancy CRUD | obrigatoria para MVP | first-class entity |
| Curriculum CRUD and versioning | obrigatoria para MVP | base curriculum flow exists |
| Application CRUD | obrigatoria para MVP | official candidacy page |
| Status transitions and history | obrigatoria para MVP | validated by `ApplicationService` |
| Interview CRUD | obrigatoria para MVP | first-class entity |
| Search, filters, and ordering | obrigatoria para MVP | present on list pages |
| Persistence and reopen | obrigatoria para MVP | data must survive restart |
| Backup and restore | obrigatoria para MVP | governed by SQLite lifecycle contract |

## Desired

| Feature | Classification | Notes |
|---|---|---|
| Delete operations | desejável | supported on most current pages |
| Curriculum activation / duplication | desejável | available, but not required for first use |
| Candidate decision panels | desejável | useful for the application flow, but not required to accept the MVP |

## Post-MVP

| Feature | Classification | Notes |
|---|---|---|
| Tasks in agent console | pós-MVP | not part of the official productive workflow |
| Analytics expansion | pós-MVP | outside the acceptance scope |
| Assistant and agent tooling | pós-MVP | useful, but not required for MVP acceptance |

## Experimental or out of scope

| Feature | Classification | Notes |
|---|---|---|
| Contact management | fora de escopo / ausente | no first-class page, service, or repository exists |
| Legacy wizard flow | experimental | not registered in the productive runtime |
| Facade-based application flow | experimental | not part of the official route map |
| Kernel / bootstrap legacy runtime | fora de escopo | intentionally excluded from desktop composition |
