#!/usr/bin/env python3
"""TASK 8 - security validation: inspect isolation properties in practice (harmless, read-only checks).

Checks
  1. Host: kernel, SMT state, CPU-vulnerability mitigations (KPTI etc.), hardware virtualization.
  2. Kernel sharing: does `uname -r` inside each runtime equal the host kernel?
       runc container -> same kernel (shared-kernel trust boundary)
       Kata / gVisor / VM -> different kernel (separate guest kernel / user-space kernel)
  3. Container isolation: namespaces, cgroup limits, capabilities, seccomp.
Writes results/security_validation.json and prints a summary.   NO exploit code is run.
"""
import argparse
import json
import os
import platform
import shutil
from pathlib import Path

from _common import RESULTS
from educloud.backends import sh


def read(path: str) -> str:
    try:
        return Path(path).read_text().strip()
    except OSError:
        return "n/a"


def host_checks() -> dict:
    vuln = {p.name: p.read_text().strip() for p in sorted(Path("/sys/devices/system/cpu/vulnerabilities").glob("*"))} \
        if Path("/sys/devices/system/cpu/vulnerabilities").exists() else {}
    cpuinfo = read("/proc/cpuinfo")
    return {
        "kernel": platform.release(),
        "smt_active": read("/sys/devices/system/cpu/smt/active"),
        "smt_control": read("/sys/devices/system/cpu/smt/control"),
        "hw_virtualization_flag": "vmx" if " vmx" in cpuinfo else "svm" if " svm" in cpuinfo else "none",
        "dev_kvm_present": os.path.exists("/dev/kvm"),
        "running_under_hypervisor (nested?)": " hypervisor" in cpuinfo,
        "cpu_vulnerability_status": vuln,
        "kpti_active": "PTI" in vuln.get("meltdown", ""),
    }


def runtime_checks(image: str, runtimes: list[str], engine: str) -> dict:
    host_kernel = platform.release()
    out = {}
    probe = ("uname -r; echo ---; cat /proc/self/status | grep -E 'CapEff|Seccomp:'; echo ---; "
             "ls -l /proc/self/ns | awk '{print $9, $10, $11}' | tail -n +2; echo ---; "
             "cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max 2>/dev/null")
    for rt in runtimes:
        flag = "" if rt == "runc" else f"--runtime={rt}"
        r = sh(f"{engine} run --rm --cpus=1 --memory=512m {flag} {image} sh -c '{probe}'", 120)
        if r.returncode != 0:
            out[rt] = {"available": False, "note": r.stdout.strip()[-200:]}
            continue
        parts = [p.strip() for p in r.stdout.split("---")]
        guest_kernel = parts[0].splitlines()[0]
        out[rt] = {"available": True, "guest_kernel": guest_kernel,
                   "shares_host_kernel": guest_kernel == host_kernel,
                   "caps_and_seccomp": parts[1] if len(parts) > 1 else "",
                   "namespaces": parts[2].splitlines() if len(parts) > 2 else [],
                   "cgroup_limits(memory.max, cpu.max)": parts[3].splitlines() if len(parts) > 3 else []}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--image", default="ubuntu:24.04")
    ap.add_argument("--engine", default="docker")
    ap.add_argument("--runtimes", nargs="+", default=["runc", "runsc", "kata"])
    a = ap.parse_args()

    report = {"host": host_checks()}
    if shutil.which(a.engine):
        report["runtimes"] = runtime_checks(a.image, a.runtimes, a.engine)
        report["lsns_host"] = sh("lsns 2>/dev/null | head -20").stdout.strip()
    else:
        report["runtimes"] = f"{a.engine} not installed - install it to run the container checks"

    (RESULTS / "security_validation.json").write_text(json.dumps(report, indent=2))
    h = report["host"]
    print(f"Host kernel {h['kernel']} | SMT active={h['smt_active']} | KPTI active={h['kpti_active']} | "
          f"HW virt={h['hw_virtualization_flag']} | /dev/kvm={h['dev_kvm_present']}")
    if isinstance(report["runtimes"], dict):
        for rt, info in report["runtimes"].items():
            if info.get("available"):
                print(f"  {rt:6s}: guest kernel {info['guest_kernel']:28s} shares host kernel: {info['shares_host_kernel']}")
            else:
                print(f"  {rt:6s}: not available ({info['note'][:80]})")
    print(f"\nFull report: {RESULTS / 'security_validation.json'}")


if __name__ == "__main__":
    main()
