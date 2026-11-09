## 4. Analytics (Role D)

All values below are read from Gold version 1, computed from Silver version 1 (run `attempt-c02`). Source files: `evidence/Q1_site_day.json`, `Q2_weighted_day.json`, `Q3_above25_rate.json`; plots `daily_mean.png` and `late_fraction.png`.

### Q2 - observation-weighted mean vs mean of site means

| event_date | n_observations | weighted mean (C) | AVG of site means (C) | difference |
|---|---:|---:|---:|---:|
| 2026-02-02 | 2489 | 23.014665 | 23.016459 | +0.001794 |
| 2026-02-03 | 2880 | 22.936111 | 22.936111 | 0.000000 |
| 2026-02-04 | 2880 | 22.950000 | 22.950000 | 0.000000 |
| 2026-02-05 | 1361 | 23.034533 | 23.034212 | -0.000321 |
| 2026-02-06 | 100 | 21.450000 | 21.450000 | 0.000000 |

The weighted mean is SUM(sum_temperature_c) / SUM(n_observations). AVG(mean_temperature_c) gives each site/day group the same weight regardless of how many observations it holds, so the two values can differ only when site counts within a day are unequal. The differences on 2026-02-02 (site counts 625, 625, 620, 619) and 2026-02-05 are non-zero for that reason; the other days show no difference at six decimals, consistent with equal site counts. The weighted mean is the correct daily mean of the retained measurements. The total of the n_observations column is 9,710, equal to the Silver row count.

### Late fraction (numerator / denominator, summed over sites)

| event_date | n_late | n_observations | late fraction |
|---|---:|---:|---:|
| 2026-02-02 | 200 | 2489 | 0.080354 |
| 2026-02-03 | 0 | 2880 | 0.000000 |
| 2026-02-04 | 0 | 2880 | 0.000000 |
| 2026-02-05 | 0 | 1361 | 0.000000 |
| 2026-02-06 | 20 | 100 | 0.200000 |

Late rows occur only on 2026-02-02 and 2026-02-06. `is_late` is true only when ingest minus event time exceeds 900 seconds, and late rows are retained.

### Fraction above 25 C (numerator / denominator, summed over sites)

| event_date | n_above_25 | n_observations | fraction |
|---|---:|---:|---:|
| 2026-02-02 | 739 | 2489 | 0.296906 |
| 2026-02-03 | 832 | 2880 | 0.288889 |
| 2026-02-04 | 841 | 2880 | 0.292014 |
| 2026-02-05 | 406 | 1361 | 0.298310 |
| 2026-02-06 | 0 | 100 | 0.000000 |

Daily fractions are SUM(n_above_25) / SUM(n_observations), not an average of site rates. 25 C is a teaching threshold, not a calibrated physical or safety threshold. The 0/100 on 2026-02-06 is a property of the 100 rows added by revision batch 02 (25 per site), not evidence of a temperature change.

### Residual quality limitations

- Values are the released observed temperatures. They are not corrected with the QA reference sample, and a range-valid value can still disagree with that sample.
- Days are not equally complete: 2026-02-02 (2,489), 2026-02-05 (1,361) and 2026-02-06 (100) have fewer observations than the 2,880 of a full day, so daily comparisons are not comparisons of equally complete days.
- The 100 rows of 2026-02-06 are the only rows beyond the 9,610 handoff rows; statistics for that day rest on a very small sample.
- The fixture is a bounded teaching dataset, not production-scale evidence.

### Plot annotations (put under each figure)

- `daily_mean.png`: source = Gold v1 built from Silver v1; counts per day as in the Q2 table; days 2026-02-02, 2026-02-05 and 2026-02-06 are incomplete.
- `late_fraction.png`: source = Gold v1 built from Silver v1; numerators and denominators as in the late-fraction table; late rows occur only on 2026-02-02 and 2026-02-06.
