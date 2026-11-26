#!/usr/bin/env python3
"""B3.2 - skewed vs uniform input, 4 reducers; prediction BEFORE the run; key salting fix."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from generate_logs import generate
from mr_local import run_job, partition
from transit_mr import q1_map, sum_reduce, parse

ROOT = os.path.join(os.path.dirname(__file__), "..")
R, SIZE = 4, 30
uni = os.path.join(ROOT, "data", "uniform.csv")
skw = os.path.join(ROOT, "data", "skewed.csv")
generate(uni, size_mb=SIZE, days=1, seed=11)
generate(skw, size_mb=SIZE, days=1, seed=11, hot="S001", hot_share=0.70)


def station_map(lines, counter=lambda g, n, v=1: None):          # job variant: total per STATION
    for l in lines:
        rec = parse(l)
        if rec and rec[2] == "ENTRY":
            yield f"{rec[1]}\t1"


def salted_map(lines, counter=lambda g, n, v=1: None):           # key salting: station#0..15
    i = 0
    for l in lines:
        rec = parse(l)
        if rec and rec[2] == "ENTRY":
            i += 1
            yield f"{rec[1]}#{i % 16}\t1"


print("PREDICTION (made before running):")
print(f"  hot station S001, 70% of records. Reducer owning key 'S001' (station-level key): "
      f"reducer {partition('S001', R)}")
print(f"  Under the hour-level Q1 key (S001|date|HH) the hot station's 24 keys hash to reducers: "
      f"{sorted({partition(f'S001|2026-03-02|{h:02d}', R) for h in range(24)})}")
print("  => skew visible with station-level key; Q1 hour-level key spreads the hot station over reducers.\n")

res = {}
for name, path, mapper, comb in (("uniform / station key", uni, station_map, None),
                                 ("skewed  / station key", skw, station_map, None),
                                 ("skewed  / Q1 hour key", skw, q1_map, None),
                                 ("skewed  / salted key", skw, salted_map, None)):
    out, C, rep = run_job(path, mapper, sum_reduce, comb, reducers=R, split_bytes=16 * 1048576)
    res[name] = rep["reducers"]
    tot = sum(x["input_records"] for x in rep["reducers"])
    print(f"{name}: total reduce input {tot:,} records")
    print("   reducer  input_records  share   reduce_time(s)")
    for x in rep["reducers"]:
        print("   %7d  %13s  %5.1f%%  %10.3f" % (x["reducer"], f"{x['input_records']:,}", 100 * x["input_records"] / tot, x["seconds"]))
    slow = max(rep["reducers"], key=lambda x: x["input_records"])["reducer"]
    print(f"   -> heaviest reducer: {slow}\n")
json.dump(res, open(os.path.join(ROOT, "results", "skew.json"), "w"), indent=1)
os.remove(uni); os.remove(skw)
