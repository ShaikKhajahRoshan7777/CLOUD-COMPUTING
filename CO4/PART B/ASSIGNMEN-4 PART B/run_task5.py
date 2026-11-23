"""TASK 5 - Three storage models, one data set (5,000,000 events).   Run: python run_task5.py"""
import os, sys, json, statistics, time, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from common.utils import *
from task5 import stores as S

plt.rcParams["font.family"] = "Liberation Serif"
banner("TASK 5 - CSV vs PARQUET vs SQLITE ON 5,000,000 EVENTS"); env = env_info()
print("ENVIRONMENT:", json.dumps({k: env[k] for k in ("python", "cpu", "cpu_cores", "ram_gb", "pandas", "pyarrow")}), "sqlite", __import__("sqlite3").sqlite_version)
D = os.path.join(DATA, "store5"); out = {}
print("\nBUILDING the three stores from one generator (500 sensors x 30 days x 166,667 events/day = 5,000,000 rows)...")
tb, csv_p, pq_p, db_p = S.build(D); out["build"] = tb
mb = lambda p: os.path.getsize(p) / 1e6
sizes = {"CSV": mb(csv_p), "Parquet": mb(pq_p), "SQLite": mb(db_p)}
import pyarrow.parquet as pq
meta = pq.ParquetFile(pq_p).metadata
print("build time: CSV %.1fs | Parquet %.1fs | SQLite insert %.1fs + index %.1fs" % (tb["csv_s"], tb["parquet_s"], tb["sqlite_insert_s"], tb["sqlite_index_s"]))
print("rows: CSV/Parquet/SQLite = ?/%d/%d" % (meta.num_rows, __import__("sqlite3").connect(db_p).execute("select count(*) from events").fetchone()[0]))
print("STORAGE SIZE: CSV %.1f MB | Parquet %.1f MB (%d row groups, zstd, sorted by date+sensor) | SQLite %.1f MB (table + index on sensor_id,event_date)" % (sizes["CSV"], sizes["Parquet"], meta.num_row_groups, sizes["SQLite"]))
out["sizes"] = sizes; out["row_groups"] = meta.num_row_groups

SENSOR, DATE, W0, W1, SLO, SHI = "S0123", "2026-03-10", "2026-03-08", "2026-03-14", "S0100", "S0109"
pred = {"Q1p_vs_Q1_bytes": {"CSV": 1.0, "Parquet": 2.0, "SQLite": 3.0}, "Q2p_vs_Q2_bytes": {"CSV": 1.0, "Parquet": 0.6, "SQLite": 1.0},
        "Q2p_vs_Q2_time": {"CSV": 0.9, "Parquet": 0.6, "SQLite": 1.0}, "Q1_bytes_pct_of_store": {"CSV": 100, "Parquet": 1.0, "SQLite": 1.0},
        "Q2_bytes_pct_of_store": {"CSV": 100, "Parquet": 8.0, "SQLite": 100}, "made_at": time.strftime("%Y-%m-%d %H:%M:%S")}
save_json("task5_prediction.json", pred)
print("\nPREDICTIONS (saved before any query ran):")
print("  Q1 point lookup : CSV scans ~100%% of file; Parquet reads ~1%% (row-group pruning); SQLite ~1%% (index seek)")
print("  Q2 week scan    : CSV ~100%%; Parquet ~8%% (7/30 days, 2/5 columns); SQLite ~100%% (index is on sensor, not date)")
print("  Q1' (10 sensors): bytes x1 CSV, x2 Parquet, x3 SQLite  |  Q2' (one column): bytes x1 CSV, x0.6 Parquet, x1 SQLite")

def drop_caches():
    try:
        open("/proc/sys/vm/drop_caches", "w").write("3"); return True
    except Exception: return False
dc = drop_caches(); print("page-cache drop before cold runs possible: %s" % dc)

def measure(fn, *a, warm=3):
    drop_caches(); t0 = time.perf_counter(); r, b = fn(*a); cold = time.perf_counter() - t0
    ts, bs = [], []
    for _ in range(warm):
        t0 = time.perf_counter(); r, b = fn(*a); ts.append(time.perf_counter() - t0); bs.append(b)
    return {"cold": cold, "warm_mean": statistics.mean(ts), "warm_sd": statistics.stdev(ts), "bytes": statistics.mean(bs), "result": r if isinstance(r, int) else len(r), "raw": r if not isinstance(r, int) else r}

paths = {"CSV": csv_p, "Parquet": pq_p, "SQLite": db_p}
F = {"Q1": {"CSV": S.q1_csv, "Parquet": S.q1_parquet, "SQLite": S.q1_sqlite}, "Q2": {"CSV": S.q2_csv, "Parquet": S.q2_parquet, "SQLite": S.q2_sqlite}}
res = {}
print("\nQ1 / Q2 (cold run reported separately; warm = mean +/- SD of 3 further runs)")
print("%-4s %-8s %8s %18s %12s %9s %9s" % ("", "store", "cold s", "warm s (n=3)", "bytes read", "% of store", "result"))
for q, args in (("Q1", (SENSOR, DATE)), ("Q2", (W0, W1))):
    for st in paths:
        r = measure(F[q][st], paths[st], *args); res[(q, st)] = r
        print("%-4s %-8s %8.3f %9.3f+/-%-7.3f %12d %8.1f%% %9s" % (q, st, r["cold"], r["warm_mean"], r["warm_sd"], r["bytes"], 100 * r["bytes"] / os.path.getsize(paths[st]), r["result"] if q == "Q1" else "%d segs" % r["result"]))
