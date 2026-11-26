#!/usr/bin/env python3
"""Synthetic gate-log generator (seeded => reproducible).

usage: python generate_logs.py OUT.csv --size-mb 10 [--days 3] [--stations 120]
                               [--hot-station S001 --hot-share 0.7]
                               [--malformed 0.0] [--seed 42]
"""
import argparse
import random


def generate(path, size_mb=None, records=None, days=3, stations=120, hot=None,
             hot_share=0.0, malformed=0.0, seed=42, exit_share=0.5,
             start="2026-03-02"):
    rnd = random.Random(seed)
    y, m, d0 = (int(x) for x in start.split("-"))
    hw = [1, 1, 1, 1, 2, 4, 8, 14, 16, 9, 6, 6, 7, 6, 6, 7, 10, 15, 16, 10, 6, 4, 2, 1]
    hours = list(range(24))
    target = None if size_mb is None else int(size_mb * 1024 * 1024)
    written, n = 0, 0
    with open(path, "w", newline="") as f:
        while True:
            if records is not None and n >= records:
                break
            if target is not None and written >= target:
                break
            if hot and rnd.random() < hot_share:
                st = hot
            else:
                st = f"S{rnd.randint(1, stations):03d}"
            hh = rnd.choices(hours, hw)[0]
            ts = f"{y}-{m:02d}-{d0 + rnd.randrange(days):02d} {hh:02d}:{rnd.randrange(60):02d}:{rnd.randrange(60):02d}"
            tap = "EXIT" if rnd.random() < exit_share else "ENTRY"
            fare = f"{rnd.choice([10, 15, 20, 25, 30, 40]):.2f}" if tap == "EXIT" else "0.00"
            line = f"{ts},{st},G{rnd.randint(1, 8)},C{rnd.randint(0, 999999):09d},{tap},{fare}"
            if malformed and rnd.random() < malformed:
                line = rnd.choice([
                    f"{ts},{st},G1,C000000001,ENTRY",
                    f"{ts},{st},G1,C000000001,EXIT,abc",
                    f"garbage-line-{n}",
                    f"{ts},{st},G1,C000000001,TAPIN,0.00",
                ])
            f.write(line + "\n")
            written += len(line) + 1
            n += 1
    return n, written


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--size-mb", type=float)
    ap.add_argument("--records", type=int)
    ap.add_argument("--days", type=int, default=3)
    ap.add_argument("--stations", type=int, default=120)
    ap.add_argument("--hot-station")
    ap.add_argument("--hot-share", type=float, default=0.0)
    ap.add_argument("--malformed", type=float, default=0.0)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()
    if a.size_mb is None and a.records is None:
        ap.error("give --size-mb or --records")
    n, w = generate(a.out, a.size_mb, a.records, a.days, a.stations, a.hot_station,
                    a.hot_share, a.malformed, a.seed)
    print(f"wrote {n:,} records, {w/1048576:.2f} MB -> {a.out}")
