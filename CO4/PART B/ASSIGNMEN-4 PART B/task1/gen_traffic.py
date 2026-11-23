"""Synthetic traffic-event generator (seeded, documented).

Schema : sensor_id, segment, speed, event_time   (CSV, header present)
Dirty  : ~2% null speed, ~1% out-of-range speed (<0 or >200), ~1% malformed timestamp.
Skew   : optional `hot_share` sends that fraction of events to one segment.
Truth  : ground_truth() is an independent pandas reference (different code path from the
         pipeline) giving read/accepted/rejected counts and exact per-key averages.
"""
import numpy as np, pandas as pd, datetime as dt

N_SEGMENTS = 200
SENSORS_PER_SEGMENT = 5
HOURS = 24
BASE = dt.datetime(2026, 3, 2, 0, 0, 0)


def generate(path, n_rows, seed=42, hot_share=0.0, n_segments=N_SEGMENTS, dirty=True):
    rng = np.random.default_rng(seed)
    seg = rng.integers(0, n_segments, n_rows)
    if hot_share > 0:
        seg[rng.random(n_rows) < hot_share] = 0
    sensor = seg * SENSORS_PER_SEGMENT + rng.integers(0, SENSORS_PER_SEGMENT, n_rows)
    secs = rng.integers(0, HOURS * 3600, n_rows)
    speed = np.clip(rng.normal(45 + (seg % 7) * 4, 12, n_rows), 1, 120).round(1)
    t = pd.to_datetime(BASE) + pd.to_timedelta(secs, unit="s")
    df = pd.DataFrame({"sensor_id": ["S%04d" % s for s in sensor],
                       "segment": ["SEG%03d" % s for s in seg],
                       "speed": speed.astype(object),
                       "event_time": t.strftime("%Y-%m-%d %H:%M:%S").to_numpy(dtype=object)})
    if dirty:
        r = rng.random(n_rows)
        df.loc[r < 0.02, "speed"] = ""                                   # null speeds
        m = (r >= 0.02) & (r < 0.03)
        df.loc[m, "speed"] = rng.choice([-5.0, 250.0, 999.0], m.sum())   # out of range
        m = (r >= 0.03) & (r < 0.04)
        df.loc[m, "event_time"] = "not-a-time"                           # malformed
    df.to_csv(path, index=False)
    return path


def ground_truth(path, chunk=500_000):
    """Independent pandas reference, chunked so a 4M-row file fits in a few hundred MB."""
    tot_s, tot_c, n_read, n_ok = None, None, 0, 0
    for df in pd.read_csv(path, dtype=str, keep_default_na=False, chunksize=chunk):
        sp = pd.to_numeric(df["speed"], errors="coerce")
        ts = pd.to_datetime(df["event_time"], format="%Y-%m-%d %H:%M:%S", errors="coerce")
        ok = sp.notna() & ts.notna() & (sp >= 0) & (sp <= 200)
        n_read += len(df); n_ok += int(ok.sum())
        g = pd.DataFrame({"segment": df["segment"][ok], "hour": ts[ok].dt.strftime("%Y-%m-%d %H"), "speed": sp[ok]}).groupby(["segment", "hour"])["speed"]
        s_, c_ = g.sum(), g.count()
        tot_s = s_ if tot_s is None else tot_s.add(s_, fill_value=0)
        tot_c = c_ if tot_c is None else tot_c.add(c_, fill_value=0)
    return {"read": n_read, "accepted": n_ok, "rejected": n_read - n_ok, "avg": tot_s / tot_c}
