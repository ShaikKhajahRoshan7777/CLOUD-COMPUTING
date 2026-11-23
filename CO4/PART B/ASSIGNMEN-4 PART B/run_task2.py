"""TASK 2 - Batch vs Stream: build it, break it, explain it.   Run:  python run_task2.py"""
import os, sys, time, statistics, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common.utils import *
from task2.engines import batch_engine, stream_engine, first_difference, StreamEngine, WINDOW
from task2.datasets import clean_ordered, counterexample, realistic_jitter

plt.rcParams["font.family"] = "Liberation Serif"
banner("TASK 2 - BATCH (Solution A) vs STREAM (Solution B)")
env = env_info(); print("ENVIRONMENT:", json.dumps({k: env[k] for k in ("python", "cpu", "cpu_cores", "ram_gb", "pyspark")}))
fmt = lambda k: "%s [%3d-%3d s)" % (k[0], k[1], k[1] + WINDOW)
out = {}

# ------------------------------------------------------------------ 2.1 normal case
ev = clean_ordered()
A = batch_engine(ev); B, _ = stream_engine(ev, allowed_lateness=10)
print("\n2.1 NORMAL CASE - %d ordered clean events, 3 segments x 5 one-minute windows" % len(ev))
print("%-22s %12s %12s  %s" % ("window", "A: batch", "B: stream", "equal"))
for k in sorted(A):
    print("%-22s %12.4f %12.4f  %s" % (fmt(k), A[k], B[k], "yes" if A[k] == B[k] else "NO"))
print("=> identical on all %d windows: %s" % (len(A), A == B))
out["normal"] = {"windows": len(A), "identical": A == B}

# ------------------------------------------------------------------ 2.2 break the stream
ce = counterexample(); batch = batch_engine(ce)
print("\n2.2 BREAK THE STREAM - hand-designed events (segment A):")
print("%-4s %9s %9s %6s  %s" % ("id", "event ts", "arrival", "speed", "note"))
notes = {"e5": "out of order by 7 s but inside the watermark", "e6": "LATE (arrives 52 s after it happened)"}
seen = set()
for e in ce:
    n = notes.get(e["id"], "")
    if e["id"] in seen: n = "DUPLICATE of the earlier %s" % e["id"]
    seen.add(e["id"]); print("%-4s %9d %9d %6.1f  %s" % (e["id"], e["ts"], e["arrival"], e["speed"], n))
BAD = dict(allowed_lateness=10, dedup_ttl=30)
res, eng, diff, cul = first_difference(ce, batch, **BAD)
print("\nSettings under test: window=60 s, watermark=10 s, de-dup retention=30 s of event time")
print("%-22s %12s %12s  %s" % ("window", "BatchResult", "StreamResult", ""))
for k in sorted(set(batch) | set(res)):
    print("%-22s %12.4f %12.4f  %s" % (fmt(k), batch[k], res.get(k, float('nan')), "<-- DIFFERENT" if k in diff else ""))
print("StreamResult != BatchResult  ->", res != batch)
print("FIRST responsible event : %s (arrival t=%d s, event ts=%d s) -> %s" % (cul[0][0]["id"], cul[0][0]["arrival"], cul[0][0]["ts"], cul[0][1]))
for e, why in cul[1:]:
    print("then                    : %s (arrival t=%d s, event ts=%d s) -> %s" % (e["id"], e["arrival"], e["ts"], why))
print("\nFIX attempts (change one setting at a time):")
fixes = [("watermark 10 s -> 60 s only", dict(allowed_lateness=60, dedup_ttl=30)),
         ("de-dup retention 30 s -> until window closes only", dict(allowed_lateness=10, dedup_ttl=None)),
         ("BOTH: watermark 60 s + de-dup until window closes", dict(allowed_lateness=60, dedup_ttl=None)),
         ("minimum watermark that fixes late event (41 s) + safe de-dup", dict(allowed_lateness=41, dedup_ttl=None)),
         ("watermark 40 s + safe de-dup (one second too small)", dict(allowed_lateness=40, dedup_ttl=None))]
fixrows = []
for label, cfg in fixes:
    r, _ = stream_engine(ce, **cfg); ok = r == batch; fixrows.append({"label": label, "equal": ok})
    print("  %-62s -> StreamResult %s BatchResult" % (label, "==" if ok else "!="))
out["break"] = {"batch": {str(k): v for k, v in batch.items()}, "stream": {str(k): v for k, v in res.items()}, "diff": [str(k) for k in diff],
                "first": cul[0][0]["id"], "culprits": [c[0]["id"] for c in cul], "fixes": fixrows}

