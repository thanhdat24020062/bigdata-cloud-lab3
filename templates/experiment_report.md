### Task 2 Evidence & Explanations (Role B)

#### B03: Conservation Checks
- Observation count conservation: SUM(Gold.n_observations) equals the exact Silver row count. No measurement keys are lost or duplicated across (site, event_date) groups.
- Additive components: SUM(Gold.sum_temperature_c) and SUM(Gold.n_late) equal the Silver totals, ensuring validity for higher-level rollups.

#### B04: Unweighted Mean vs. Observation-Weighted Mean
- Reason for divergence: AVG(mean_temperature_c) across site/day groups is an unweighted average of group means, assigning equal weight to every group regardless of observation counts. In contrast, SUM(sum_temperature_c) / SUM(n_observations) is the observation-weighted mean, reflecting the true overall dataset temperature.
- Conclusion: The two values only match when all site/day groups have identical observation counts (n_observations).
