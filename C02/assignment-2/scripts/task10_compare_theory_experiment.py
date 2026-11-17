#!/usr/bin/env python3
"""TASK 10 - compare Task 3 model predictions with Task 9 measurements (error analysis).

Predictions use the Task 3 model with the measured bare-metal baseline and YOUR machine's core
count (the model's 64 cores do not apply to a laptop):
   CPU per instance   = base_cpu * (1-h) * min(1, cores/N)
   CPU mean latency   = base_lat / ((1-h)*min(1, cores/N))
   Disk per instance  = base_disk * (1-h_io) / N            (device shared fairly)
   Net per instance   = min(base_net, line*(1-h_io)/N)
APE = |measured - predicted| / predicted * 100.   Also fits h from the N <= cores points.
"""
import argparse
import os
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import _common
from _common import ROOT, RESULTS, save_table
from educloud.config import APPROACHES, MODEL_KEY, HOST
from educloud.stats import ape_pct


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(ROOT / "data" / "results" / "results.csv"))
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--cores", type=int, default=os.cpu_count(), help="cores of the machine you tested on")
    ap.add_argument("--line-gbps", type=float, default=HOST.nic_gbps, help="line rate of the tested link")
    a = ap.parse_args()
    path = ROOT / "data" / "demo" / "results.csv" if a.demo else a.input
    outdir = ROOT / "results" / "demo" if a.demo else RESULTS
    outdir.mkdir(parents=True, exist_ok=True)
    _common.RESULTS = outdir
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        sys.exit(f"{path} not found - run Task 8 first (or --demo).")
    sc = df[(df.scenario == "scaling") & (df.mitigation == "none")]
    b = sc[(sc.approach == "baremetal") & (sc.instances == 1)]
    if b.empty:
        sys.exit("Need a bare-metal baseline row (approach=baremetal, instances=1).")
    base = b.mean(numeric_only=True)

    rows, fits = [], []
    for appr, g in sc[sc.approach != "baremetal"].groupby("approach"):
        m = APPROACHES[MODEL_KEY[appr]]
        for n, gg in g.groupby("instances"):
            share = min(1.0, a.cores / n)
            pred = {
                "cpu_eps": base.cpu_eps * (1 - m.h_cpu) * share,
                "cpu_lat_mean_ms": base.cpu_lat_mean_ms / ((1 - m.h_cpu) * share),
                "disk_mbps": base.disk_mbps * (1 - m.h_io) / n,
                "net_gbps": min(base.net_gbps, a.line_gbps * (1 - m.h_io) / n),
            }
            for metric, p in pred.items():
                meas = gg[metric].mean()
                if pd.isna(meas):
                    continue
                rows.append({"approach": appr, "instances": n, "metric": metric,
                             "predicted": round(p, 3), "measured": round(meas, 3),
                             "APE_%": round(ape_pct(p, meas), 1)})
        low = g[g.instances <= a.cores]
        h_fit = 1 - low.cpu_eps.mean() / base.cpu_eps
        fits.append({"approach": appr, "h_assumed_%": m.h_cpu * 100, "h_fitted_from_data_%": round(h_fit * 100, 1)})
    res = pd.DataFrame(rows)
    save_table(res, "task10_prediction_vs_measurement")
    save_table(res.groupby(["approach", "metric"], as_index=False)["APE_%"].mean().round(1)
               .rename(columns={"APE_%": "mean_APE_%"}), "task10_mean_error")
    save_table(pd.DataFrame(fits), "task10_overhead_fit")

    # scaling efficiency: aggregate throughput at largest N relative to perfect scaling up to `cores`
    eff = []
    for appr, g in sc[sc.approach != "baremetal"].groupby("approach"):
        s = g.groupby("instances").cpu_eps.mean()
        n_max = int(s.index.max())
        eff.append({"approach": appr, "N_max": n_max,
                    "aggregate_vs_ideal_%": round(100 * s[n_max] * n_max / (base.cpu_eps * min(n_max, a.cores)), 1)})
    save_table(pd.DataFrame(eff).sort_values("aggregate_vs_ideal_%", ascending=False), "task10_scaling_efficiency")

    cpu = res[res.metric == "cpu_eps"]
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for appr, g in cpu.groupby("approach"):
        ax.plot(g.instances, g.measured, "o-", label=f"{appr} measured")
        ax.plot(g.instances, g.predicted, "x--", label=f"{appr} predicted")
    ax.set_xscale("log", base=2)
    ax.set_xticks(sorted(cpu.instances.unique()))
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax.set_xlabel("co-located instances")
    ax.set_ylabel("CPU events/s per instance")
    ax.set_title("Task 10: model vs measurement" + ("  [DEMO DATA]" if a.demo else ""))
    ax.legend(fontsize=7)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(outdir / "task10_model_vs_measurement.png", dpi=150)
    print(f"\nFigure: {outdir / 'task10_model_vs_measurement.png'}")


if __name__ == "__main__":
    main()
