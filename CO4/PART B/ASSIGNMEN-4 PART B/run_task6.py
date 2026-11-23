"""TASK 6 - Fraud-link detector: naive O(n^2) vs keyed sliding window.   Run: python run_task6.py"""
import os, sys, json, subprocess, statistics, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common.utils import *
from task6.detector import naive, keyed, keyed_events, generate, evidence

plt.rcParams["font.family"] = "Liberation Serif"
banner("TASK 6 - FRAUD-LINK DETECTOR (rule: >=3 distinct beneficiaries within 7 days)"); env = env_info(); out = {}
print("ENVIRONMENT:", json.dumps({k: env[k] for k in ("python", "cpu", "cpu_cores", "ram_gb", "numpy")}))

# ---- 6.1 Part I events (placeholder - see note)
p1 = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tests", "part1_events.json")))
ev = [tuple(e) for e in p1["events"]]
print("\n6.1 PART I EVENTS (%d events; NOTE: %s)" % (len(ev), "placeholders - the original eight events were not supplied"))
for e in ev: print("   ", e)
fn, fk = naive(ev), keyed_events(ev)
print("naive flagged: %s | keyed flagged: %s | expected: %s -> %s" % (sorted(fn), sorted(fk), p1["expected_flagged"], "MATCH" if fn == fk == set(p1["expected_flagged"]) else "MISMATCH"))

for acc in sorted(fn):
    d0, win = evidence(ev, acc); print("  FLAGGED %s : window days %d..%d  events (day, beneficiary) = %s  distinct beneficiaries = %s" % (acc, d0, d0 + 6, win, sorted({b for _, b in win})))
# ---- 6.2 hand-verified 20-event case
E = [("X", 1, "b1"), ("X", 3, "b2"), ("X", 7, "b3"), ("Y", 1, "b1"), ("Y", 3, "b2"), ("Y", 8, "b3"),
     ("Z", 2, "b1"), ("Z", 2, "b1"), ("Z", 2, "b1"), ("Z", 2, "b1"), ("P", 1, "b1"), ("P", 2, "b2"), ("P", 3, "b2"), ("P", 4, "b3"),
     ("Q", 10, "b1"), ("Q", 12, "b2"), ("Q", 20, "b3"), ("S", 3, "b1"), ("S", 3, "b2"), ("S", 3, "b3")]
hand = {"X", "P", "S"}
print("\n6.2 HAND-VERIFIED 20-EVENT TEST (expected flagged derived by hand BEFORE running: X, P, S)")
print("  X: days 1,3,7 -> window [1..7] holds b1,b2,b3 (day 7 = d+6 is INSIDE)          -> flag")
print("  Y: days 1,3,8 -> [1..7]={b1,b2}, [3..9]={b2,b3}; day 8 is 7 days after day 1   -> no flag")
print("  Z: four payments to the same b1                                                   -> no flag (1 distinct)")
print("  P: days 1-4 -> b1,b2,b3 all inside one window                                      -> flag")
print("  Q: days 10,12,20 -> never 3 distinct inside 7 days                                 -> no flag")
print("  S: three different beneficiaries on the SAME day 3                                 -> flag")
fn, fk = naive(E), keyed_events(E)
print("naive: %s | keyed: %s | hand: %s -> %s" % (sorted(fn), sorted(fk), sorted(hand), "ALL AGREE" if fn == fk == hand else "DISAGREE"))
for acc in sorted(fn):
    d0, win = evidence(E, acc); print("  FLAGGED %s : window days %d..%d  events (day, beneficiary) = %s" % (acc, d0, d0 + 6, win))
out["hand"] = {"naive": sorted(fn), "keyed": sorted(fk), "hand": sorted(hand), "agree": fn == fk == hand}

# ---- 6.3 scaling
print("\n6.3 SCALING (events = n, accounts = n/10, 50 beneficiaries, 365 days)")
nv = {}
print("NAIVE all-pairs (measured; agreement with keyed checked at every size):")
for n, reps in ((1000, 3), (2000, 3), (5000, 3), (10000, 1)):
    a, d, b = generate(n); evs = list(zip(a.tolist(), d.tolist(), b.tolist())); ts = []
    for _ in range(reps):
        t0 = time.perf_counter(); fnv = naive(evs); ts.append(time.perf_counter() - t0)
    fk, _, _ = keyed(a, d, b); nv[n] = (statistics.mean(ts), statistics.stdev(ts) if reps > 1 else 0.0)
    print("  n=%6d : %8.3f +/- %.3f s (%d run%s)  flagged=%d  agrees with keyed: %s" % (n, nv[n][0], nv[n][1], reps, "s" if reps > 1 else "", len(fnv), fnv == fk))
