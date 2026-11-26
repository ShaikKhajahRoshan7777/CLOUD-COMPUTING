#!/usr/bin/env python3
"""B2.2 - effect of the combiner: same input, with and without."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from generate_logs import generate
from mr_local import run_job
from transit_mr import q1_map, sum_reduce

ROOT = os.path.join(os.path.dirname(__file__), "..")
p = os.path.join(ROOT, "data", "combiner_20mb.csv")
n, w = generate(p, size_mb=20, days=3, seed=42)
print(f"input: {n:,} records, {w/1048576:.1f} MB, split size 4 MB (scaled from 128 MB)")
res = {}
for label, comb in (("without", None), ("with", sum_reduce)):
    out, C, R = run_job(p, q1_map, sum_reduce, comb, reducers=2, split_bytes=4 * 1048576)
    res[label] = {"counters": C, "elapsed": R["elapsed"], "rows": len(out), "out_hash": hash(tuple(sorted(out))) }
a, b = res["without"], res["with"]
print("\n%-28s %16s %16s" % ("Counter", "Without Combiner", "With Combiner"))
rows = [("Map input records", "Map input records"), ("Map output records", "Map output records"),
        ("Combine input records", "Combine input records"), ("Combine output records", "Combine output records"),
        ("Reduce shuffle bytes", "Reduce shuffle bytes"), ("Reduce input records", "Reduce input records"),
        ("Reduce input groups", "Reduce input groups")]
for lab, key in rows:
    print("%-28s %16s %16s" % (lab, f"{a['counters'].get(key, 0):,}", f"{b['counters'].get(key, 0):,}"))
print("%-28s %16s %16s" % ("Elapsed time (s)", f"{a['elapsed']:.2f}", f"{b['elapsed']:.2f}"))
red = 100 * (1 - b["counters"]["Reduce shuffle bytes"] / a["counters"]["Reduce shuffle bytes"])
print(f"\nShuffle volume reduced by {red:.1f}%.  Final output identical: {a['out_hash'] == b['out_hash']}")
json.dump({"without": a["counters"] | {"elapsed": a["elapsed"]}, "with": b["counters"] | {"elapsed": b["elapsed"]}, "reduction_pct": red, "identical": a['out_hash'] == b['out_hash'], "records": n}, open(os.path.join(ROOT, "results", "combiner.json"), "w"), indent=1)
