import json, hashlib, sys, statistics
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict
from pathlib import Path

ev = Path(sys.argv[1] if len(sys.argv) > 1 else "evidence")
impl = Path(sys.argv[2] if len(sys.argv) > 2 else "templates/student_impl.py")
Q6 = Decimal("0.000001")
ok = True
def chk(name, cond, detail=""):
    global ok
    print(("PASS  " if cond else "FAIL  ") + name + (("  -> " + str(detail)) if (detail and not cond) else ""))
    ok = ok and bool(cond)
J = lambda n: json.load(open(ev / n))
r6 = lambda x: Decimal(x).quantize(Q6, ROUND_HALF_UP)

S = [json.loads(l) for l in open(ev / "silver_after_batch02.jsonl") if l.strip()]
state, bench, runb = J("state.json"), J("benchmark_report.json"), J("run_benchmark.json")

g = defaultdict(list)
for r in S: g[(r["site"], r["event_time_utc"][:10])].append(r)
G = {}
for k, v in g.items():
    n = len(v); s = sum(Decimal(r["temperature_c"]) for r in v); late = sum(1 for r in v if r["is_late"])
    G[k] = dict(n=n, s=s, mean=r6(s / n), mn=min(Decimal(r["temperature_c"]) for r in v),
                mx=max(Decimal(r["temperature_c"]) for r in v), late=late, lr=r6(Decimal(late) / n),
                a25=sum(1 for r in v if Decimal(r["temperature_c"]) > 25), sens=len({r["sensor_id"] for r in v}))

print("== Silver / Gold (role B cross-check)")
chk("Silver has 9710 rows, unique record_id", len(S) == 9710 and len({r["record_id"] for r in S}) == 9710, len(S))
gold = J("gold_after_batch02.json")
gk = {(x["site"], x["event_date"]): x for x in gold}
bad = [k for k, x in gk.items() if k not in G or (x["n_observations"], Decimal(x["sum_temperature_c"]), Decimal(x["mean_temperature_c"]),
       Decimal(x["min_temperature_c"]), Decimal(x["max_temperature_c"]), x["n_late"], Decimal(x["late_rate"]),
       x["n_above_25"], x["n_sensors"]) != (G[k]["n"], G[k]["s"], G[k]["mean"], G[k]["mn"], G[k]["mx"], G[k]["late"], G[k]["lr"], G[k]["a25"], G[k]["sens"])]
chk("Gold after batch02: every group and field equals independent recomputation", set(gk) == set(G) and not bad, bad)
chk("SUM(Gold.n_observations) == Silver rows", sum(x["n_observations"] for x in gold) == len(S))
chk("SUM(Gold.sum_temperature_c) == Silver total", sum(Decimal(x["sum_temperature_c"]) for x in gold) == sum(Decimal(r["temperature_c"]) for r in S))

print("== Q1 / Q2 / Q3")
bq1 = [x for x in J("Q1_site_day.json")["rows"] if (x["site"], x["event_date"]) not in G or
       (x["n_observations"], Decimal(x["mean_temperature_c"]), x["n_late"], Decimal(x["late_rate"])) != (G[(x["site"], x["event_date"])]["n"], G[(x["site"], x["event_date"])]["mean"], G[(x["site"], x["event_date"])]["late"], G[(x["site"], x["event_date"])]["lr"])]
chk("Q1 rows equal recomputation (n, mean, n_late, late_rate)", not bq1 and len(J("Q1_site_day.json")["rows"]) == len(G), bq1)
bq3 = [x for x in J("Q3_above25_rate.json")["rows"] if (x["site"], x["event_date"]) not in G or
       (x["n_observations"], x["n_above_25"], Decimal(x["above25_rate"])) != (G[(x["site"], x["event_date"])]["n"], G[(x["site"], x["event_date"])]["a25"], r6(Decimal(G[(x["site"], x["event_date"])]["a25"]) / G[(x["site"], x["event_date"])]["n"]))]
chk("Q3 rows equal recomputation (n, n_above_25, rate)", not bq3, bq3)
day = defaultdict(lambda: [Decimal(0), 0, [], ])
for (site, d), e in G.items():
    day[d][0] += e["s"]; day[d][1] += e["n"]; day[d][2].append(e["mean"])
