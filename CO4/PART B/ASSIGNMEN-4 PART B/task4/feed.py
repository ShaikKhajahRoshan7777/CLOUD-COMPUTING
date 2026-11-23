"""Synthetic dirty traffic feed (seeded). dup_share = fraction of ALL delivered lines that are re-sent duplicates."""
import random
from datetime import datetime, timedelta

BASE = datetime(2026, 3, 2)


def make_feed(n_unique=200_000, dup_share=0.05, seed=3, drift=None):
    rnd = random.Random(seed); lines = []
    for i in range(n_unique):
        seg = "SEG%03d" % rnd.randrange(50); sensor = "S%04d" % rnd.randrange(300)
        ts = (BASE + timedelta(seconds=i)).strftime("%Y-%m-%d %H:%M:%S"); sp = max(1, rnd.gauss(50, 12))
        r = rnd.random()
        if drift == "ms":                                    # silent unit change km/h -> m/s plus a NEW trailing field
            lines.append("%s,%s,%.2f,%s,lane%d" % (sensor, seg, sp / 3.6, ts, rnd.randrange(3))); continue
        if r < 0.010: lines.append("%s,%s,%s" % (sensor, seg, ts))                       # malformed: 3 fields
        elif r < 0.025: lines.append("%s,%s,,%s" % (sensor, seg, ts))                    # missing speed
        elif r < 0.030: lines.append(",%s,%.1f,%s" % (seg, sp, ts))                      # missing sensor
        elif r < 0.040: lines.append("%s,%s,%.1f,%s" % (sensor, seg, rnd.choice([-12, 260, 999]), ts))   # invalid range
        elif r < 0.050: lines.append("%s,%s,fast,%s" % (sensor, seg, ts))                # non-numeric
        elif r < 0.060: lines.append("%s,%s,%.1f km/h,%s" % (sensor, seg, sp, ts))       # repairable unit suffix
        elif r < 0.070: lines.append("%s,%s,%.1f,31/02/2026" % (sensor, seg, sp))        # bad timestamp
        else: lines.append("%s,%s,%.1f,%s" % (sensor, seg, sp, ts))
    n_dup = int(n_unique * dup_share / (1 - dup_share))
    lines += [lines[rnd.randrange(len(lines))] for _ in range(n_dup)]
    rnd.shuffle(lines)
    return lines
