#!/usr/bin/env python3
"""B4.1 - controlled failure injection, emulating YARN task-attempt retry semantics.

mapreduce.map.maxattempts = 4 (Hadoop default).  A 'poison' record makes the mapper raise.
Scenario 1: transient failure (fails on attempts 1-2 only, e.g. bad node) -> job SUCCEEDS.
Scenario 2: permanent failure (record always fails)                          -> job FAILS.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(__file__))
from mr_local import make_splits, read_split
from transit_mr import q1_map, sum_reduce

ROOT = os.path.join(os.path.dirname(__file__), "..")
MAX_ATTEMPTS = 4
POISON = "C666666666"


def build(path):
    from generate_logs import generate
    generate(path, records=3000, days=1, seed=5)
    lines = open(path).read().splitlines()
    lines[1700] = "2026-03-02 09:09:09,S042,G1,%s,ENTRY,0.00" % POISON
    open(path, "w").write("\n".join(lines) + "\n")


def run(path, mode):
    print(f"\n===== SCENARIO: {mode.upper()} failure | mapreduce.map.maxattempts={MAX_ATTEMPTS} =====")
    splits = make_splits(path, 40000)
    nodes = ["node1", "node2", "node3"]
    out, failed_job = [], False
    print(f"job_0001 submitted: {len(splits)} map tasks, 1 reduce task")
    for t, (off, ln) in enumerate(splits):
        for attempt in range(MAX_ATTEMPTS):
            node = nodes[(t + attempt) % 3]
            tid = f"attempt_0001_m_{t:06d}_{attempt}"
            lines = list(read_split(path, off, ln))

            def mapper(ls, counter):
                for l in ls:
                    if POISON in l and (mode == "permanent" or attempt < 2):
                        raise RuntimeError(f"Mapper crashed on record: ...{POISON}...")
                    yield from q1_map([l], counter)
            try:
                res = list(mapper(lines, lambda *a: None))
                print(f"  {tid} on {node}: SUCCEEDED")
                out += res
                break
            except RuntimeError as e:
                print(f"  {tid} on {node}: FAILED  ({e})")
        else:
            print(f"  task m_{t:06d} exhausted {MAX_ATTEMPTS} attempts -> TASK FAILED")
            failed_job = True
            break
    if failed_job:
        print("job_0001 state: FAILED  (remaining tasks KILLED, no output committed, _SUCCESS marker absent)")
        return None
    out.sort(key=lambda s: s.split("\t")[0])
    final = list(sum_reduce(iter(out)))
    print(f"job_0001 state: SUCCEEDED ; reduce output rows = {len(final)} ; failed attempts counted = 2")
    return final


if __name__ == "__main__":
    p = os.path.join(ROOT, "data", "failure_test.csv")
    build(p)
    a = run(p, "transient")
    b = run(p, "permanent")
