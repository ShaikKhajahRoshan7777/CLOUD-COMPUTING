"""Three storage models for the SAME traffic data set (5,000,000 events, 500 sensors, 30 days):
   (1) row-oriented CSV   (2) columnar Parquet (zstd, sorted by date+sensor, 100k-row groups)   (3) relational SQLite (+ index)
Query functions return (result, bytes_read) where bytes_read = delta of rchar in /proc/self/io (all read() bytes)."""
import csv, glob, os, sqlite3, time
import numpy as np, pandas as pd
import pyarrow as pa, pyarrow.parquet as pq
import pyarrow.compute as pc

N_SENSORS, DAYS, PER_DAY = 500, 30, 166_667
SEG_OF = lambda s: s // 5
COLS = ["sensor_id", "segment", "speed", "event_time", "event_date"]
D0 = pd.Timestamp("2026-03-01")


def rchar():
    for l in open("/proc/self/io"):
        if l.startswith("rchar"): return int(l.split()[1])


def wchar():
    for l in open("/proc/self/io"):
        if l.startswith("wchar"): return int(l.split()[1])


def day_frame(day, rng, n=PER_DAY):
    secs = np.sort(rng.integers(0, 86400, n)); s = rng.integers(0, N_SENSORS, n)
    ts = D0 + pd.to_timedelta(day * 86400 + secs, unit="s")
    return pd.DataFrame({"sensor_id": np.char.add("S", np.char.zfill(s.astype(str), 4)), "segment": np.char.add("SEG", np.char.zfill((s // 5).astype(str), 3)),
                         "speed": np.clip(rng.normal(50, 14, n), 1, 130).round(1), "event_time": ts.strftime("%Y-%m-%d %H:%M:%S"),
                         "event_date": ts.strftime("%Y-%m-%d")})


def build(dirpath, seed=17):
    os.makedirs(dirpath, exist_ok=True)
    csv_p, pq_p, db_p = (os.path.join(dirpath, x) for x in ("events.csv", "events.parquet", "events.db"))
    for p in (csv_p, pq_p, db_p):
        if os.path.exists(p): os.remove(p)
    rng = np.random.default_rng(seed); timing = {}
    con = sqlite3.connect(db_p); con.execute("PRAGMA journal_mode=OFF"); con.execute("PRAGMA synchronous=OFF")
    con.execute("CREATE TABLE events (sensor_id TEXT, segment TEXT, speed REAL, event_time TEXT, event_date TEXT)")
    writer, tc, tp, ts_ = None, 0.0, 0.0, 0.0; first = True
    for day in range(DAYS):
        df = day_frame(day, rng)
        t0 = time.perf_counter(); df.to_csv(csv_p, mode="w" if first else "a", header=first, index=False); tc += time.perf_counter() - t0
        t0 = time.perf_counter(); tab = pa.Table.from_pandas(df.sort_values("sensor_id", kind="stable"), preserve_index=False)
        writer = writer or pq.ParquetWriter(pq_p, tab.schema, compression="zstd"); writer.write_table(tab, row_group_size=100_000); tp += time.perf_counter() - t0
        t0 = time.perf_counter(); con.executemany("INSERT INTO events VALUES (?,?,?,?,?)", df.values.tolist()); ts_ += time.perf_counter() - t0; first = False
    writer.close(); con.commit()
    t0 = time.perf_counter(); con.execute("CREATE INDEX idx_sensor_date ON events(sensor_id, event_date)"); con.commit(); ti = time.perf_counter() - t0
    con.close()
    return {"csv_s": tc, "parquet_s": tp, "sqlite_insert_s": ts_, "sqlite_index_s": ti}, csv_p, pq_p, db_p


# ------------------------------------------------------------------ queries
def q1_csv(p, sensor, date, sensor_hi=None):
    b = rchar(); parts = []
    for ch in pd.read_csv(p, chunksize=500_000, dtype={"sensor_id": str, "segment": str, "event_time": str, "event_date": str}):
        m = (ch["event_date"] == date) & ((ch["sensor_id"] == sensor) if sensor_hi is None else (ch["sensor_id"] >= sensor) & (ch["sensor_id"] <= sensor_hi))
        if m.any(): parts.append(ch[m])
    r = pd.concat(parts) if parts else pd.DataFrame(); return len(r), rchar() - b


def q1_parquet(p, sensor, date, sensor_hi=None):
    b = rchar()
    f = [("event_date", "=", date)] + ([("sensor_id", "=", sensor)] if sensor_hi is None else [("sensor_id", ">=", sensor), ("sensor_id", "<=", sensor_hi)])
    t = pq.read_table(p, filters=f); return t.num_rows, rchar() - b


def q1_sqlite(p, sensor, date, sensor_hi=None):
    b = rchar(); con = sqlite3.connect(p)
    if sensor_hi is None: rows = con.execute("SELECT * FROM events WHERE sensor_id=? AND event_date=?", (sensor, date)).fetchall()
    else: rows = con.execute("SELECT * FROM events WHERE sensor_id BETWEEN ? AND ? AND event_date=?", (sensor, sensor_hi, date)).fetchall()
    con.close(); return len(rows), rchar() - b


def q2_csv(p, d0, d1, one_col=False):
    b = rchar(); acc = {}
    for ch in pd.read_csv(p, chunksize=500_000, usecols=["speed", "event_date"] if one_col else ["segment", "speed", "event_date"]):
        ch = ch[(ch["event_date"] >= d0) & (ch["event_date"] <= d1)]
        if one_col: s = acc.get("all", (0.0, 0)); acc["all"] = (s[0] + ch["speed"].sum(), s[1] + len(ch))
        else:
            for k, v in ch.groupby("segment")["speed"].agg(["sum", "count"]).iterrows():
                s = acc.get(k, (0.0, 0)); acc[k] = (s[0] + v["sum"], s[1] + int(v["count"]))
    return {k: s / c for k, (s, c) in acc.items()}, rchar() - b


def q2_parquet(p, d0, d1, one_col=False):
    b = rchar(); f = [("event_date", ">=", d0), ("event_date", "<=", d1)]
    t = pq.read_table(p, columns=["speed"] if one_col else ["segment", "speed"], filters=f)
    if one_col: return {"all": pc.mean(t["speed"]).as_py()}, rchar() - b
    g = t.group_by("segment").aggregate([("speed", "mean")]); return dict(zip(g["segment"].to_pylist(), g["speed_mean"].to_pylist())), rchar() - b


def q2_sqlite(p, d0, d1, one_col=False):
    b = rchar(); con = sqlite3.connect(p)
    sql = "SELECT AVG(speed) FROM events WHERE event_date BETWEEN ? AND ?" if one_col else "SELECT segment, AVG(speed) FROM events WHERE event_date BETWEEN ? AND ? GROUP BY segment"
    rows = con.execute(sql, (d0, d1)).fetchall(); con.close()
    return ({"all": rows[0][0]} if one_col else dict(rows)), rchar() - b


def q3_csv(p, batches):
    w0 = wchar(); t0 = time.perf_counter()
    with open(p, "a", newline="") as f:
        wr = csv.writer(f)
        for b in batches: wr.writerows(b.values.tolist()); f.flush()
    return time.perf_counter() - t0, wchar() - w0, 1


def q3_parquet(dirp, batches, tag):
    os.makedirs(dirp, exist_ok=True); w0 = wchar(); t0 = time.perf_counter()
    for i, b in enumerate(batches): pq.write_table(pa.Table.from_pandas(b, preserve_index=False), os.path.join(dirp, "%s_%04d.parquet" % (tag, i)), compression="zstd")
    return time.perf_counter() - t0, wchar() - w0, len(batches)


def q3_sqlite(p, batches):
    w0 = wchar(); con = sqlite3.connect(p); con.execute("PRAGMA journal_mode=WAL"); con.execute("PRAGMA synchronous=NORMAL"); t0 = time.perf_counter()
    for b in batches: con.executemany("INSERT INTO events VALUES (?,?,?,?,?)", b.values.tolist()); con.commit()
    el = time.perf_counter() - t0; con.execute("PRAGMA wal_checkpoint(TRUNCATE)"); con.close(); return el, wchar() - w0, len(batches)
