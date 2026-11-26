#!/usr/bin/env python3
"""B3.1 - scaling: 4 dataset sizes x 1/2/4 reducers (local emulation, split size 16 MB)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from generate_logs import generate
from mr_local import run_job
from transit_mr import q1_map, sum_reduce

ROOT = os.path.join(os.path.dirname(__file__), "..")
SPLIT = 16 * 1048576
SIZES = [10, 25, 50, 100]
rows = []
print("%8s %7s %9s %9s %14s %9s %10s" % ("Size(MB)", "Splits", "MapTasks", "Reducers", "ShuffleBytes", "Time(s)", "s per MB"))
for s in SIZES:
    p = os.path.join(ROOT, "data", f"scale_{s}mb.csv")
    n, w = generate(p, size_mb=s, days=3, seed=100 + s)
    for r in (1, 2, 4):
        out, C, R = run_job(p, q1_map, sum_reduce, sum_reduce, reducers=r, split_bytes=SPLIT)
        row = dict(size_mb=s, records=n, splits=R["splits"], maps=C["Launched map tasks"], reducers=r,
                   shuffle=C["Reduce shuffle bytes"], time=R["elapsed"])
        rows.append(row)
        print("%8d %7d %9d %9d %14s %9.2f %10.4f" % (s, row["splits"], row["maps"], r, f"{row['shuffle']:,}", row["time"], row["time"] / s))
    os.remove(p)                       # keep the repo small
json.dump(rows, open(os.path.join(ROOT, "results", "scaling.json"), "w"), indent=1)
