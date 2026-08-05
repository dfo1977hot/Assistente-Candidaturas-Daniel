# Performance test matrix

| Concern | Evidence | Enforcement |
|---|---|---|
| cold import/no CWD side effect | fresh subprocess samples | tolerant budget |
| bootstrap | new/existing temporary DB, 92 tables | tolerant budget |
| initial UI | Sidebar/ApplicationPage | tolerant budget |
| event loop/cancel | active worker and Qt processing | invariant/budget |
| queue/backpressure | capacity/depth/rejection/event | invariant |
| query count | 50 applications and relations | exactly one statement |
| memory/resources | ten widget cycles and teardown | coarse ceiling |
| backup/restore | temporary full-schema DB | tolerant budget |
| OpenAI/plugin | fake/synthetic boundaries | tolerant budget |
| package boundary | architecture checks | invariant |