bq2 = []
for x in J("Q2_weighted_day.json")["rows"]:
    s, n, means = day[x["event_date"]]
    if (x["n_observations"], Decimal(x["weighted_mean_c"]), Decimal(x["naive_mean_of_means_c"])) != (n, r6(s / n), r6(sum(means) / len(means))): bq2.append(x["event_date"])
chk("Q2 weighted mean and naive mean equal recomputation", not bq2 and len(J("Q2_weighted_day.json")["rows"]) == len(day), bq2)

print("== Benchmark")
exp = defaultdict(lambda: [0, Decimal(0), 0])
for r in S:
    if r["event_time_utc"][:10] == "2026-02-06":
        e = exp[r["site"]]; e[0] += 1; e[1] += Decimal(r["temperature_c"]); e[2] += int(r["is_late"])
expected = [{"site": s, "n_observations": e[0] * 100, "sum_temperature_c": str(e[1] * 100), "n_late": e[2] * 100} for s, e in sorted(exp.items())]
chk("benchmark query_result equals independent recomputation x100", bench["query_result"] == expected, (bench["query_result"], expected))
chk("expanded_rows == source_rows x 100 and source_rows == Silver rows", bench["expanded_rows"] == bench["source_rows"] * 100 == 971000 and bench["source_rows"] == len(S))
m = bench["measurements"]
chk("six measurements, order A-B, B-A, A-B, all result_equal", [x["layout"] for x in m] == list("ABBAAB") and len(m) == 6 and all(x["result_equal"] for x in m))
medA = statistics.median(x["elapsed_seconds"] for x in m if x["layout"] == "A"); medB = statistics.median(x["elapsed_seconds"] for x in m if x["layout"] == "B")
chk("recomputed medians and A/B ratio equal the report", abs(medA - bench["median_seconds"]["A"]) < 1e-9 and abs(medB - bench["median_seconds"]["B"]) < 1e-9 and abs(medA / medB - bench["A_median_over_B_median"]) < 1e-9)
ld = bench["layout_details"]
chk("layout A unpartitioned/32 files; layout B partitioned by event_date/5 files", ld["A"]["partition_columns"] == [] and ld["A"]["total_table_data_files"] == 32 and ld["B"]["partition_columns"] == ["event_date"] and ld["B"]["total_table_data_files"] == 5)
pa, pb = (ev / "plan_A.txt").read_text(), (ev / "plan_B.txt").read_text()
chk("plan_B has PartitionFilters on event_date = 2026-02-06", "PartitionFilters" in pb and "2026-02-06" in pb)
chk("plan_A has no PartitionFilters line", "PartitionFilters" not in pa)
chk("benchmark source Silver version == state.silver_final_version, Gold bound to same Silver version",
    bench["source_silver_version"] == state["silver_final_version"] == state["gold_source_silver_version"])

print("== Code, lineage, files, secrets")
h = hashlib.sha256(open(impl, "rb").read()).hexdigest()
chk("sha256(student_impl.py) == benchmark implementation_sha256", h == runb["implementation_sha256"], h)
chk("that code is archived in evidence/code_versions/", (ev / "code_versions" / (h + ".py")).exists())
chk("run_benchmark.json status COMPLETE", runb["status"] == "COMPLETE", runb["status"])
ev_l = [json.loads(l) for l in open(ev / "lineage.jsonl") if l.strip()]
bl = [e.get("eventType") for e in ev_l if e.get("job", {}).get("name") == "benchmark"]
print("INFO  benchmark lineage events:", bl)
chk("lineage has START and a terminal event for every benchmark run (incl. the aborted first attempt)",
    bl.count("START") == len(bl) - bl.count("START") and len(bl) > 0, bl)
for f in ["Q1_site_day.json", "Q2_weighted_day.json", "Q3_above25_rate.json", "daily_mean.png", "late_fraction.png",
          "plan_A.txt", "plan_B.txt", "benchmark_report.json", "run_benchmark_error.json", "runtime_benchmark.json"]:
    chk("exists: " + f, (ev / f).exists())
leak = [str(p) for p in ev.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl", ".txt", ".md") and
        any(t in p.read_text(errors="ignore") for t in ("PRIVATE KEY", "operator_email", "secret_key", "SecretAccessKey"))]
chk("no private key / operator_email / secret strings in evidence text files", not leak, leak)
print("\nOVERALL:", "ALL CHECKS PASSED" if ok else "SOME CHECKS FAILED")
