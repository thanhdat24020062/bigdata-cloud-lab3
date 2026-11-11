# Role C: Cross-check of Role D layout A/B benchmark equivalence (Lab 3)

**Status: PASS**

## What was checked
Role D's benchmark query on both physical layouts must return the same result,
and that result must equal an independently computed answer.

- Query: `event_date = DATE '2026-02-06'`, `GROUP BY site`,
  columns `n_observations`, `sum_temperature_c` (decimal(18,2)), `n_late`.
- Layout A: unpartitioned Delta table. Layout B: Delta table partitioned by `event_date`.
- Source under test: `evidence/benchmark_report.json` (branch `role_D`, commit `f77e35a`).

## Independent reference answer (Role C)
Computed in plain Python (`decimal.Decimal`, no Spark, no code from Role D) from
`evidence/silver_after_batch02.jsonl` (Silver after batch 02, Delta version 1, 9,710 rows),
filtering `event_time_utc` date = 2026-02-06 and grouping by `site`.

| site   | n_observations | sum_temperature_c | n_late |
|--------|---------------:|------------------:|-------:|
| zone-1 | 25             | 532.50            | 5      |
| zone-2 | 25             | 540.00            | 5      |
| zone-3 | 25             | 532.50            | 5      |
| zone-4 | 25             | 540.00            | 5      |

## Role D's reported result
Role D's benchmark runs on a synthetic table expanded 100 times
(`benchmark_copies = 100`, 9,710 source rows -> 971,000 rows, `source_silver_version = 1`).
Replicas are not independent observations (stated by Role D in the report).

| site   | n_observations | sum_temperature_c | n_late |
|--------|---------------:|------------------:|-------:|
| zone-1 | 2500           | 53250.00          | 500    |
| zone-2 | 2500           | 54000.00          | 500    |
| zone-3 | 2500           | 53250.00          | 500    |
| zone-4 | 2500           | 54000.00          | 500    |

## Comparison
1. Layout A vs B: `result_equal = true` in all 6 measurements (3 rounds x 2 layouts).
   The report prints one shared `query_result`; the A = B conclusion relies on Role D's
   runner flag `result_equal`, not on two separately printed tables.
2. Role D's result divided by 100 equals the Role C reference for every site and every column
   (2500/100 = 25; 53250.00/100 = 532.50; 54000.00/100 = 540.00; 500/100 = 5).
3. Exactly 4 rows, one per site; `replica_id` is not part of the GROUP BY.
4. Source consistency: `source_silver_version = 1` and `source_rows = 9710` match the Silver
   after merge (9,610 -> 9,710 rows, version 0 -> 1) of run label `attempt-c02`.

## Notes and limits
- Timing in the report (median A 0.527 s, median B 0.402 s, ratio 1.31) comes from a synthetic
  experiment under warmed caches. The report states `table_file_count_is_not_scanned_file_count = true`,
  so the table file count (A: 32, B: 5) must not be read as scanned files. No partition-pruning claim
  is made here; that would need the physical plans (`plan_A.txt`, `plan_B.txt`), which were not part of this check.
- Multi-host execution is NOT_DEMONSTRATED (Spark `local[2]`, single host).
- `run_benchmark_error.json` (NotImplementedError: TODO 4) is Role D's first run before
  `benchmark_query` was implemented; it is kept as evidence of the failed attempt.

## Reproduce the reference answer
```bash
cd ~/Lab3-Student-Starter
python3 - <<'EOF'
import json
from decimal import Decimal
from collections import defaultdict
agg = defaultdict(lambda: [0, Decimal('0'), 0])
for l in open('evidence/silver_after_batch02.jsonl'):
    r = json.loads(l)
    if r['event_time_utc'][:10] == '2026-02-06':
        a = agg[r['site']]; a[0] += 1; a[1] += Decimal(r['temperature_c']); a[2] += 1 if r['is_late'] else 0
for s in sorted(agg): print(s, agg[s][0], agg[s][1].quantize(Decimal('0.01')), agg[s][2])
EOF
```

Checked by: Role C. Date: 2026-11-11.
