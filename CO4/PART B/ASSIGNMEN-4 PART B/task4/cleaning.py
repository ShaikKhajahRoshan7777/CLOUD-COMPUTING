"""Rule-based cleaning stage with quarantine. Pure functions: clean_line() decides, run_cleaning() does the I/O."""
import pickle, time
from datetime import datetime

RULES = ["R1_FIELD_COUNT", "R2_MISSING_VALUE", "R3_TYPE_REPAIR_OR_REJECT", "R4_RANGE", "R5_DUPLICATE"]
EXPECTED_FIELDS = 4


def clean_line(line, strict_schema=True):
    """Return (decision, rule, reason, record). decision in KEEP / REPAIR / REJECT (R5 is applied later)."""
    f = line.rstrip("\r\n").split(",")
    if len(f) != EXPECTED_FIELDS and (strict_schema or len(f) < EXPECTED_FIELDS):
        return "REJECT", RULES[0], "expected 4 fields, found %d" % len(f), None
    f = f[:EXPECTED_FIELDS]
    sensor, seg, spd, ts = [x.strip() for x in f]
    if not (sensor and seg and spd and ts):
        return "REJECT", RULES[1], "empty " + ",".join(n for n, v in zip(("sensor", "segment", "speed", "time"), (sensor, seg, spd, ts)) if not v), None
    decision, rule, reason = "KEEP", None, "valid"
    try:
        speed = float(spd)
    except ValueError:
        s2 = spd.lower().replace("km/h", "").replace("kmph", "").strip()
        try:
            speed = float(s2); decision, rule, reason = "REPAIR", RULES[2], "unit suffix stripped from '%s'" % spd
        except ValueError:
            return "REJECT", RULES[2], "speed '%s' is not numeric" % spd, None
    try:
        datetime.fromisoformat(ts)
    except ValueError:
        return "REJECT", RULES[2], "timestamp '%s' unparsable" % ts, None
    if not 0.0 <= speed <= 200.0:
        return "REJECT", RULES[3], "speed %.1f outside [0,200]" % speed, None
    return decision, rule, reason, (sensor, seg, speed, ts)


def run_cleaning(lines, strict_schema=True, trace_n=0):
    """Stage 1: per-line rules.  Stage 2: de-duplication on (sensor, time) = the 'shuffle' stage (hash partition by key)."""
    counts = {r: 0 for r in RULES}; counts.update({"KEEP": 0, "REPAIR": 0, "READ": 0})
    quarantine, trace, staged = [], [], []
    t0 = time.perf_counter()
    for n, line in enumerate(lines, 1):
        counts["READ"] += 1
        d, rule, why, rec = clean_line(line, strict_schema)
        if d == "REJECT":
            counts[rule] += 1; quarantine.append((n, rule, why, line.rstrip("\n")))
        else:
            staged.append((n, d, rule, why, rec))
        if len(trace) < trace_n and (d != "KEEP" or n % 997 == 0):
            trace.append((n, d, rule or "-", why))
    t_rules = time.perf_counter() - t0
    t0 = time.perf_counter()
    shuffle_bytes = len(pickle.dumps([(r[4][0], r[4][3]) for r in staged], protocol=4))       # key payload sent to the dedup stage
    seen, clean = set(), []
    for n, d, rule, why, rec in staged:
        key = (rec[0], rec[3])
        if key in seen:
            counts[RULES[4]] += 1; quarantine.append((n, RULES[4], "duplicate of (%s, %s) - first copy kept" % key, ",".join(map(str, rec)))); continue
        seen.add(key); clean.append(rec); counts[d] += 1
    t_dedup = time.perf_counter() - t0
    return {"clean": clean, "quarantine": quarantine, "counts": counts, "trace": trace, "shuffle_records": len(staged),
            "shuffle_bytes": shuffle_bytes, "t_rules": t_rules, "t_dedup": t_dedup}
