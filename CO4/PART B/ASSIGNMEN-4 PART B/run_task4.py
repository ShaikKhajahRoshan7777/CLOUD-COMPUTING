"""TASK 4 - Data-quality engineering: cleaning stage, decisions, prediction, drift.   Run: python run_task4.py"""
import os, sys, json, statistics, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common.utils import *
from task4.cleaning import run_cleaning, RULES
from task4.feed import make_feed

plt.rcParams["font.family"] = "Liberation Serif"
banner("TASK 4 - DATA QUALITY ENGINEERING"); env = env_info()
print("ENVIRONMENT:", json.dumps({k: env[k] for k in ("python", "cpu", "cpu_cores", "ram_gb")})); out = {}

# ---------------------------------------------------------------- 4.1
feed = make_feed(200_000, 0.05)
r = run_cleaning(feed, trace_n=14); c = r["counts"]
qpath, cpath = os.path.join(DATA, "quarantine.csv"), os.path.join(DATA, "clean.csv")
with open(qpath, "w") as f:
    f.write("line_no|rule|reason|raw\n"); [f.write("%d|%s|%s|%s\n" % q) for q in r["quarantine"]]
with open(cpath, "w") as f:
    f.write("sensor_id,segment,speed,event_time\n"); [f.write("%s,%s,%.2f,%s\n" % rec) for rec in r["clean"]]
print("\n4.1 CLEANING STAGE on %d delivered lines (200,000 distinct + 5%% re-sent duplicates)" % c["READ"])
print("outputs: %s (%d clean rows)   %s (%d quarantined rows)" % (os.path.basename(cpath), len(r["clean"]), os.path.basename(qpath), len(r["quarantine"])))
print("\n4.2 PER-RULE SUMMARY")
print("%-28s %-10s %-10s %8s %7s" % ("rule", "decision", "", "records", "share"))
dec = {"R1_FIELD_COUNT": "reject", "R2_MISSING_VALUE": "reject", "R3_TYPE_REPAIR_OR_REJECT": "repair/reject", "R4_RANGE": "reject", "R5_DUPLICATE": "reject"}
for k in RULES: print("%-28s %-10s %-10s %8d %6.2f%%" % (k, dec[k], "", c[k], 100 * c[k] / c["READ"]))
print("%-28s %-10s %-10s %8d %6.2f%%" % ("KEEP (unchanged)", "keep", "", c["KEEP"], 100 * c["KEEP"] / c["READ"]))
print("%-28s %-10s %-10s %8d %6.2f%%" % ("REPAIR (unit suffix)", "repair", "", c["REPAIR"], 100 * c["REPAIR"] / c["READ"]))
tot = c["KEEP"] + c["REPAIR"] + sum(c[k] for k in RULES); print("reconciliation: kept+repaired+rejected = %d = lines read %d -> %s" % (tot, c["READ"], "BALANCED" if tot == c["READ"] else "MISMATCH"))
print("\nDECISION TRACE (sample of records: which rule fired, decision, why)")
print("%-8s %-8s %-26s %s" % ("line", "decision", "rule", "reason"))
for n, d, rule, why in r["trace"]: print("%-8d %-8s %-26s %s" % (n, d, rule, why))
print("\nQUARANTINE FILE (first 4 rows):"); print("\n".join(open(qpath).read().splitlines()[:5]))
out["rules"] = {k: c[k] for k in RULES}; out["keep"] = c["KEEP"]; out["repair"] = c["REPAIR"]; out["read"] = c["READ"]; out["trace"] = r["trace"]

# ---------------------------------------------------------------- 4.3 prediction BEFORE execution
base_total = len(feed)
pred_tot = 200_000 / (1 - 0.40)
unique_valid = c["KEEP"] + c["REPAIR"]
pred = {"kept": unique_valid, "time_ratio": pred_tot / base_total, "shuffle_ratio": pred_tot / base_total,
        "reasoning": "kept = distinct valid keys, independent of duplicates; time and shuffle scale with delivered lines (200k/(1-0.40) vs %d)" % base_total}
save_json("task4_prediction.json", {**pred, "made_at": time.strftime("%Y-%m-%d %H:%M:%S")})
print("\n4.3 PREDICTION (recorded before the run): duplicates 5% -> 40% of delivered lines")
print("  records kept: unchanged (%d) ; run time x%.2f ; shuffle volume x%.2f (records AND bytes)" % (pred["kept"], pred["time_ratio"], pred["shuffle_ratio"]))
res = {}
for d in (0.05, 0.40):
    f = make_feed(200_000, d); ts, last = [], None
    for _ in range(3):
        t0 = time.perf_counter(); last = run_cleaning(f); ts.append(time.perf_counter() - t0)
    res[d] = {"lines": len(f), "kept": last["counts"]["KEEP"] + last["counts"]["REPAIR"], "dups": last["counts"]["R5_DUPLICATE"], "mean": statistics.mean(ts), "sd": statistics.stdev(ts),
              "shuffle_records": last["shuffle_records"], "shuffle_bytes": last["shuffle_bytes"]}
