"""Shared helpers: environment report, repeated timing (mean +/- SD), JSON results, paths."""
import json, os, platform, statistics, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RESULTS = os.path.join(ROOT, "results")
FIGURES = os.path.join(ROOT, "figures")
DATA = os.path.join(ROOT, "data")
for _d in (RESULTS, FIGURES, DATA):
    os.makedirs(_d, exist_ok=True)


def env_info():
    """Hardware / software versions required by the assignment."""
    info = {"python": sys.version.split()[0], "os": platform.platform(),
            "cpu_cores": os.cpu_count()}
    try:
        info["cpu"] = [l.split(":")[1].strip() for l in open("/proc/cpuinfo") if "model name" in l][0]
        info["ram_gb"] = round(int(open("/proc/meminfo").readline().split()[1]) / 1048576, 2)
    except Exception:
        pass
    for mod in ("pandas", "numpy", "pyarrow", "pyspark", "cryptography", "matplotlib"):
        try:
            info[mod] = __import__(mod).__version__
        except Exception:
            pass
    return info


def repeat_timed(fn, n=3):
    """Run fn n times; return (last_result, [times], mean, sd)."""
    times, res = [], None
    for _ in range(n):
        t0 = time.perf_counter()
        res = fn()
        times.append(time.perf_counter() - t0)
    sd = statistics.stdev(times) if n > 1 else 0.0
    return res, times, statistics.mean(times), sd


def save_json(name, obj):
    with open(os.path.join(RESULTS, name), "w") as f:
        json.dump(obj, f, indent=2, default=str)


def load_json(name):
    with open(os.path.join(RESULTS, name)) as f:
        return json.load(f)


def banner(title):
    print("=" * 78)
    print(title)
    print("=" * 78)
