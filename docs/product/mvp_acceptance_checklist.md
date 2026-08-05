# MVP Acceptance Checklist

| Item | Expected | Evidence | Status |
|---|---|---|---|
| First run starts on an isolated database | productive DB is created in the isolated workspace | ✓ test_mvp_first_run.py | passed |
| Dashboard opens with empty KPIs | all counters show zero before seeding | ✓ test_mvp_first_run.py | passed |
| Company can be created and reopened | company persists after restart | ✓ test_mvp_workflow_and_persistence.py | passed |
| Vacancy can be created and reopened | vacancy persists after restart | ✓ test_mvp_workflow_and_persistence.py | passed |
| Curriculum can be created and reopened | curriculum and versions persist | ✓ test_mvp_workflow_and_persistence.py | passed |
| Application can be created and reopened | application persists after restart | ✓ test_mvp_workflow_and_persistence.py | passed |
| Status can be changed and history is recorded | valid transition succeeds, invalid one fails | ✓ test_mvp_workflow_and_persistence.py | passed |
| Interview can be created and reopened | interview persists after restart | ✓ test_mvp_workflow_and_persistence.py | passed |
| Search and filters work on list pages | filtered tables show the expected rows | ✓ test_mvp_workflow_and_persistence.py | passed |
| Backup is created with metadata | backup manifest and hash are valid | ✓ test_mvp_backup_restore.py | passed |
| Restore reopens the same data set | restored workspace matches the source | ✓ test_mvp_backup_restore.py | passed |
| Contact flow is not promised as MVP | documented as absent or out of scope | ✓ mvp_scope.md | classified as absent |

