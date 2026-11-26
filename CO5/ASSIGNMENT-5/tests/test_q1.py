#!/usr/bin/env python3
"""B2.1 - validation tests for Q1 (run: python tests/test_q1.py)."""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from mr_local import run_job
from transit_mr import q1_map, sum_reduce
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")
os.makedirs(DATA, exist_ok=True)

SAMPLE = [  # A3.3 trace sample: 10 records, 3 stations, two splits of 5 lines each
    "2026-03-02 08:05:10,S001,G1,C000000001,ENTRY,0.00",
    "2026-03-02 08:20:44,S001,G2,C000000002,ENTRY,0.00",
    "2026-03-02 08:31:09,S002,G1,C000000003,ENTRY,0.00",
    "2026-03-02 08:45:00,S001,G1,C000000004,EXIT,20.00",
    "2026-03-02 09:02:31,S003,G4,C000000005,ENTRY,0.00",
    "2026-03-02 08:50:12,S002,G2,C000000006,ENTRY,0.00",
    "2026-03-02 09:10:15,S001,G3,C000000007,ENTRY,0.00",
    "2026-03-02 09:15:59,S003,G1,C000000008,ENTRY,0.00",
    "2026-03-02 09:40:03,S002,G2,C000000009,EXIT,15.00",
    "2026-03-02 09:55:27,S001,G2,C000000010,ENTRY,0.00",
]
MALFORMED = SAMPLE[:3] + [
    "2026-03-02 08:10:00,S001,G1,C000000011",              # missing fields
    "2026-03-02 08:12:00,S001,G1,C000000012,EXIT,abc",     # non-numeric fare
    "total garbage",
    "2026-03-02 08:14:00,S002,G1,C000000013,ENTRY,0.00",
]
EXIT_ONLY = [
    "2026-03-02 08:45:00,S001,G1,C000000004,EXIT,20.00",
    "2026-03-02 09:40:03,S002,G2,C000000009,EXIT,15.00",
]


def write(name, lines):
    p = os.path.join(DATA, name)
    with open(p, "w") as f:
        f.write("".join(l + "\n" for l in lines))
    return p


def independent(lines):
    """Independent oracle: plain Python, no MapReduce structures."""
    c = Counter()
    for l in lines:
        p = l.split(",")
        if len(p) == 6 and p[4] == "ENTRY":
            try:
                float(p[5])
            except ValueError:
                continue
            c[f"{p[1]}|{p[0][:10]}|{p[0][11:13]}"] += 1
    return sorted(f"{k}\t{v}" for k, v in c.items())


def run(name, lines, split_bytes):
    p = write(name, lines)
    out, C, rep = run_job(p, q1_map, sum_reduce, sum_reduce, 1, split_bytes)
    return sorted(out), C, rep


def check(title, got, want, extra=""):
    ok = got == want
    print(f"[{'PASS' if ok else 'FAIL'}] {title} {extra}")
    if not ok:
        print("   expected:", want); print("   actual  :", got)
    return ok


ok = True
print("TEST 1 - hand-checkable sample (10 records, 2 splits => 2 map tasks)")
split = sum(len(l) + 1 for l in SAMPLE[:5])
got, C, rep = run("sample.csv", SAMPLE, split)
hand = ["S001|2026-03-02|08\t2", "S001|2026-03-02|09\t2", "S002|2026-03-02|08\t2", "S003|2026-03-02|09\t2"]
for l in got: print("   ", l)
ok &= check("hand-computed answer", got, sorted(hand))
ok &= check("independent oracle", got, independent(SAMPLE))
print("    counters:", {k: v for k, v in C.items() if "Map" in k or "Transit" in k})
print("\nTEST 2 - malformed records are skipped AND counted")
got, C, rep = run("malformed.csv", MALFORMED, 10**6)
ok &= check("valid records still aggregated", got, independent(MALFORMED))
ok &= check("MalformedRecords counter == 3", C.get("Transit.MalformedRecords"), 3)
print("\nTEST 3a - boundary: empty file")
got, C, rep = run("empty.csv", [], 10**6)
ok &= check("empty input -> empty output, no crash", got, [])
print("\nTEST 3b - boundary: only EXIT taps")
got, C, rep = run("exit_only.csv", EXIT_ONLY, 10**6)
ok &= check("EXIT-only input -> empty output", got, [])
ok &= check("ExitTapsSkipped counter == 2", C.get("Transit.ExitTapsSkipped"), 2)
print("\nTEST 4 - split-boundary integrity (many tiny splits must equal 1 split)")
a, _, _ = run("sample.csv", SAMPLE, 10**6)
b, _, _ = run("sample.csv", SAMPLE, 37)
ok &= check("37-byte splits == single split", a, b)
print("\nOVERALL:", "ALL TESTS PASSED" if ok else "SOME TESTS FAILED")
sys.exit(0 if ok else 1)