xs = np.array(sorted(nv)); ys = np.array([nv[k][0] for k in xs]); slope, ic = np.polyfit(np.log(xs), np.log(ys), 1)
print("  fitted growth: time ~ n^%.2f  (quadratic expected = 2)" % slope)
print("KEYED sliding window (measured, one fresh process per size for clean memory):")
kv = {}
for n in (10_000, 100_000, 1_000_000, 10_000_000):
    runs = [json.loads(subprocess.run([sys.executable, "-m", "task6.bench", str(n)], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))).stdout) for _ in range(3 if n <= 1_000_000 else 1)]
    kv[n] = {"mean": statistics.mean(r["seconds"] for r in runs), "sd": statistics.stdev(r["seconds"] for r in runs) if len(runs) > 1 else 0.0, "rss": max(r["rss_mb"] for r in runs), "flagged": runs[0]["flagged"], "runs": len(runs)}
    print("  n=%8d : %8.3f +/- %.3f s (%d run%s)  peak RSS %.0f MB  flagged accounts=%d" % (n, kv[n]["mean"], kv[n]["sd"], len(runs), "s" if len(runs) > 1 else "", kv[n]["rss"], kv[n]["flagged"]))
print("%-10s %-24s %-24s %s" % ("events", "naive", "keyed", "speed-up"))
tab = []
for n in (10_000, 100_000, 1_000_000, 10_000_000):
    nt = np.exp(ic) * n ** slope; meas = n in nv
    tab.append({"n": n, "naive": nv[n][0] if meas else nt, "naive_measured": meas, "keyed": kv[n]["mean"]})
    print("%-10d %-24s %-24s x%.0f" % (n, ("%.2f s (measured)" % nv[n][0]) if meas else ("%.3g s = %.3g h (EXTRAPOLATED)" % (nt, nt / 3600)), "%.2f s (measured)" % kv[n]["mean"], tab[-1]["naive"] / kv[n]["mean"]))
out["naive"] = {str(k): v for k, v in nv.items()}; out["keyed"] = {str(k): v for k, v in kv.items()}; out["slope"] = slope; out["table"] = tab

# ---- 6.4 skew
print("\n6.4 SKEW TEST (1,000,000 events; hot account receives 50% of all events) - keyed algorithm")
runs = {}
for lab, hot in (("uniform", 0.0), ("hot account 50%", 0.5)):
    r = json.loads(subprocess.run([sys.executable, "-m", "task6.bench", "1000000", str(hot)], capture_output=True, text=True, cwd=os.path.dirname(os.path.abspath(__file__))).stdout); runs[lab] = r
    print("  %-16s %.3f s  flagged=%d  largest per-account window state: %d events / %d distinct beneficiaries  peak RSS %.0f MB" % (lab, r["seconds"], r["flagged"], r["max_deque"], r["max_distinct"], r["rss_mb"]))
import zlib
for lab, hot in (("uniform", 0.0), ("hot account 50%", 0.5)):
    a, _, _ = generate(1_000_000, hot_share=hot); part = np.bincount((a.astype(np.int64) * 2654435761) % 8, minlength=8)
    print("  8 hash partitions by account (%-16s): events per partition %s  max/mean = %.2f" % (lab, part.tolist(), part.max() / part.mean()))
    runs[lab]["partitions"] = part.tolist()
out["skew"] = runs
save_json("task6_results.json", out)

fig, ax = plt.subplots(1, 2, figsize=(11, 4.0)); ns = [t["n"] for t in tab]
ax[0].loglog(ns, [t["naive"] for t in tab], "o--", color="#c55a11", label="naive (measured to 10k, then extrapolated)"); ax[0].loglog(ns, [t["keyed"] for t in tab], "s-", color="#1f4e79", label="keyed (all measured)")
ax[0].loglog(list(nv), [nv[k][0] for k in nv], "o", color="#c55a11", ms=9, mfc="none"); ax[0].set_xlabel("events"); ax[0].set_ylabel("seconds"); ax[0].set_title("(a) Run time vs input size"); ax[0].legend(fontsize=8)
for i, lab in enumerate(runs): ax[1].bar(np.arange(8) + (i - 0.5) * 0.4, np.array(runs[lab]["partitions"]) / 1e3, 0.4, label=lab)
ax[1].set_xlabel("partition (hash of account)"); ax[1].set_ylabel("events (thousands)"); ax[1].set_title("(b) Partition load under skew"); ax[1].legend(fontsize=8)
for a_ in ax: a_.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "fig_task6.png"), dpi=170); plt.close()
print("\nSaved results/task6_results.json and figures/fig_task6.png")
