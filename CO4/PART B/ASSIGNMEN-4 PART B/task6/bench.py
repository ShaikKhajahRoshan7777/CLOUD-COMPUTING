"""Run one keyed benchmark in a fresh process so peak RSS is clean:  python -m task6.bench <n> [hot_share]"""
import json, resource, sys, time
from task6.detector import generate, keyed
n = int(sys.argv[1]); hot = float(sys.argv[2]) if len(sys.argv) > 2 else 0.0
a, d, b = generate(n, hot_share=hot); base = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
t0 = time.perf_counter(); f, mq, mc = keyed(a, d, b); el = time.perf_counter() - t0
print(json.dumps({"n": n, "seconds": el, "flagged": len(f), "max_deque": mq, "max_distinct": mc, "rss_mb": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, "rss_before_mb": base / 1024}))
