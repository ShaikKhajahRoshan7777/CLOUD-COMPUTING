"""TASK 1 - Batch pipeline: average speed per segment per hour.   Run:  python run_task1.py"""
import math, os, sys, time, statistics, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common.utils import *
from task1.gen_traffic import generate, ground_truth, N_SEGMENTS
from task1.mapreduce import run_job, single_process_reference, parse_line

plt.rcParams["font.family"] = "Liberation Serif"
SIZES = {"S (200k rows)": 200_000, "M (1M rows)": 1_000_000, "L (4M rows)": 4_000_000}
SPLITS, REDUCERS, REPS = 8, 4, 3
KEYS = N_SEGMENTS * 24                      # 4,800 (segment, hour) keys

banner("TASK 1 - BATCH PIPELINE (map / shuffle / reduce)")
env = env_info(); print("ENVIRONMENT:", json.dumps(env))

# ---------------------------------------------------------------- data generation
paths = {}
for name, n in SIZES.items():
    p = os.path.join(DATA, "traffic_%d.csv" % n)
    if not os.path.exists(p):
        generate(p, n, seed=42)
    paths[name] = p
    print("  data %-14s %8.1f MB  %s" % (name, os.path.getsize(p) / 1e6, os.path.basename(p)))

# ---------------------------------------------------------------- 1.3 predictions (written BEFORE running)
def exp_distinct_keys_per_split(rows):             # balls-in-bins expectation, 96% rows accepted
    per_split = rows * 0.96 / SPLITS
    return KEYS * (1 - math.exp(-per_split / KEYS))
pred = {}
base = None
for name, n in SIZES.items():
    pred[name] = {"dominant_stage": "map",
                  "shuffle_records_with_combiner": round(SPLITS * exp_distinct_keys_per_split(n)),
                  "shuffle_records_without_combiner": round(n * 0.96),
                  "runtime_ratio_vs_S": n / 200_000}
