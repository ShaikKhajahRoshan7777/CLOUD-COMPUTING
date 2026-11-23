"""Faithful map / shuffle / reduce implementation of 'average speed per segment per hour'.

Pure functions (parse_line, partition_of, reduce_partition) are separated from the I/O
(split reading) so they can be unit-tested and reused.

Stages (mirrors Hadoop / Spark):
  1. MAP     : read one input split (byte range aligned to newline), parse + validate each
               line, emit ((segment, hour), (sum, count)); a COMBINER pre-aggregates per split.
  2. SHUFFLE : hash-partition every combiner output record to one of R reducers and
               serialise it (pickle) - the bytes are the 'shuffle volume'.
  3. REDUCE  : each reducer merges partial (sum,count) pairs and emits the average.
"""
import os, pickle, time, zlib
from datetime import datetime

MAX_SPEED = 200.0


def parse_line(line):
    """Return ((segment, hour), speed) or (None, reason). Pure function."""
    parts = line.rstrip("\r\n").split(",")
    if len(parts) != 4:
        return None, "malformed_field_count"
    _sensor, seg, spd, ts = parts
    if spd == "":
        return None, "null_speed"
    try:
        speed = float(spd)
    except ValueError:
        return None, "non_numeric_speed"
    if not (0.0 <= speed <= MAX_SPEED):
        return None, "speed_out_of_range"
    try:
        t = datetime.fromisoformat(ts)
    except ValueError:
        return None, "bad_timestamp"
    if not seg:
        return None, "missing_segment"
    return (seg, t.strftime("%Y-%m-%d %H")), speed


def partition_of(key, n_reducers):
    return zlib.crc32(("%s|%s" % key).encode()) % n_reducers


def input_splits(path, n_splits):
    """Hadoop-style byte-range splits aligned to line boundaries."""
    size = os.path.getsize(path)
    bounds = [i * size // n_splits for i in range(n_splits)] + [size]
    return [(bounds[i], bounds[i + 1]) for i in range(n_splits)]


def read_split(path, start, end):
    """Yield the lines that START inside [start, end) (Hadoop TextInputFormat rule)."""
    with open(path, "rb") as f:
        if start == 0:
            f.readline()               # skip header
        else:
            f.seek(start - 1)
            f.readline()               # skip the partial line owned by the previous split
        while True:
            pos = f.tell()
            if pos >= end:
                break
            line = f.readline()
            if not line:
                break
            yield line.decode()


def map_stage(path, splits, combiner=True):
    outputs, stats = [], {"read": 0, "accepted": 0, "rejected": 0, "reasons": {}}
    for (s, e) in splits:
        local, raw = {}, []
        for line in read_split(path, s, e):
            stats["read"] += 1
            key, val = parse_line(line)
            if key is None:
                stats["rejected"] += 1
                stats["reasons"][val] = stats["reasons"].get(val, 0) + 1
                continue
            stats["accepted"] += 1
            if combiner:
                a = local.get(key)
                local[key] = (val, 1) if a is None else (a[0] + val, a[1] + 1)
            else:
                raw.append((key, (val, 1)))
        outputs.append(list(local.items()) if combiner else raw)
    return outputs, stats


def shuffle_stage(map_outputs, n_reducers):
    buckets = [[] for _ in range(n_reducers)]
    for out in map_outputs:
        for key, val in out:
            buckets[partition_of(key, n_reducers)].append((key, val))
    nbytes = sum(len(pickle.dumps(b, protocol=4)) for b in buckets)
    return buckets, nbytes


def reduce_stage(buckets):
    results, load = {}, []
    for b in buckets:
        agg, n_raw = {}, 0
        for key, (s, c) in b:
            a = agg.get(key)
            agg[key] = (s, c) if a is None else (a[0] + s, a[1] + c)
            n_raw += c
        load.append({"partial_records": len(b), "raw_records": n_raw, "keys": len(agg)})
        for key, (s, c) in agg.items():
            results[key] = s / c
    return results, load


def run_job(path, n_splits=8, n_reducers=4, combiner=True):
    """Run the whole job; return (averages, metrics)."""
    t = {}
    t0 = time.perf_counter()
    splits = input_splits(path, n_splits)
    outs, st = map_stage(path, splits, combiner)
    t["map"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    buckets, nbytes = shuffle_stage(outs, n_reducers)
    t["shuffle"] = time.perf_counter() - t0
    t0 = time.perf_counter()
    res, load = reduce_stage(buckets)
    t["reduce"] = time.perf_counter() - t0
    shuffle_records = sum(len(b) for b in buckets)
    metrics = {"stage_seconds": t, "total_seconds": sum(t.values()), "splits": n_splits,
               "reducers": n_reducers, "combiner": combiner, "shuffle_records": shuffle_records,
               "shuffle_bytes": nbytes, "reducer_load": load, **st}
    return res, metrics


def single_process_reference(path, limit=None):
    """Simple single-process computation (plain dict loop) for comparison on a small sample."""
    acc = {}
    with open(path) as f:
        next(f)
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            key, val = parse_line(line)
            if key is None:
                continue
            s, c = acc.get(key, (0.0, 0))
            acc[key] = (s + val, c + 1)
    return {k: s / c for k, (s, c) in acc.items()}
