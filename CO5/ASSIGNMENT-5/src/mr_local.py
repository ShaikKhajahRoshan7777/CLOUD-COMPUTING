#!/usr/bin/env python3
"""
mr_local.py - a small LOCAL emulator of the Hadoop MapReduce data path.

Reproduces: input splits (byte ranges with Hadoop's line-boundary rule), one map task per
split, map-side sort, optional combiner, hash partitioner, shuffle, merge-sort, reduce,
and the standard job counters.  It is NOT a cluster: times are wall-clock seconds of this
Python process and are used only for relative comparison.
"""
import os
import time
import zlib
from collections import defaultdict


def make_splits(path, split_bytes):
    size = os.path.getsize(path)
    if size == 0:
        return []
    return [(off, min(split_bytes, size - off)) for off in range(0, size, split_bytes)]


def read_split(path, off, length):
    """Hadoop LineRecordReader rule: skip the partial first line (unless offset 0);
    read past the split end to finish the last line that STARTS inside the split."""
    with open(path, "rb") as f:
        f.seek(off)
        if off != 0:
            f.readline()
        end = off + length
        while f.tell() <= end:
            raw = f.readline()
            if not raw:
                break
            yield raw.decode("utf-8", "replace")
            if f.tell() > end:
                break


def partition(key, n):
    return zlib.crc32(key.split("\t")[0].encode()) % n


def run_job(path, mapper, reducer, combiner=None, reducers=1, split_bytes=16 * 1048576):
    """Return (outputs, counters, report). mapper(lines, counter) -> iterator of 'k<TAB>v'."""
    t0 = time.time()
    C = defaultdict(int)

    def counter(g, n, v=1):
        C[f"{g}.{n}"] += v

    splits = make_splits(path, split_bytes)
    C["Launched map tasks"] = len(splits)
    C["Launched reduce tasks"] = reducers
    buckets = [[] for _ in range(reducers)]
    map_times = []
    for off, ln in splits:
        tm = time.time()
        lines = list(read_split(path, off, ln))
        C["Map input records"] += len(lines)
        out = list(mapper(lines, counter))
        C["Map output records"] += len(out)
        out.sort(key=lambda s: s.split("\t")[0])
        if combiner:
            C["Combine input records"] += len(out)
            out = list(combiner(iter(out)))
            C["Combine output records"] += len(out)
        for rec in out:
            buckets[partition(rec, reducers)].append(rec)
            C["Reduce shuffle bytes"] += len(rec.encode()) + 1
        map_times.append(time.time() - tm)

    outputs, red_report = [], []
    for r, recs in enumerate(buckets):
        tr = time.time()
        recs.sort(key=lambda s: s.split("\t")[0])
        groups = len({x.split("\t")[0] for x in recs})
        C["Reduce input records"] += len(recs)
        C["Reduce input groups"] += groups
        res = list(reducer(iter(recs)))
        C["Reduce output records"] += len(res)
        outputs.extend(res)
        red_report.append({"reducer": r, "input_records": len(recs),
                           "input_groups": groups, "seconds": time.time() - tr})
    report = {"splits": len(splits), "map_seconds": map_times, "reducers": red_report,
              "elapsed": time.time() - t0}
    return outputs, dict(C), report