pred["_made_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
save_json("task1_predictions.json", pred)
print("\nPREDICTIONS (saved before execution):")
for name in SIZES:
    p = pred[name]
    print("  %-14s dominant=%s  shuffle(with combiner)=%7d  shuffle(no combiner)=%8d  time x%.0f" % (
        name, p["dominant_stage"], p["shuffle_records_with_combiner"], p["shuffle_records_without_combiner"], p["runtime_ratio_vs_S"]))

# ---------------------------------------------------------------- 1.1 / 1.2 / 1.3 runs
obs = {}
for name, path in paths.items():
    truth = ground_truth(path)
    runs, totals = [], []
    for r in range(REPS):
        res, m = run_job(path, SPLITS, REDUCERS, combiner=True)
        runs.append(m); totals.append(m["total_seconds"])
    _, m_nc = run_job(path, SPLITS, REDUCERS, combiner=False)
    maxerr = max(abs(v - truth["avg"][k]) for k, v in res.items())
    assert len(res) == len(truth["avg"]) and maxerr < 1e-9
    assert (m["read"], m["accepted"], m["rejected"]) == (truth["read"], truth["accepted"], truth["rejected"])
    stage_mean = {s: statistics.mean(x["stage_seconds"][s] for x in runs) for s in ("map", "shuffle", "reduce")}
    obs[name] = {"rows": SIZES[name], "mb": os.path.getsize(path) / 1e6, "read": m["read"], "accepted": m["accepted"],
                 "rejected": m["rejected"], "reasons": m["reasons"], "keys_out": len(res), "max_abs_err_vs_pandas": maxerr,
                 "total_mean": statistics.mean(totals), "total_sd": statistics.stdev(totals), "totals": totals,
                 "stage_mean": stage_mean, "shuffle_records": m["shuffle_records"], "shuffle_bytes": m["shuffle_bytes"],
                 "shuffle_records_nocomb": m_nc["shuffle_records"], "shuffle_bytes_nocomb": m_nc["shuffle_bytes"],
                 "reducer_load": m["reducer_load"], "reducer_load_nocomb": m_nc["reducer_load"]}
    o = obs[name]
    print("\n--- %s : %.1f MB ---" % (name, o["mb"]))
    print("records read=%d accepted=%d rejected=%d  reasons=%s" % (o["read"], o["accepted"], o["rejected"], o["reasons"]))
    print("(segment,hour) results=%d   max |error| vs independent pandas reference = %.2e" % (o["keys_out"], maxerr))
    print("stage time (mean of %d runs): map=%.3fs shuffle=%.3fs reduce=%.3fs | total %.3f +/- %.3f s" % (
        REPS, stage_mean["map"], stage_mean["shuffle"], stage_mean["reduce"], o["total_mean"], o["total_sd"]))
    print("shuffle: with combiner %d records / %.0f KB ; without combiner %d records / %.0f KB" % (
        o["shuffle_records"], o["shuffle_bytes"] / 1e3, o["shuffle_records_nocomb"], o["shuffle_bytes_nocomb"] / 1e3))
    print("per-reducer load (raw records / partial records / keys):")
    for i, l in enumerate(o["reducer_load"]):
        print("   reducer %d : %8d raw | %6d partial | %5d keys" % (i, l["raw_records"], l["partial_records"], l["keys"]))

# sample of actual output
sample_res, _ = run_job(paths["S (200k rows)"], SPLITS, REDUCERS)
print("\nSAMPLE OUTPUT - average speed per segment per hour (first 6 keys sorted):")
for k in sorted(sample_res)[:6]:
    print("   %-7s %s:00   %6.2f km/h" % (k[0], k[1][-5:], sample_res[k]))

# ---------------------------------------------------------------- 1.1 single-process comparison on a small sample
small = os.path.join(DATA, "traffic_sample_10k.csv"); generate(small, 10_000, seed=7)
ref = single_process_reference(small)
mr, _ = run_job(small, SPLITS, REDUCERS)
diff = max(abs(mr[k] - ref[k]) for k in ref)
print("\nSAMPLE (10,000 rows): single-process dict result vs map/shuffle/reduce -> keys %d vs %d, max |diff| = %.1e => %s" % (
    len(ref), len(mr), diff, "IDENTICAL" if diff < 1e-9 and set(ref) == set(mr) else "MISMATCH"))

# ---------------------------------------------------------------- 1.3 compare predictions
print("\nPREDICTION vs OBSERVATION")
print("%-14s %-9s %-22s %-24s %-22s" % ("size", "dominant", "shuffle recs (pred/obs)", "shuffle no-comb (pred/obs)", "time ratio (pred/obs)"))
t0s = obs["S (200k rows)"]["total_mean"]
cmp_rows = []
for name in SIZES:
    o, p = obs[name], pred[name]
    dom = max(o["stage_mean"], key=o["stage_mean"].get)
    ratio = o["total_mean"] / t0s
    cmp_rows.append({"size": name, "dominant_pred": p["dominant_stage"], "dominant_obs": dom,
                     "shuffle_pred": p["shuffle_records_with_combiner"], "shuffle_obs": o["shuffle_records"],
                     "nocomb_pred": p["shuffle_records_without_combiner"], "nocomb_obs": o["shuffle_records_nocomb"],
                     "ratio_pred": p["runtime_ratio_vs_S"], "ratio_obs": ratio})
    print("%-14s %-9s %8d / %-12d %9d / %-12d %5.1f / %-5.1f" % (name, dom, p["shuffle_records_with_combiner"], o["shuffle_records"],
          p["shuffle_records_without_combiner"], o["shuffle_records_nocomb"], p["runtime_ratio_vs_S"], ratio))

# ---------------------------------------------------------------- 1.4 boundary tests
print("\nBOUNDARY / FAILURE TESTS (each checked against an independent expectation)")
def write(name, text):
    p = os.path.join(DATA, name); open(p, "w").write("sensor_id,segment,speed,event_time\n" + text); return p
bt = []
def check(label, ok, detail):
    bt.append({"case": label, "pass": bool(ok), "detail": detail}); print("  [%s] %-44s %s" % ("PASS" if ok else "FAIL", label, detail))

p = write("b_empty.csv", ""); r, m = run_job(p, 8, 4)
check("B1 header-only (empty) file", r == {} and m["read"] == 0, "read=0, 4 empty reducers, no crash")
p = write("b_few.csv", "S1,A,50,2026-03-02 10:00:00\nS2,A,60,2026-03-02 10:30:00\nS3,B,30,2026-03-02 11:00:00\n"); r, m = run_job(p, 8, 4)
check("B2 more splits (8) than lines (3)", m["read"] == 3 and r[("A", "2026-03-02 10")] == 55.0, "read=%d, avg(A,10h)=55.0" % m["read"])
p = write("b_single.csv", "S1,ONLY,37.5,2026-03-02 09:15:00\nS2,X,40,2026-03-02 09:15:00\nS3,X,50,2026-03-02 09:15:00\n"); r, m = run_job(p, 2, 2)
check("B3 segment with a single record", r[("ONLY", "2026-03-02 09")] == 37.5, "avg = the single value 37.5")
p = write("b_null.csv", "S1,N,,2026-03-02 09:00:00\nS2,N,,2026-03-02 09:05:00\nS3,Y,20,2026-03-02 09:00:00\n"); r, m = run_job(p, 2, 2)
check("B4 segment with only null speeds", ("N", "2026-03-02 09") not in r and m["rejected"] == 2, "absent from output (no NaN); rejected=2")
p = write("b_range.csv", "S1,A,0,2026-03-02 01:00:00\nS2,A,200,2026-03-02 01:00:00\nS3,A,200.1,2026-03-02 01:00:00\nS4,A,-0.1,2026-03-02 01:00:00\n"); r, m = run_job(p, 2, 2)
check("B5 speed limits 0 and 200 inclusive", m["accepted"] == 2 and r[("A", "2026-03-02 01")] == 100.0, "accepted=2, rejected=2, avg=100.0")
p = write("b_hour.csv", "S1,A,40,2026-03-02 23:59:59\nS2,A,60,2026-03-03 00:00:00\n"); r, m = run_job(p, 2, 2)
check("B6 hour boundary 23:59:59 / 00:00:00", len(r) == 2, "two different hour keys: %s" % sorted(k[1] for k in r))
r16, m16 = run_job(paths["S (200k rows)"], 8, 16)
empty = sum(1 for l in m16["reducer_load"] if l["keys"] == 0)
check("B7 reducers (5000) > keys (4800)", m16["accepted"] == obs["S (200k rows)"]["accepted"] and len(r16) == 4800, "R=5000 would leave empty reducers; R=16 ok, empty=%d" % empty)

hot = os.path.join(DATA, "traffic_hot_1m.csv")
if not os.path.exists(hot): generate(hot, 1_000_000, seed=11, hot_share=0.9)
_, mh = run_job(hot, 8, 4, combiner=False); _, mhc = run_job(hot, 8, 4, combiner=True)
loads = [l["raw_records"] for l in mh["reducer_load"]]; imbalance = max(loads) / (sum(loads) / len(loads))
loads_c = [l["partial_records"] for l in mhc["reducer_load"]]
print("\nB8 SKEW CASE (chosen boundary case): 90% of 1M events on segment SEG000")
print("   no combiner  : reducer raw-record load =", loads, "-> max/mean = %.2f" % imbalance)
print("   with combiner: reducer partial-record load =", loads_c, "-> max/mean = %.2f" % (max(loads_c) / (sum(loads_c) / 4)))
print("   reduce-stage time: no combiner %.3fs vs with combiner %.3fs ; shuffle %d vs %d records" % (
    mh["stage_seconds"]["reduce"], mhc["stage_seconds"]["reduce"], mh["shuffle_records"], mhc["shuffle_records"]))
skew = {"loads_nocomb": loads, "loads_comb": loads_c, "imbalance_nocomb": imbalance,
        "reduce_s_nocomb": mh["stage_seconds"]["reduce"], "reduce_s_comb": mhc["stage_seconds"]["reduce"],
        "shuffle_nocomb": mh["shuffle_records"], "shuffle_comb": mhc["shuffle_records"]}

# ---------------------------------------------------------------- Spark evidence
spark_res = {}
try:
    from task1 import spark_job
    sp = spark_job.quiet(spark_job.spark_session(4))
    print("\nAPACHE SPARK %s (local[2], shuffle partitions=4) - same job" % sp.version)
    seen = 0
    for name, path in paths.items():
        reps = 3 if SIZES[name] <= 1_000_000 else 1
        times, last = [], None
        truth = ground_truth(path) if SIZES[name] <= 1_000_000 else None
        for _ in range(reps):
            a, m = spark_job.run_spark(sp, path, 8); times.append(m["seconds"])
            m["stages"] = [s for s in m["stages"] if s.get("stage_id", 0) >= seen]
            seen = max([seen] + [s.get("stage_id", 0) + 1 for s in m["stages"]]); last = m
        ok = "n/a" if truth is None else ("OK" if max(abs(v - truth["avg"][k]) for k, v in a.items()) < 1e-9 else "MISMATCH")
        spark_res[name] = {"times": times, "mean": statistics.mean(times), "sd": statistics.stdev(times) if reps > 1 else 0.0,
                           "reps": reps, "read": last["read"], "accepted": last["accepted"], "rejected": last["rejected"],
                           "stages": last["stages"], "matches_pandas": ok}
        print("\n  %s: read=%d accepted=%d rejected=%d | %d run(s): %.2f +/- %.2f s | result check vs pandas: %s" % (
            name, last["read"], last["accepted"], last["rejected"], reps, statistics.mean(times), spark_res[name]["sd"], ok))
        print("   %-6s %-28s %6s %10s %9s %16s %15s" % ("stage", "operation", "tasks", "run time s", "input MB", "shuffle write KB", "shuffle read KB"))
        for s in last["stages"]:
            print("   %-6s %-28s %6d %10.2f %9.2f %16.1f %15.1f" % (s["stage_id"], s["name"], s["tasks"], s["run_time_s"], s["input_mb"], s["shuffle_write_kb"], s["shuffle_read_kb"]))
    sp.stop()
except Exception as e:
    print("Spark section skipped:", e)

# ---------------------------------------------------------------- figures
names = list(SIZES)
fig, ax = plt.subplots(1, 3, figsize=(13, 4.0))
bot = np.zeros(3)
for stg, col in (("map", "#1f4e79"), ("shuffle", "#c55a11"), ("reduce", "#548235")):
    v = np.array([obs[n]["stage_mean"][stg] for n in names]); ax[0].bar(range(3), v, bottom=bot, label=stg, color=col); bot += v
ax[0].set_xticks(range(3)); ax[0].set_xticklabels(["200k", "1M", "4M"]); ax[0].set_ylabel("seconds (mean of 3)"); ax[0].set_title("(a) Time per stage"); ax[0].legend()
w = 0.38; x = np.arange(3)
ax[1].bar(x - w / 2, [obs[n]["shuffle_records"] for n in names], w, label="with combiner", color="#1f4e79")
ax[1].bar(x + w / 2, [obs[n]["shuffle_records_nocomb"] for n in names], w, label="without combiner", color="#c55a11")
ax[1].set_yscale("log"); ax[1].set_xticks(x); ax[1].set_xticklabels(["200k", "1M", "4M"]); ax[1].set_title("(b) Shuffle volume (records, log scale)"); ax[1].legend()
ax[2].bar(np.arange(4) - 0.2, np.array(skew["loads_nocomb"]) / 1e3, 0.4, label="no combiner (raw)", color="#c55a11")
ax[2].bar(np.arange(4) + 0.2, np.array(skew["loads_comb"]) / 1e3, 0.4, label="with combiner (partial)", color="#1f4e79")
ax[2].set_xticks(range(4)); ax[2].set_xlabel("reducer"); ax[2].set_ylabel("records (thousands)"); ax[2].set_title("(c) Skew test: 90% on one segment"); ax[2].legend()
for a in ax: a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "fig_task1.png"), dpi=170); plt.close()

save_json("task1_results.json", {"env": env, "predictions": pred, "observed": obs, "compare": cmp_rows, "boundary": bt, "skew": skew, "spark": spark_res, "sample_diff": diff})
print("\nSaved results/task1_results.json and figures/fig_task1.png")
