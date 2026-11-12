"""Redraw the two Role D plots from saved Gold query results (no Spark needed).
Usage: python3 -I replot.py <evidence_dir> <out_dir>
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ev, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)

q2 = json.load(open(ev / "Q2_weighted_day.json"))["rows"]
q1 = json.load(open(ev / "Q1_site_day.json"))["rows"]

# ---- Plot 1: observation-weighted daily mean ----
dates = [r["event_date"] for r in q2]
mean = [float(r["weighted_mean_c"]) for r in q2]
n = [int(r["n_observations"]) for r in q2]
x = np.arange(len(dates))

fig, ax = plt.subplots(figsize=(10, 5.4))
ax.plot(x, mean, marker="o", color="#1f77b4")
for xi, m, ni in zip(x, mean, n):
    ax.annotate(f"{m:.3f} C\nn = {ni:,}", (xi, m), textcoords="offset points",
                xytext=(0, 12), ha="center", fontsize=8)
ax.annotate("only 100 rows\n(25 per site)", (x[-1], mean[-1]), textcoords="offset points",
            xytext=(-60, -34), ha="center", fontsize=8, color="#b22222",
            arrowprops=dict(arrowstyle="->", color="#b22222"))
ax.set_xticks(x, dates, rotation=20)
ax.set_ylim(20, 24.5)
ax.set_xlabel("UTC event date")
ax.set_ylabel("Observation-weighted mean temperature (C)")
ax.set_title("Daily mean temperature = SUM(sum_temperature_c) / SUM(n_observations)")
fig.tight_layout()
fig.savefig(out / "daily_mean.png", dpi=200)
plt.close(fig)

# ---- Plot 2: late fraction per site and day (grouped bars) ----
sites = sorted({r["site"] for r in q1})
days = sorted({r["event_date"] for r in q1})
cell = {(r["site"], r["event_date"]): r for r in q1}
w = 0.2
x = np.arange(len(days))
colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

fig, ax = plt.subplots(figsize=(11.5, 5.8))
for i, s in enumerate(sites):
    vals = [float(cell[(s, d)]["late_rate"]) for d in days]
    pos = x + (i - (len(sites) - 1) / 2) * w
    ax.bar(pos, vals, w, label=s, color=colors[i % 4])
    for p, d, v in zip(pos, days, vals):
        r = cell[(s, d)]
        ax.text(p, v + 0.004, f"{r['n_late']}/{r['n_observations']}", ha="center", va="bottom",
                fontsize=6.5, rotation=90)
ax.set_xticks(x, days, rotation=20)
ax.set_ylim(0, 0.26)
ax.set_xlabel("UTC event date")
ax.set_ylabel("Late fraction = n_late / n_observations")
ax.set_title("Late-arrival fraction per site and day (labels: n_late / n_observations)")
ax.legend(title="site", ncol=4, loc="upper center")
fig.tight_layout()
fig.savefig(out / "late_fraction.png", dpi=200)
plt.close(fig)
print("wrote", out / "daily_mean.png", out / "late_fraction.png")