a, b = res[0.05], res[0.40]
print("OBSERVATION (3 runs each):")
print("%-26s %14s %14s %10s" % ("", "5% duplicates", "40% duplicates", "ratio"))
print("%-26s %14d %14d %10.2f" % ("lines delivered", a["lines"], b["lines"], b["lines"] / a["lines"]))
print("%-26s %14d %14d %10.2f" % ("records kept", a["kept"], b["kept"], b["kept"] / a["kept"]))
print("%-26s %14d %14d" % ("duplicates quarantined", a["dups"], b["dups"]))
print("%-26s %9.3f+/-%.3f %9.3f+/-%.3f %10.2f" % ("run time (s)", a["mean"], a["sd"], b["mean"], b["sd"], b["mean"] / a["mean"]))
print("%-26s %14d %14d %10.2f" % ("shuffle records to dedup", a["shuffle_records"], b["shuffle_records"], b["shuffle_records"] / a["shuffle_records"]))
print("%-26s %14.1f %14.1f %10.2f" % ("shuffle volume (KB)", a["shuffle_bytes"] / 1e3, b["shuffle_bytes"] / 1e3, b["shuffle_bytes"] / a["shuffle_bytes"]))
out["dup"] = {"pred": pred, "obs": {str(k): v for k, v in res.items()}}

# ---------------------------------------------------------------- 4.4 schema drift
print("\n4.4 SCHEMA DRIFT: source switches speed km/h -> m/s and appends a 5th field 'lane'")
drift = make_feed(50_000, 0.0, drift="ms", seed=8); base = make_feed(50_000, 0.0, seed=8)
def avg_speed(res_):
    return float(np.mean([x[2] for x in res_["clean"]])) if res_["clean"] else float("nan")
rb = run_cleaning(base); rs = run_cleaning(drift, strict_schema=True); rt = run_cleaning(drift, strict_schema=False)
print("%-44s %10s %10s %12s" % ("pipeline variant", "kept", "rejected", "mean speed"))
print("%-44s %10d %10d %12.2f" % ("baseline feed (km/h, 4 fields)", len(rb["clean"]), rb["counts"]["READ"] - len(rb["clean"]), avg_speed(rb)))
print("%-44s %10d %10d %12s" % ("drifted feed, STRICT schema (R1 on)", len(rs["clean"]), rs["counts"]["READ"] - len(rs["clean"]), "n/a"))
print("%-44s %10d %10d %12.2f" % ("drifted feed, TOLERANT of extra fields", len(rt["clean"]), rt["counts"]["READ"] - len(rt["clean"]), avg_speed(rt)))
print("  strict mode  : R1_FIELD_COUNT fired on %d of %d lines (%.0f%%) -> drift is detected loudly, but the whole feed is quarantined" % (rs["counts"]["R1_FIELD_COUNT"], rs["counts"]["READ"], 100 * rs["counts"]["R1_FIELD_COUNT"] / rs["counts"]["READ"]))
print("  tolerant mode: every range rule PASSES (0-55 is inside [0,200]) -> result is silently wrong: mean %.2f vs %.2f km/h (x%.2f)" % (avg_speed(rt), avg_speed(rb), avg_speed(rt) / avg_speed(rb)))
med_b, med_d = float(np.median([x[2] for x in rb["clean"]])), float(np.median([x[2] for x in rt["clean"]]))
ratio = med_d / med_b
print("DRIFT MONITOR (median speed of batch vs trusted baseline): baseline %.1f, batch %.1f, ratio %.3f -> %s" % (med_b, med_d, ratio, "UNIT DRIFT SUSPECTED (ratio ~ 1/3.6 = 0.278)" if abs(ratio - 1 / 3.6) < 0.03 else ("ALERT: distribution shift" if abs(ratio - 1) > 0.25 else "ok")))
conv = [(s, g, v * 3.6, t) for s, g, v, t in rt["clean"]]
print("HANDLING: schema registry maps source 'speed_unit=m/s' -> multiply by 3.6 : mean after conversion %.2f km/h (baseline %.2f, diff %.2f%%)" % (np.mean([x[2] for x in conv]), avg_speed(rb), 100 * abs(np.mean([x[2] for x in conv]) - avg_speed(rb)) / avg_speed(rb)))
out["drift"] = {"base_mean": avg_speed(rb), "tolerant_mean": avg_speed(rt), "strict_rejected": rs["counts"]["R1_FIELD_COUNT"], "lines": rs["counts"]["READ"], "ratio": ratio, "converted_mean": float(np.mean([x[2] for x in conv]))}
save_json("task4_results.json", out)

fig, ax = plt.subplots(1, 3, figsize=(13, 3.9))
ax[0].barh([k.split("_", 1)[1] for k in RULES][::-1], [c[k] for k in RULES][::-1], color="#1f4e79"); ax[0].set_xlabel("records quarantined"); ax[0].set_title("(a) Records per rule (5% duplicates)")
x = np.arange(3); w = 0.38
ax[1].bar(x - w / 2, [1, 1, 1], w, label="5% dup (=1.0)", color="#1f4e79")
ax[1].bar(x + w / 2, [b["kept"] / a["kept"], b["mean"] / a["mean"], b["shuffle_bytes"] / a["shuffle_bytes"]], w, label="40% dup", color="#c55a11")
ax[1].plot([0.2, 1.2, 2.2], [pred["kept"] / a["kept"], pred["time_ratio"], pred["shuffle_ratio"]], "k_", ms=22, mew=2, label="prediction")
ax[1].set_xticks(x); ax[1].set_xticklabels(["kept", "run time", "shuffle bytes"]); ax[1].set_title("(b) Duplicate experiment: ratio vs 5%"); ax[1].legend(fontsize=8)
ax[2].bar(["baseline\nkm/h", "drift\nunhandled", "drift +\nconversion"], [avg_speed(rb), avg_speed(rt), float(np.mean([x[2] for x in conv]))], color=["#548235", "#c55a11", "#1f4e79"]); ax[2].set_ylabel("mean speed (km/h)"); ax[2].set_title("(c) Schema drift effect")
for a_ in ax: a_.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "fig_task4.png"), dpi=170); plt.close()
print("\nSaved results/task4_results.json and figures/fig_task4.png")
