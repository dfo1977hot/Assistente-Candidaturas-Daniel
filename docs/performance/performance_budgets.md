# Performance budgets

Measurements used Windows/Python 3.14, `perf_counter`, local storage, temporary SQLite and offscreen Qt. They are diagnostic observations, not cross-machine SLAs.

| Scenario | Observed Sprint K | Blocking ceiling |
|---|---:|---:|
| cold import `acd` | median 190.395 ms (135.086–293.403) | 2,000 ms |
| cold import `acd.desktop` | median 1,655.663 ms (1,381.545–5,551.624) | 10,000 ms |
| bootstrap new DB | median 1,217.591 ms | 5,000 ms |
| bootstrap existing DB | median 390.033 ms | 3,000 ms |
| composition root, new DB | 1,430.786 ms | 5,000 ms informative |
| composition root, existing DB | median 569.581 ms | 3,000 ms informative |
| Sidebar / ApplicationPage | medians 1.460 / 7.416 ms | 500 / 1,000 ms |
| cancellation request | synchronous local request | 250 ms |
| temporary backup / restore | focused synthetic measurement | 10,000 ms each |
| fake OpenAI / synthetic plugin | focused synthetic measurement | 2,000 ms each |

Exact durations are not compared to a committed JSON baseline. Cold desktop import showed roughly 4x range, so monotonic promotion would encode machine noise. A promoted baseline requires stable multi-run CI evidence on a controlled runner.

