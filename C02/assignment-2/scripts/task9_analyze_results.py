#!/usr/bin/env python3
"""TASK 9 - tables and graphs from data/results/results.csv (mean +/- standard deviation).

Produces in results/ :
  task9_table_scaling.csv/.md         throughput, latency, steal, degradation vs bare metal
  task9_table_startup_memory.csv/.md  start-up time and memory footprint
  task9_table_mitigation.csv/.md      with vs without mitigation
  graph1_throughput_vs_instances.png  Graph 1
  graph2_p95_under_interference.png   Graph 2
Use  --demo  to run on the synthetic demo data (pipeline test only).
"""
import argparse
import sys
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import _common
from _common import ROOT, RESULTS, save_table

METRICS = ["cpu_eps", "cpu_lat_mean_ms", "cpu_lat_p95_ms", "disk_mbps", "disk_lat_p95_ms",
           "net_gbps", "mem_bogo_ops_s", "steal_pct"]
ORDER = ["baremetal", "docker", "gvisor", "kata", "kvm"]
STYLE = {"baremetal": ("k", "s"), "docker": ("tab:blue", "o"), "gvisor": ("tab:green", "^"),
         "kata": ("tab:orange", "D"), "kvm": ("tab:red", "v")}


def pm(m, s, d=2):
    return "n/a" if pd.isna(m) else f"{m:.{d}f} ± {0 if pd.isna(s) else s:.{d}f}"