# ------------------------------------------------------------------ Spark Structured Streaming confirmation
try:
    from task1 import spark_job
    from task2.spark_stream import run_spark_stream
    sp = spark_job.quiet(spark_job.spark_session(2))
    print("\nAPACHE SPARK %s STRUCTURED STREAMING (file-source micro-batches, append mode):" % sp.version)
    sres = {}
    for L in (10, 60):
        t0 = time.perf_counter(); r = run_spark_stream(sp, ce, L, "wm%d" % L); dt = time.perf_counter() - t0
        sres[L] = {"equal_to_batch": r == batch, "result": {str(k): v for k, v in sorted(r.items())}, "seconds": dt}
        print("  watermark=%2d s : %s   (%.1f s)   window[0,60) Spark=%.4f  batch=%.4f" % (L, "StreamResult == BatchResult" if r == batch else "StreamResult != BatchResult",
              dt, r.get(("A", 0), float("nan")), batch[("A", 0)]))
    out["spark"] = sres; sp.stop()
except Exception as ex:
    print("Spark streaming section skipped:", ex); out["spark"] = {}

# ------------------------------------------------------------------ 2.3 engineering comparison
big = realistic_jitter(); n_ids = len({e["id"] for e in big}); n_dup = len(big) - n_ids
print("\n2.3 ENGINEERING COMPARISON on %d delivered events (%d unique, %d duplicates, 5%% have a 12 s-mean delay tail)" % (len(big), n_ids, n_dup))
def timed(fn, n=3):
    ts_, r = [], None
    for _ in range(n):
        t0 = time.perf_counter(); r = fn(); ts_.append(time.perf_counter() - t0)
    return r, ts_
truth, tb = timed(lambda: batch_engine(big))
(sres_, seng), ts_ = timed(lambda: stream_engine(big, allowed_lateness=10))
last_arrival = big[-1]["arrival"]
lat_batch = [last_arrival - (k[1] + WINDOW) for k in truth]            # results only exist after the batch job finishes
lat_stream = [v[1] - (k[1] + WINDOW) for k, v in seng.emitted.items()]
wrong = sum(1 for k in truth if sres_.get(k) != truth[k])
errs = np.array([abs(sres_.get(k, np.nan) - truth[k]) for k in truth if k in sres_]); mae, maxerr = float(np.nanmean(errs)), float(np.nanmax(errs))
rate = lambda ts: len(big) / np.array(ts)
print("%-34s %-26s %-26s" % ("metric", "A: batch", "B: stream (watermark 10 s)"))
rows = [("throughput (events/s, 3 runs)", "%.0f +/- %.0f" % (rate(tb).mean(), rate(tb).std(ddof=1)), "%.0f +/- %.0f" % (rate(ts_).mean(), rate(ts_).std(ddof=1))),
        ("mean latency window-end -> result", "%.0f s (after job end)" % np.mean(lat_batch), "%.2f s" % np.mean(lat_stream)),
        ("p95 latency", "%.0f s" % np.percentile(lat_batch, 95), "%.2f s" % np.percentile(lat_stream, 95)),
        ("state / memory held (entries)", "%d event ids + all events" % n_ids, "%d (peak windows+ids)" % seng.peak_state),
        ("windows computed", "%d" % len(truth), "%d" % len(sres_)),
        ("result correctness vs batch", "reference", "%d / %d windows exact (%.2f%%)" % (len(truth) - wrong, len(truth), 100 * (1 - wrong / len(truth)))),
        ("error of stream avg vs batch avg", "0", "mean %.3f, max %.3f km/h" % (mae, maxerr)),
        ("late events dropped", "0", "%d (%.3f%%)" % (len(seng.dropped_late), 100 * len(seng.dropped_late) / len(big))),
        ("duplicates removed", "%d" % n_dup, "%d" % len(seng.dup_dropped))]
