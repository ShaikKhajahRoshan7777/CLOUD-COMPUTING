#!/usr/bin/env python3
"""TASK 8 / 9 - run the CPU, disk, network and memory benchmarks on N co-located instances.

Examples
--------
  # baseline on the host (1 process)
  python scripts/task8_run_benchmarks.py --approach baremetal --instances 1 --reps 5

  # scaling test, containers, 1 -> 2 -> 4 -> 8 -> 16 instances, 5 repetitions
  python scripts/task8_run_benchmarks.py --approach docker --instances 1 2 4 8 16 --reps 5 \
         --iperf-server 172.17.0.1

  # noisy-neighbour experiment (victim = instance 0, 3 noisy neighbours)
  python scripts/task8_run_benchmarks.py --approach docker --scenario interference --instances 4 \
         --noise none cpu disk mem --reps 5

  # same test with a mitigation applied by hand (record its name in the CSV)
  sudo scripts/task8_toggle_smt.sh off
  python scripts/task8_run_benchmarks.py --approach docker --instances 8 --mitigation smt_off

  # show what would run without running anything
  python scripts/task8_run_benchmarks.py --approach docker --instances 2 --dry-run

All rows go to data/results/results.csv (appended).  One row = one repetition; per-instance
metrics are averaged over the N instances (scaling) or taken from the victim (interference).
"""
import argparse
import csv
import math
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from _common import ROOT
from educloud import parsers, workloads
from educloud.backends import BACKENDS, sh

OUT = ROOT / "data" / "results" / "results.csv"
FIELDS = ["approach", "scenario", "instances", "noise", "mitigation", "smt_active", "run",
          "cpu_eps", "cpu_lat_mean_ms", "cpu_lat_p95_ms",
          "disk_iops", "disk_mbps", "disk_lat_mean_ms", "disk_lat_p95_ms",
          "net_gbps", "mem_bogo_ops_s", "steal_pct", "startup_s", "mem_footprint_mb", "timestamp"]


def smt_active() -> str:
    try:
        return Path("/sys/devices/system/cpu/smt/active").read_text().strip()
    except OSError:
        return "unknown"


def mean(vals):
    vals = [v for v in vals if v is not None and not math.isnan(v)]
    return sum(vals) / len(vals) if vals else float("nan")


def run_parallel(backend, insts, cmd, timeout):
    with ThreadPoolExecutor(max_workers=len(insts)) as ex:
        return list(ex.map(lambda i: backend.exec(i, cmd, timeout), insts))


def timed_workload(backend, insts, cmd, parser, timeout, dry):
    """Run `cmd` on all instances at once; return parsed metrics (list per instance) and steal %."""
    before = [backend.read_steal(i) for i in insts]
    outs = run_parallel(backend, insts, cmd, timeout)
    after = [backend.read_steal(i) for i in insts]
    if dry:
        return [{} for _ in insts], float("nan")
    steals = []
    for (s0, t0), (s1, t1) in zip(before, after):
        steals.append(100.0 * (s1 - s0) / (t1 - t0) if t1 > t0 else 0.0)
    parsed = []
    for o in outs:
        try:
            parsed.append(parser(o))
        except Exception as e:                       # keep going, but make the failure visible
            print(f"  ! parse error ({e}); first 200 chars: {o[:200]!r}", file=sys.stderr)
            parsed.append({})
    return parsed, mean(steals)


def measure_set(backend, insts, args, iperf_ports, victims):
    """Run cpu -> disk -> mem -> net on `victims` and return the merged metric dict."""
    row, steals = {}, []
    d = args.duration
    jobs = [("cpu", workloads.cpu(d), parsers.parse_sysbench_cpu),
            ("disk", workloads.disk(d, direct=not args.no_direct), parsers.parse_fio_json),
            ("mem", workloads.memory(d), parsers.parse_stress_ng_vm)]
    if args.iperf_server:
        jobs.append(("net", None, parsers.parse_iperf3_json))
    for name, cmd, parser in jobs:
        if name == "net":                            # each instance talks to its own iperf3 server
            before = [backend.read_steal(i) for i in victims]
            with ThreadPoolExecutor(max_workers=len(victims)) as ex:
                outs = list(ex.map(lambda ip: backend.exec(
                    ip[1], workloads.network(args.iperf_server, iperf_ports[ip[0]], d), d + 60),
                    enumerate(victims)))
            after = [backend.read_steal(i) for i in victims]
            parsed = []
            for o in outs:
                if args.dry_run:
                    parsed.append({})
                    continue
                try:
                    parsed.append(parser(o))
                except Exception as e:
                    print(f"  ! iperf3 parse error ({e})", file=sys.stderr)
                    parsed.append({})
            st = mean([100.0 * (b[0] - a_[0]) / (b[1] - a_[1]) for a_, b in zip(before, after) if b[1] > a_[1]]) \
                if not args.dry_run else float("nan")
        else:
            parsed, st = timed_workload(backend, victims, cmd, parser, d + 120, args.dry_run)
        steals.append(st)
        for key in {k for p in parsed for k in p}:
            row[key] = mean([p.get(key) for p in parsed])
    row["steal_pct"] = mean(steals)
    return row


