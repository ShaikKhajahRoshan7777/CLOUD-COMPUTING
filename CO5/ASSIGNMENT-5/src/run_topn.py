#!/usr/bin/env python3
"""B2.3 - Q2 Top-5 busiest stations per day via a two-job chain, verified independently."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
from generate_logs import generate
from mr_local import run_job
from transit_mr import q2_station_day_map, q2_job2_map, sum_reduce, topn_reduce
from collections import Counter, defaultdict

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
p = os.path.join(DATA, "topn_small.csv")
n, w = generate(p, records=60000, days=3, seed=7)
print(f"input: {n:,} records, 3 days, 120 stations")

# Job 1: (station|date) -> count     [4 reducers, combiner = sum]
j1, C1, R1 = run_job(p, q2_station_day_map, sum_reduce, sum_reduce, reducers=4, split_bytes=512 * 1024)
print(f"Job 1: {C1['Launched map tasks']} maps, {C1['Map output records']:,} map-out -> "
      f"{C1['Reduce input records']:,} shuffled after combiner -> {len(j1)} (station,day) rows")
tmp = os.path.join(DATA, "job1_out.txt")
open(tmp, "w").write("".join(x + "\n" for x in j1))

# Job 2: date -> top-5 (station|count)   [1 reducer is safe: only #days keys, <=N rows per mapper per day]
j2, C2, R2 = run_job(tmp, q2_job2_map, topn_reduce, topn_reduce, reducers=1, split_bytes=2048)
print(f"Job 2: {C2['Launched map tasks']} maps, {C2['Map output records']} map-out -> "
      f"{C2['Combine output records']} after top-5 combiner -> {len(j2)} output rows")

# Independent verification (plain Python, no MapReduce)
cnt = defaultdict(Counter)
for l in open(p):
    f = l.rstrip().split(",")
    if len(f) == 6 and f[4] == "ENTRY":
        cnt[f[0][:10]][f[1]] += 1
oracle = []
for d in sorted(cnt):
    ranked = sorted(cnt[d].items(), key=lambda kv: (-kv[1], kv[0]))[:5]
    oracle += [f"{d}\t{s}|{c}" for s, c in ranked]
got = sorted(j2)
print("\nTop-5 busiest stations per day (MapReduce output):")
for l in sorted(j2, key=lambda s: (s.split("\t")[0], -int(s.split("|")[1]))): print("  ", l)
print("\nVERIFICATION against independent script:", "MATCH" if got == sorted(oracle) else "MISMATCH")
json.dump({"job1": C1, "job2": C2, "match": got == sorted(oracle)}, open(os.path.join(os.path.dirname(__file__), "..", "results", "topn.json"), "w"), indent=1)