for r in rows: print("%-34s %-26s %-26s" % r)
# restart behaviour
half = len(big) // 2
e1 = StreamEngine(10)
for e in big[:half]: e1.process(e)
blob = e1.snapshot()
e2 = StreamEngine.restore(blob)                                  # (a) restart WITH checkpoint
for e in big[half:]: e2.process(e)
r_ck = e2.finish(last_arrival)
e3 = StreamEngine(10)                                            # (b) restart WITHOUT state (empty)
for e in big[half:]: e3.process(e)
r_nostate = e3.finish(last_arrival)
full = {k: v[0] for k, v in seng.emitted.items()}
bad_ck = sum(1 for k in set(full) | set(r_ck) if full.get(k) != r_ck.get(k))
bad_ns = sum(1 for k in set(full) | set(r_nostate) if full.get(k) != r_nostate.get(k))
print("\nRESTART after crash at event %d of %d:" % (half, len(big)))
print("  with checkpoint (%d KB state snapshot) : %d windows differ from the uninterrupted run -> %s" % (len(blob) // 1024, bad_ck, "EXACT" if bad_ck == 0 else "NOT exact"))
print("  stateless restart (state lost)       : %d windows differ from the uninterrupted run" % bad_ns)
print("  batch after crash                     : re-reads all %d stored events, deterministic (same %d windows)" % (len(big), len(truth)))
out["compare"] = {"n_events": len(big), "n_unique": n_ids, "n_dup": n_dup, "batch_rate": rate(tb).mean(), "batch_rate_sd": rate(tb).std(ddof=1),
                  "stream_rate": rate(ts_).mean(), "stream_rate_sd": rate(ts_).std(ddof=1), "lat_batch_mean": float(np.mean(lat_batch)),
                  "lat_stream_mean": float(np.mean(lat_stream)), "lat_stream_p95": float(np.percentile(lat_stream, 95)),
                  "state_stream": seng.peak_state, "state_batch": n_ids, "wrong_windows": wrong, "windows": len(truth),
                  "late_dropped": len(seng.dropped_late), "mae": mae, "maxerr": maxerr, "restart_ckpt_bad": bad_ck, "restart_nostate_bad": bad_ns, "snapshot_kb": len(blob) // 1024}

# ------------------------------------------------------------------ 2.4 changed requirement : sweep the watermark
print("\n2.4 CHANGED REQUIREMENT: 'alerts within 2 seconds; a few late events may be ignored'")
print("sweep of the watermark on the same %d events (window = 60 s):" % len(big))
print("%-9s %-10s %-9s %-10s %-12s %-14s %-10s" % ("watermark", "late drop", "% dropped", "wrong win.", "mean lat (s)", "<=2 s results", "peak state"))
sweep = []
for L in (0, 1, 2, 5, 10, 30, 60, 120):
    r, g = stream_engine(big, allowed_lateness=L)
    lat = np.array([v[1] - (k[1] + WINDOW) for k, v in g.emitted.items()])
    w = sum(1 for k in truth if r.get(k) != truth[k])
    row = {"L": L, "dropped": len(g.dropped_late), "pct": 100 * len(g.dropped_late) / len(big), "wrong": w, "windows": len(truth),
           "mean_lat": float(lat.mean()), "within2": float((lat <= 2.0).mean() * 100), "state": g.peak_state}
    sweep.append(row)
    print("%-9s %-10d %-9.3f %-10d %-12.2f %-14.1f %-10d" % ("%d s" % L, row["dropped"], row["pct"], w, row["mean_lat"], row["within2"], row["state"]))
delays = np.array([e["arrival"] - e["ts"] for e in big])
event_path = float((delays <= 2.0).mean() * 100)
print("\nEvent-level alert path (update mode: evaluate on every arrival): %.1f%% of events reach the engine within 2 s of happening" % event_path)
print("  (the remaining %.1f%% are the delayed tail - they can only be caught by a later correction/batch re-computation)" % (100 - event_path))
out["sweep"] = sweep; out["event_path_within2"] = event_path
save_json("task2_results.json", out)

# ------------------------------------------------------------------ figure
fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
ks = sorted(batch); x = np.arange(len(ks)); w = 0.38
ax[0].bar(x - w / 2, [batch[k] for k in ks], w, label="BatchResult", color="#1f4e79")
ax[0].bar(x + w / 2, [res[k] for k in ks], w, label="StreamResult", color="#c55a11")
ax[0].set_xticks(x); ax[0].set_xticklabels(["[%d,%d)" % (k[1], k[1] + 60) for k in ks], fontsize=8); ax[0].set_ylabel("average speed (km/h)")
ax[0].set_title("(a) Counterexample: window [0,60) differs"); ax[0].legend()
Ls = [r["L"] for r in sweep]
ax[1].plot(Ls, [r["mean_lat"] for r in sweep], "o-", color="#1f4e79", label="mean latency (s)"); ax[1].axhline(2, color="red", ls="--", lw=1, label="2 s requirement")
ax[1].set_xlabel("watermark (s)"); ax[1].set_ylabel("latency after window end (s)"); ax[1].set_title("(b) Latency grows with the watermark"); ax[1].legend()
a2 = ax[2]; a2.plot(Ls, [r["pct"] for r in sweep], "s-", color="#c55a11"); a2.set_xlabel("watermark (s)"); a2.set_ylabel("events dropped as late (%)", color="#c55a11")
a3 = a2.twinx(); a3.plot(Ls, [r["state"] for r in sweep], "^-", color="#548235"); a3.set_ylabel("peak state entries", color="#548235"); a2.set_title("(c) Correctness vs memory trade-off")
for a in ax: a.spines[["top"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "fig_task2.png"), dpi=170); plt.close()
print("\nSaved results/task2_results.json and figures/fig_task2.png")
