# Lab 3 – Short Experiment Report
## Lakehouse Processing and Analytics

**Submission scope:** Group experiment report  
**Implementation:** `student_impl.py`  
**Evidence directory:** `evidence/`

## 1. Handoff

The project uses the Lab 2 handoff as the initial input for the Lab 3 data pipeline. Before processing, input files are checked against the trusted manifest to verify file existence, integrity, and compatibility with the expected input contract.

Role A was responsible for the input acceptance and verification stage. This work included SHA-256 integrity verification, input schema validation, handoff identity verification, Delta schema-change rejection, and runtime preflight checks.

The recorded integrity verification reported 16 passing objects, 0 failed objects, and 0 missing objects in the checked `/home/ubuntu/repo-lab3` repository snapshot. This result applies only to that checked snapshot and should not be interpreted as proof that every EC2 workspace or distributed worker independently verified the same inputs.

A matching hash confirms that an object is consistent with the manifest used for verification. However, it does not independently prove the authenticity of the manifest itself. The supplied handoff is identified as `course_fallback_not_student_approval`, so it must not be described as a student-approved Lab 2 release.

**Evidence:**
- `evidence/role_a/input_integrity.json`
- `evidence/role_a/input_contract_tests.json`
- `evidence/role_a/delta_schema_probe.json`
- `evidence/role_a/preflight.json`
- `evidence/role_a/runtime_preflight.json`
- `evidence/role_a/worker_probe.json`
- `manifests/lab2_source_manifest.json`
- `manifests/lab3_inputs_convenience.json`

## 2. Table Semantics and Lineage

The pipeline organizes data into Bronze, Silver, and Gold layers.

- **Bronze:** Stores incoming physical source receipts and operational metadata. Repeated delivery of the same physical receipt should not create duplicate records. A later physical revision is retained as a separate receipt.
- **Silver:** Stores the selected current version of each observation, identified by `record_id`. Source provenance is preserved through fields such as `source_object`, `source_sha256`, and `source_row`.
- **Gold:** Stores aggregated analytical results derived from Silver, including site-level and daily metrics.

The event timestamp and ingestion timestamp are interpreted in UTC. The `event_date` field is derived from the UTC event timestamp. The observed `temperature_c` value is retained as released data and is not replaced by values from the QA reference.

Lineage records describe how source objects and physical row positions contribute to Silver records and downstream Gold aggregates. The QA reference is used for validation and reference purposes; it is not a source of measured temperature values.

Gold is a snapshot derived from a particular Silver version. Therefore, after Silver changes, Gold must be recomputed and its source Silver version recorded. A historical Silver version must not be combined with an unrelated Gold snapshot.

**Evidence:**
- `evidence/lineage.jsonl`
- `evidence/role_a/lineage.jsonl`
- `evidence/silver_baseline.jsonl`
- `evidence/silver_after_batch02.jsonl`
- `evidence/gold_baseline.json`
- `evidence/gold_after_batch02.json`

## 3. Incremental Processing

The incremental workflow processes the supplied change batch and updates the current Silver state.

Incoming records are evaluated using the defined business key and deterministic revision ordering. The pipeline must select the appropriate winning revision before applying the merge. Older revisions must not overwrite newer selected records.

The incremental verification considers the following behaviors:

1. Processing a new batch of changes.
2. Selecting the correct winning revision for each business key.
3. Rejecting stale revisions.
4. Preventing duplicate physical receipts during replay.
5. Preserving logical data consistency when the same batch is replayed.
6. Supporting historical reads and time-travel verification.
7. Recomputing Gold after Silver changes.

The baseline, post-update, replay, and historical exports are retained to support comparisons. Logical equivalence is the main replay invariant; a no-op merge does not necessarily need to preserve the same Delta version number.

Invalid input batches should be rejected before any write operation.