def aggregate(df, by):
    g = df.groupby(by)[METRICS + ["startup_s", "mem_footprint_mb"]].agg(["mean", "std", "count"])
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(ROOT / "data" / "results" / "results.csv"))
    ap.add_argument("--demo", action="store_true", help="use data/demo/results.csv (synthetic!)")
    ap.add_argument("--machine", default="<describe your machine: CPU, RAM, kernel>",
                    help="text printed under the graphs (required by the assignment)")
    args = ap.parse_args()
    path = ROOT / "data" / "demo" / "results.csv" if args.demo else args.input
    outdir = ROOT / "results" / "demo" if args.demo else RESULTS
    outdir.mkdir(parents=True, exist_ok=True)
    _common.RESULTS = outdir                     # save_table() writes here
    try:
        df = pd.read_csv(path)
    except FileNotFoundError:
        sys.exit(f"{path} not found. Run scripts/task8_run_benchmarks.py first (or use --demo to test the pipeline).")
    tag = "  [DEMO DATA - synthetic]" if args.demo else ""
    reps = int(df.groupby(["approach", "scenario", "instances", "noise", "mitigation"]).run.nunique().min())
    foot = f"{args.machine} | repetitions per point: {reps} | error bars: ±1 SD{tag}"

    base_df = df[(df.approach == "baremetal") & (df.scenario == "scaling") & (df.instances == 1)
                 & (df.mitigation == "none")]
    base = base_df[METRICS].mean() if len(base_df) else None
    if base is None:
        print("WARNING: no bare-metal baseline (approach=baremetal, instances=1) -> degradation columns skipped",
              file=sys.stderr)

    # ---------------- scaling table
    sc = df[(df.scenario == "scaling") & (df.mitigation == "none")]
    rows = []
    for (a, n), g in sc.groupby(["approach", "instances"]):
        r = {"approach": a, "instances": n, "runs": g.run.nunique()}
        for m in METRICS:
            r[m] = pm(g[m].mean(), g[m].std(), 3 if "gbps" in m else 2)
        if base is not None:
            r["cpu_degradation_%"] = round((base.cpu_eps - g.cpu_eps.mean()) / base.cpu_eps * 100, 1)
            r["p95_latency_increase_%"] = round((g.cpu_lat_p95_ms.mean() - base.cpu_lat_p95_ms) / base.cpu_lat_p95_ms * 100, 1)
        rows.append(r)
    t = pd.DataFrame(rows)
    t["_o"] = t.approach.map({k: i for i, k in enumerate(ORDER)})
    save_table(t.sort_values(["_o", "instances"]).drop(columns="_o"), "task9_table_scaling")

    # ---------------- startup / memory
    rows = []
    for a, g in sc.groupby("approach"):
        rows.append({"approach": a, "startup_s": pm(g.startup_s.mean(), g.startup_s.std(), 2),
                     "memory_per_instance_MB": pm(g.mem_footprint_mb.mean(), g.mem_footprint_mb.std(), 0)})
    save_table(pd.DataFrame(rows), "task9_table_startup_memory")

    # ---------------- mitigation
    mit = df[(df.scenario == "scaling") & (df.mitigation != "none")]
    if len(mit):
        rows = []
        for (a, n, m), g in mit.groupby(["approach", "instances", "mitigation"]):
            ref = sc[(sc.approach == a) & (sc.instances == n)]
            if ref.empty:
                continue
            rows.append({"approach": a, "instances": n, "mitigation": m,
                         "cpu_eps_without": pm(ref.cpu_eps.mean(), ref.cpu_eps.std()),
                         "cpu_eps_with": pm(g.cpu_eps.mean(), g.cpu_eps.std()),
                         "cost_%": round((ref.cpu_eps.mean() - g.cpu_eps.mean()) / ref.cpu_eps.mean() * 100, 1),
                         "p95_without_ms": pm(ref.cpu_lat_p95_ms.mean(), ref.cpu_lat_p95_ms.std()),
                         "p95_with_ms": pm(g.cpu_lat_p95_ms.mean(), g.cpu_lat_p95_ms.std())})
        save_table(pd.DataFrame(rows), "task9_table_mitigation")

    # ---------------- Graph 1
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
    for a in ORDER:
        g = sc[sc.approach == a]
        if g.empty:
            continue
        c, mk = STYLE[a]
        s = g.groupby("instances").cpu_eps.agg(["mean", "std"]).reset_index()
        s["std"] = s["std"].fillna(0)
        axs[0].errorbar(s.instances, s["mean"] * s.instances, yerr=s["std"] * s.instances, color=c, marker=mk,
                        capsize=3, label=a)
        axs[1].errorbar(s.instances, s["mean"], yerr=s["std"], color=c, marker=mk, capsize=3, label=a)
    for ax, ttl, yl in ((axs[0], "Aggregate CPU throughput", "events/s (sum over instances)"),
                        (axs[1], "Per-instance CPU throughput", "events/s per instance")):
        ax.set_xscale("log", base=2)
        ax.set_xticks([1, 2, 4, 8, 16])
        ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
        ax.set_xlabel("co-located instances")
        ax.set_ylabel(yl)
        ax.set_title(ttl)
        ax.grid(alpha=.3)
        ax.legend()
    fig.suptitle("Graph 1: sysbench CPU throughput vs number of co-located instances" + tag, fontsize=11)
    fig.text(0.5, 0.005, foot, ha="center", fontsize=7)
    fig.tight_layout(rect=(0, 0.03, 1, 0.95))
    fig.savefig(outdir / "graph1_throughput_vs_instances.png", dpi=150)

    # ---------------- Graph 2
    itf = df[(df.scenario == "interference") & (df.mitigation == "none")]
    if len(itf):
        conds = [c for c in ["none", "cpu", "disk", "mem"] if c in set(itf.noise)]
        apps = [a for a in ORDER if a in set(itf.approach)]
        n = int(itf.instances.max())
        fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
        for ax, metric, lab in ((axs[0], "cpu_lat_p95_ms", "CPU-benchmark p95 latency (ms)"),
                                (axs[1], "disk_lat_p95_ms", "disk p95 latency (ms)")):
            w = 0.8 / len(apps)
            for i, a in enumerate(apps):
                s = [itf[(itf.approach == a) & (itf.noise == c)][metric] for c in conds]
                ax.bar(np.arange(len(conds)) + i * w, [x.mean() for x in s], w, yerr=[x.std() for x in s],
                       capsize=3, color=STYLE[a][0], label=a)
            ax.set_xticks(np.arange(len(conds)) + 0.4 - w / 2)
            ax.set_xticklabels([f"{c} noise" if c != "none" else "no interference" for c in conds])
            ax.set_ylabel(lab)
            ax.grid(axis="y", alpha=.3)
            ax.legend(fontsize=8)
        fig.suptitle(f"Graph 2: victim p95 latency under noisy-neighbour interference ({n} instances)" + tag, fontsize=11)
        fig.text(0.5, 0.005, foot, ha="center", fontsize=7)
        fig.tight_layout(rect=(0, 0.03, 1, 0.95))
        fig.savefig(outdir / "graph2_p95_under_interference.png", dpi=150)
    else:
        print("No interference data found -> Graph 2 skipped (run --scenario interference).", file=sys.stderr)
    print(f"\nFigures and tables written to {outdir}")


if __name__ == "__main__":
    main()
