## 5. Controlled layout experiment (Role D)

### Setup

- **Dataset.** Silver version 1 of run `attempt-c02` (9,710 rows) expanded with 100 replica IDs into 971,000 synthetic rows (9,710 x 100). Replicas are copies, not independent observations, and were never written to operational Gold. The benchmark tables are separate Delta tables under the run's `benchmarks/` prefix.
- **Provenance note.** The benchmark ran on `attempt-c02`, while the group release candidate pins Silver v1 of `attempt-e01`. The post-batch Silver and Gold exports of the two runs are byte-identical, so the benchmark was built from the logically same snapshot; only the table paths differ.
- **Query (identical for both layouts).** `event_date = DATE '2026-02-06'`, `GROUP BY site`, returning `site`, `n_observations`, `sum_temperature_c`, `n_late`. Evaluation is forced by collecting the small grouped answer.
- **Resources.** Spark 4.0.1, Delta 4.0.1, Python 3.11.18, Java 17, Hadoop 3.4.1; master `local[2]` with local-file storage on one host (parallel local execution, not multi-node); adaptive query execution (AQE) enabled; `spark.sql.shuffle.partitions` = 8; timezone UTC. The same build, resources, snapshot, query, copy factor and AQE setting were used for both layouts.

### Layouts and metadata

| | Layout A | Layout B |
|---|---|---|
| Physical design | unpartitioned, repartitioned to 32 writer tasks | `partitionBy(event_date)`, five date-keyed writer partitions |
| Delta version | 0 | 0 |
| Total table data files | 32 | 5 |
| Total table bytes | 16,396,223 (about 16.4 MB) | 525,397 (about 0.53 MB) |
| Setup / write time (excluded from query times) | 13.86 s | 6.20 s |

The file counts and byte totals are table metadata. They are not the number of files scanned, and the files actually read by the query must come from the Spark UI, which is not captured in the evidence.

### Measurements

One warm-up per layout, then three rounds in the order A-B, B-A, A-B (six measured evaluations):

| Round | First | Second |
|---|---|---|
| 1 | A: 0.582 s | B: 0.456 s |
| 2 | B: 0.402 s | A: 0.527 s |
| 3 | A: 0.514 s | B: 0.350 s |

All six answers were identical and equal to the expected result: 4 sites with 2,500 observations each, `sum_temperature_c` of 53,250.00 / 54,000.00 / 53,250.00 / 54,000.00 and `n_late` of 500 per site (exactly 100 times the 2026-02-06 Gold values). Layout A times: 0.582, 0.527, 0.514 s, median **0.527 s**. Layout B times: 0.456, 0.402, 0.350 s, median **0.402 s**.

$$\frac{\operatorname{median}(A)}{\operatorname{median}(B)} = \frac{0.527}{0.402} \approx 1.31$$

### Plans and interpretation

- The plan for B contains `PartitionFilters: [isnotnull(event_date), event_date = 2026-02-06]` on the `PreparedDeltaFileIndex` of the date-partitioned table, which means partition directories can be pruned by the date predicate before data files are read.
- The plan for A has no partition filters; it shows `PushedFilters: [IsNotNull(event_date), EqualTo(event_date,2026-02-06)]`, a row-level filter on `event_date` applied while reading, so the date predicate is not used to prune partition directories.
- Both plans were captured with `isFinalPlan=false`, i.e. before AQE finalised the physical plan, so the executed plan may differ in details.
- Layout B was faster in all three rounds, but the evidence supports only a modest conclusion: there are three samples per layout, the absolute gap is about 0.1 s, both layouts also get faster from round to round (A 0.582 to 0.514 s, B 0.456 to 0.350 s), and the runs are warmed and repeated on one host, not cold-cache or distributed. `clearCache` does not reset operating-system or object-store caches.
- The table sizes differ by a factor of about 31 (16.4 MB against 0.53 MB). The B timing advantage therefore cannot be attributed to partition pruning alone: B also reads far fewer and smaller files. The likely reason for the smaller size is that grouping rows by date improves compression, but this was not tested here.
- No minimum speedup is claimed. If B had been slower, the overhead of writing and managing more partitions would have been the explanation. These results say nothing about production-scale performance.