**Evidence:**
- `evidence/incremental.json`
- `evidence/silver_baseline.jsonl`
- `evidence/silver_after_batch02.jsonl`
- `evidence/silver_replay.jsonl`
- `evidence/silver_time_travel.jsonl`
- `evidence/gold_baseline.json`
- `evidence/gold_after_batch02.json`
- `evidence/state.json`

## 4. Analytics

The analytics stage produces three main Gold query outputs.

- **Q1 – Site/Day KPI:** Summarizes key metrics for each site and event date.
- **Q2 – Weighted Daily Mean:** Calculates observation-weighted daily averages. The weighted result must be computed from the underlying sums and counts rather than by simply averaging site-level averages.
- **Q3 – Above-threshold Rate:** Calculates the fraction of observations exceeding the specified temperature threshold for each site/day group.

The analytical outputs are used to inspect data behavior and compare site-level and daily patterns. Visualizations provide additional insight into the distribution of measurements and late-arriving observations.

The analytical results must be interpreted against the corresponding source snapshot. Synthetic replica-expanded data used for performance benchmarking must not be mixed into the operational Gold results.

**Evidence:**
- `evidence/Q1_site_day.json`
- `evidence/Q2_weighted_day.json`
- `evidence/Q3_above25_rate.json`
- `evidence/late_fraction.png`
- `evidence/daily_mean.png`

## 5. Layout Experiment

The layout experiment compares two physical storage configurations using the same logical dataset and analytical workload.

- **Layout A:** Unpartitioned Delta table.
- **Layout B:** Delta table partitioned by `event_date`.

The benchmark is intended to compare query execution performance under equivalent data and query conditions. Both layouts must return identical grouped results before their execution times can be compared.

The experiment uses warm-up executions followed by repeated measurements in the prescribed A/B order. The analysis should compare the six measured execution times, their medians, and the median ratio. Physical execution plans are also inspected to understand whether partition pruning reduces the amount of data scanned.

The benchmark evidence is retained in the project. Exact timing values and the performance winner should be reported only after checking the final benchmark output and confirming result equivalence. These measurements represent repeated executions under the experiment environment, not necessarily cold-cache performance.

**Evidence:**
- `evidence/benchmark_report.json`
- `evidence/run_benchmark.json`
- `evidence/runtime_benchmark.json`
- `evidence/plan_A.txt`
- `evidence/plan_B.txt`

## 6. Release and Accountability

The release stage validates the relationship between the handoff, Silver snapshot, Gold snapshot, and implementation metadata.

The recorded release candidate has the status:

`CANDIDATE_NOT_OWNER_PUBLISHED`

The release check reports:

`CANDIDATE_READY_FOR_INDEPENDENT_OWNER_REVIEW`

This means the candidate is prepared for independent review. It does not mean that the release has been officially published by the owner.

The release validation artifacts cover snapshot binding, release metadata, and rejection of invalid release conditions such as mismatched Silver/Gold versions, self-review, missing steward information, and invalid generating-code hashes. The actual author, reviewer, and steward identities must correspond to the members who performed those actions.

The independent cross-check also identified limitations. In particular, the Role C tamper-verification artifact `c_verify_a_i03.json` has an overall status of `PARTIAL`. Four tamper test cases passed, but the original trusted manifest in the checked `/work` location had been overwritten and could not serve as an independent trust anchor. Therefore, the tests demonstrate tamper detection for the tested copies, but do not establish independent authenticity of the original manifest.

Similarly, Role A's runtime and worker evidence should not be interpreted as complete proof of multi-host AWS execution without corresponding independent driver and executor evidence.

The group contribution records and manual verification results are maintained separately in `contributions.csv` and `manual_checks.csv`. All member names and responsibilities should be checked against the actual group allocation before final submission.

**Evidence:**
- `evidence/release_candidate/release_manifest.json`
- `evidence/release_candidate/snapshot_binding.json`
- `evidence/release_candidate/catalog.json`
- `evidence/release_check.json`
- `evidence/release_gate_tests.json`
- `evidence/role_a/`
- `evidence/c_verify_a_i03.json` (if included in the submitted evidence package)