def start_iperf_servers(n, args):
    if not args.iperf_server or args.dry_run:
        return [], [5201 + i for i in range(n)]
    ports = [5201 + i for i in range(n)]
    procs = [subprocess.Popen(["iperf3", "-s", "-p", str(p)], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL) for p in ports]
    time.sleep(1.0)
    return procs, ports


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--approach", required=True, choices=list(BACKENDS))
    ap.add_argument("--scenario", default="scaling", choices=["scaling", "interference"])
    ap.add_argument("--instances", type=int, nargs="+", default=[1, 2, 4, 8, 16])
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--duration", type=int, default=30, help="seconds per workload")
    ap.add_argument("--noise", nargs="+", default=["none", "cpu", "disk"],
                    help="interference scenario: noisy-neighbour kinds (none cpu disk mem)")
    ap.add_argument("--mitigation", default="none", help="label stored in the CSV (e.g. smt_off, kpti, seccomp)")
    ap.add_argument("--iperf-server", help="IP of the host as seen from the instances (enables the network test)")
    ap.add_argument("--no-direct", action="store_true", help="fio --direct=0 (use if the FS rejects O_DIRECT)")
    ap.add_argument("--image", default="educloud-bench:latest", help="container image (docker/gvisor/kata)")
    ap.add_argument("--engine", default="docker", help="docker or podman")
    ap.add_argument("--kvm-domains", default="", help="comma list of libvirt domain names")
    ap.add_argument("--kvm-ips", default="", help="comma list of guest IPs (same order)")
    ap.add_argument("--kvm-user", default="ubuntu")
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--dry-run", action="store_true", help="print commands, run nothing")
    args = ap.parse_args()

    cls = BACKENDS[args.approach]
    kw = {"dry_run": args.dry_run}
    if args.approach in ("docker", "gvisor", "kata"):
        kw.update(image=args.image, engine=args.engine)
    if args.approach == "kvm":
        kw.update(domains=[d for d in args.kvm_domains.split(",") if d],
                  ips=[i for i in args.kvm_ips.split(",") if i], user=args.kvm_user)

    out = Path(os.devnull) if args.dry_run else Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    new_file = args.dry_run or not out.exists()
    print(f"host: {platform.node()}  kernel: {platform.release()}  cpus: {os.cpu_count()}  SMT active: {smt_active()}")

    with out.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        for n in args.instances:
            backend = cls(**kw)
            procs, ports = start_iperf_servers(n, args)
            try:
                print(f"\n== {args.approach}: starting {n} instance(s)")
                insts = backend.start(n)
                startup = mean([i.startup_s for i in insts])
                footprint = mean([backend.memory_mb(i) for i in insts])
                conds = [None] if args.scenario == "scaling" else args.noise
                for noise in conds:
                    for rep in range(1, args.reps + 1):
                        print(f"-- n={n} scenario={args.scenario} noise={noise} run {rep}/{args.reps}")
                        if args.scenario == "scaling":
                            victims, bg = insts, []
                        else:
                            if n < 2 and noise not in (None, "none"):
                                raise SystemExit("interference needs >= 2 instances (1 victim + noisy neighbours)")
                            victims, bg = insts[:1], insts[1:]
                        ex = ThreadPoolExecutor(max_workers=max(1, len(bg)))
                        futs = []
                        if bg and noise not in (None, "none"):
                            cmd = workloads.noise(noise, args.duration * 4 + 30)
                            futs = [ex.submit(backend.exec, b, cmd, args.duration * 4 + 120) for b in bg]
                            time.sleep(3)             # let the noise ramp up
                        row = measure_set(backend, insts, args, ports, victims)
                        for f in futs:
                            f.result()
                        ex.shutdown()
                        row.update(approach=args.approach, scenario=args.scenario, instances=n,
                                   noise=noise or "none", mitigation=args.mitigation,
                                   smt_active=smt_active(), run=rep, startup_s=startup,
                                   mem_footprint_mb=footprint,
                                   timestamp=time.strftime("%Y-%m-%dT%H:%M:%S"))
                        if not args.dry_run:
                            w.writerow({k: row.get(k, "") for k in FIELDS})
                            fh.flush()
            finally:
                backend.stop()
                for p in procs:
                    p.terminate()
    print(f"\nDone. Results appended to {out}")


if __name__ == "__main__":
    main()