rows_q1 = {st: res[("Q1", st)]["result"] for st in paths}; print("Q1 row counts agree across stores: %s %s" % (len(set(rows_q1.values())) == 1, rows_q1))
ref = res[("Q2", "Parquet")]["raw"]; mx = {st: max(abs(res[("Q2", st)]["raw"][k] - ref[k]) for k in ref) for st in paths}; print("Q2 max |avg difference| vs Parquet: %s" % {k: "%.1e" % v for k, v in mx.items()})

# tuning: covering index for Q2 on SQLite
import sqlite3
con = sqlite3.connect(db_p); before = mb(db_p); t0 = time.perf_counter(); con.execute("CREATE INDEX idx_cov ON events(event_date, segment, speed)"); con.commit(); tix = time.perf_counter() - t0; con.close()
r = measure(S.q2_sqlite, db_p, W0, W1); res[("Q2", "SQLite+cov")] = r
print("\nTUNING: SQLite covering index (event_date, segment, speed): build %.1fs, DB %.1f -> %.1f MB ; Q2 now %.3fs warm, %d bytes read (%.1f%% of DB)" % (tix, before, mb(db_p), r["warm_mean"], r["bytes"], 100 * r["bytes"] / os.path.getsize(db_p)))
out["tuning"] = {"index_build_s": tix, "db_mb_before": before, "db_mb_after": mb(db_p)}

print("\nSTRESS THE DESIGN - changed query patterns")
for lab, q, fn, args in (("Q1'  10 sensors, 1 day", "Q1", F["Q1"], (SLO, DATE, SHI)), ("Q2'  one column (AVG speed)", "Q2", F["Q2"], (W0, W1, True))):
    for st in paths:
        r = measure(fn[st], paths[st], *args); res[(lab[:3], st)] = r
for st in paths:
    a, b = res[("Q1", st)], res[("Q1'", st)]; c, d = res[("Q2", st)], res[("Q2'", st)]
    print("%-8s Q1': %.3fs (x%.2f time) bytes x%.2f (pred x%.1f) rows %d | Q2': %.3fs (x%.2f) bytes x%.2f (pred x%.1f)" % (st, b["warm_mean"], b["warm_mean"] / a["warm_mean"], b["bytes"] / a["bytes"], pred["Q1p_vs_Q1_bytes"][st], b["result"],
          d["warm_mean"], d["warm_mean"] / c["warm_mean"], d["bytes"] / c["bytes"], pred["Q2p_vs_Q2_bytes"][st]))

print("\nQ3 WRITE LOAD: stream of 50 batches x 1,000 new events (3 repetitions each)")
rng = np.random.default_rng(5); mk = lambda: [S.day_frame(30, rng, 1000) for _ in range(50)]
w = {}
size0 = {"CSV": os.path.getsize(csv_p), "SQLite": os.path.getsize(db_p)}
for st in ("CSV", "Parquet", "SQLite"):
    ts, wb, nf = [], 0, 0
    for rep in range(3):
        b = mk()
        if st == "CSV": t, wbytes, nf = S.q3_csv(csv_p, b)
        elif st == "Parquet": t, wbytes, nf = S.q3_parquet(os.path.join(D, "parquet_new"), b, "r%d" % rep)
        else: t, wbytes, nf = S.q3_sqlite(db_p, b)
        ts.append(t); wb = wbytes
    w[st] = {"mean": statistics.mean(ts), "sd": statistics.stdev(ts), "eps": 50000 / statistics.mean(ts), "bytes_written": wb, "files": nf}
    print("  %-8s %.3f +/- %.3f s per 50,000 events  -> %9.0f events/s ; bytes written/run %.2f MB ; units created per run: %d %s" % (st, w[st]["mean"], w[st]["sd"], w[st]["eps"], wb / 1e6, nf, "file(s)" if st != "SQLite" else "transactions"))
newfiles = len(os.listdir(os.path.join(D, "parquet_new"))); print("  Parquet small files after 3 runs: %d (each immutable; reads must open all of them -> compaction needed)" % newfiles)
out["Q3"] = w; out["parquet_small_files"] = newfiles
out["queries"] = {"%s|%s" % k: {kk: vv for kk, vv in v.items() if kk != "raw"} for k, v in res.items()}; out["pred"] = pred
save_json("task5_results.json", out)

fig, ax = plt.subplots(1, 3, figsize=(13.5, 4.0)); stn = ["CSV", "Parquet", "SQLite"]; x = np.arange(3); w_ = 0.2
labs = [("Q1", "Q1"), ("Q2", "Q2"), ("Q1'", "Q1'"), ("Q2'", "Q2'")]
for i, (l, key) in enumerate(labs): ax[0].bar(x + (i - 1.5) * w_, [res[(key, s)]["warm_mean"] for s in stn], w_, label=l)
ax[0].set_yscale("log"); ax[0].set_xticks(x); ax[0].set_xticklabels(stn); ax[0].set_ylabel("warm run time (s, log)"); ax[0].set_title("(a) Query time"); ax[0].legend(fontsize=8)
for i, (l, key) in enumerate(labs): ax[1].bar(x + (i - 1.5) * w_, [max(res[(key, s)]["bytes"] / 1e6, 0.01) for s in stn], w_, label=l)
ax[1].set_yscale("log"); ax[1].set_xticks(x); ax[1].set_xticklabels(stn); ax[1].set_ylabel("bytes read (MB, log)"); ax[1].set_title("(b) Data read per query")
ax[2].bar(stn, [sizes[s] for s in stn], color=["#c55a11", "#548235", "#1f4e79"]); ax[2].set_ylabel("storage size (MB)"); ax[2].set_title("(c) Storage size, 5M events")
for a in ax: a.spines[["top", "right"]].set_visible(False)
plt.tight_layout(); plt.savefig(os.path.join(FIGURES, "fig_task5.png"), dpi=170); plt.close()
print("\nSaved results/task5_results.json and figures/fig_task5.png")
