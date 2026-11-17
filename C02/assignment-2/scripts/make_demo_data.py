#!/usr/bin/env python3
"""Generate SYNTHETIC *DEMO* data so you can test the analysis pipeline before you have real results.

!!  These numbers are produced by a toy formula + random noise.  They are NOT measurements.
!!  Never put them in your report.  Real data comes from scripts/task8_run_benchmarks.py.
Writes data/demo/results.csv (git-ignored).
"""
import csv
import random
from _common import ROOT
from educloud.config import APPROACHES, MODEL_KEY

FIELDS = ["approach", "scenario", "instances", "noise", "mitigation", "smt_active", "run",
          "cpu_eps", "cpu_lat_mean_ms", "cpu_lat_p95_ms", "disk_iops", "disk_mbps", "disk_lat_mean_ms",
          "disk_lat_p95_ms", "net_gbps", "mem_bogo_ops_s", "steal_pct", "startup_s", "mem_footprint_mb", "timestamp"]
CORES, REPS = 8, 5
BASE = dict(cpu=1000.0, disk=2800.0, net=22.0, mem=90000.0)
STARTUP = {"baremetal": 0.0, "docker": 1.2, "gvisor": 1.6, "kata": 4.5, "kvm": 18.0}
FOOT = {"baremetal": 0, "docker": 120, "gvisor": 160, "kata": 256, "kvm": 1024}
NOISE_P = {"none": 1.0, "cpu": 1.35, "disk": 1.2, "mem": 1.15}


def row(approach, scenario, n, noise, mitigation, run, rng):
    key = MODEL_KEY.get(approach)
    h = APPROACHES[key].h_cpu if key else 0.0
    hio = APPROACHES[key].h_io if key else 0.0
    if mitigation == "smt_off":
        h += 0.03
    victims = n if scenario == "scaling" else 1
    share = min(1.0, CORES / max(n, 1))
    jitter = lambda: rng.gauss(1.0, 0.025)
    cpu = BASE["cpu"] * (1 - h) * share * jitter()
    pen = NOISE_P[noise] if scenario == "interference" else 1.0
    lat = 1000.0 / cpu * pen
    disk = BASE["disk"] * (1 - hio) / n * jitter() / (pen if scenario == "interference" else 1)
    return {"approach": approach, "scenario": scenario, "instances": n, "noise": noise,
            "mitigation": mitigation, "smt_active": 0 if mitigation == "smt_off" else 1, "run": run,
            "cpu_eps": cpu, "cpu_lat_mean_ms": lat, "cpu_lat_p95_ms": lat * rng.gauss(1.45, 0.05) * pen,
            "disk_iops": disk * 250, "disk_mbps": disk, "disk_lat_mean_ms": 0.2 * n ** 0.5 * pen * jitter(),
            "disk_lat_p95_ms": 0.5 * n ** 0.5 * pen * jitter(),
            "net_gbps": min(BASE["net"], 25 * (1 - hio) / n) * jitter(),
            "mem_bogo_ops_s": BASE["mem"] * (1 - h) * share * jitter(),
            "steal_pct": max(0.0, (1 - share) * 100 * (0.6 if approach != "docker" else 0.2)) + rng.random(),
            "startup_s": STARTUP[approach] * jitter(), "mem_footprint_mb": FOOT[approach] * jitter(),
            "timestamp": "DEMO"}


def main():
    rng = random.Random(42)
    out = ROOT / "data" / "demo" / "results.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        w.writeheader()
        for run in range(1, REPS + 1):
            w.writerow(row("baremetal", "scaling", 1, "none", "none", run, rng))
            for ap in ("docker", "gvisor", "kata", "kvm"):
                for n in (1, 2, 4, 8, 16):
                    w.writerow(row(ap, "scaling", n, "none", "none", run, rng))
                for noise in ("none", "cpu", "disk"):
                    w.writerow(row(ap, "interference", 4, noise, "none", run, rng))
                w.writerow(row(ap, "scaling", 8, "none", "smt_off", run, rng))
    print(f"DEMO data written to {out}  (synthetic - do NOT report as measurements)")


if __name__ == "__main__":
    main()
