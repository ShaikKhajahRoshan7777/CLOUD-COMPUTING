"""Parsers for benchmark tool output (sysbench, fio --output-format=json, iperf3 -J, stress-ng)."""
import json
import re


def parse_sysbench_cpu(text: str) -> dict:
    eps = re.search(r"events per second:\s*([\d.]+)", text)
    avg = re.search(r"avg:\s*([\d.]+)", text)
    p95 = re.search(r"95th percentile:\s*([\d.]+)", text)
    if not (eps and avg and p95):
        raise ValueError("could not parse sysbench output")
    return {"cpu_eps": float(eps.group(1)), "cpu_lat_mean_ms": float(avg.group(1)),
            "cpu_lat_p95_ms": float(p95.group(1))}


def parse_fio_json(text: str) -> dict:
    """fio prints some warnings before the JSON object, so start at the first '{'."""
    data = json.loads(text[text.index("{"):])
    job = data["jobs"][0]
    iops = bw_bytes = 0.0
    means, p95s = [], []
    for d in ("read", "write"):
        part = job.get(d, {})
        if part.get("io_bytes", 0) > 0:
            iops += part.get("iops", 0.0)
            bw_bytes += part.get("bw_bytes", part.get("bw", 0) * 1024)
            clat = part.get("clat_ns", {})
            if "mean" in clat:
                means.append(clat["mean"])
            p = clat.get("percentile", {})
            for key in ("95.000000", "95.00"):
                if key in p:
                    p95s.append(p[key])
                    break
    if not means:
        raise ValueError("fio output has no completion-latency data")
    return {"disk_iops": iops, "disk_mbps": bw_bytes / 1e6,
            "disk_lat_mean_ms": max(means) / 1e6, "disk_lat_p95_ms": (max(p95s) / 1e6) if p95s else float("nan")}


def parse_iperf3_json(text: str) -> dict:
    data = json.loads(text[text.index("{"):])
    end = data["end"]
    bps = (end.get("sum_received") or end.get("sum_sent") or end["sum"])["bits_per_second"]
    return {"net_gbps": bps / 1e9}


def parse_stress_ng_vm(text: str) -> dict:
    """Bogo ops/s (real time) of the 'vm' stressor from --metrics-brief output."""
    m = re.search(r"\]\s+vm\s+((?:[\d.]+\s+){4,}[\d.]+)", text)
    if not m:
        raise ValueError("could not parse stress-ng metrics")
    nums = [float(x) for x in m.group(1).split()]
    return {"mem_bogo_ops_s": nums[4]}


def parse_proc_stat(line: str) -> tuple[float, float]:
    """Return (steal_jiffies, total_jiffies) from the first line of /proc/stat."""
    f = [float(x) for x in line.split()[1:]]
    steal = f[7] if len(f) > 7 else 0.0
    return steal, sum(f[:8])
