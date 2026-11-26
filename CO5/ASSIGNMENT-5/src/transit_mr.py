"""
transit_mr.py  -  core MapReduce logic for the Metro Transit footfall analysis.

Record format (scenario assumption, see README):
    timestamp,station_id,gate_id,card_id,tap_type,fare
    2026-03-02 08:15:32,S017,G3,C000123456,ENTRY,0.00

The same functions are used (a) by the Hadoop Streaming scripts
mapper.py / reducer.py and (b) by the local MapReduce emulator mr_local.py.
"""
import re

TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$")
ST_RE = re.compile(r"^S\d{3}$")


def parse(line):
    """Return (ts, station, tap_type, fare) or None when the record is malformed."""
    parts = line.rstrip("\r\n").split(",")
    if len(parts) != 6:
        return None
    ts, station, gate, card, tap, fare = (p.strip() for p in parts)
    if not TS_RE.match(ts) or not ST_RE.match(station):
        return None
    if tap not in ("ENTRY", "EXIT"):
        return None
    try:
        fare_v = float(fare)
    except ValueError:
        return None
    if fare_v < 0:
        return None
    return ts, station, tap, fare_v


def q1_map(lines, counter=lambda g, n, v=1: None):
    """Q1 mapper: emit 'station|YYYY-MM-DD|HH <TAB> 1' for each valid ENTRY tap."""
    for line in lines:
        if not line.strip():
            continue
        rec = parse(line)
        if rec is None:
            counter("Transit", "MalformedRecords")
            continue
        ts, station, tap, _ = rec
        if tap != "ENTRY":
            counter("Transit", "ExitTapsSkipped")
            continue
        yield f"{station}|{ts[:10]}|{ts[11:13]}\t1"


def sum_reduce(sorted_lines):
    """Streaming reducer (also usable as combiner): input is SORTED 'key<TAB>int' lines."""
    cur_key, total = None, 0
    for line in sorted_lines:
        key, _, val = line.rstrip("\n").partition("\t")
        if key != cur_key:                 # key change detected -> flush previous key
            if cur_key is not None:
                yield f"{cur_key}\t{total}"
            cur_key, total = key, 0
        total += int(val)
    if cur_key is not None:
        yield f"{cur_key}\t{total}"


# ---------------- Q2: five busiest stations per day (two-job chain) ----------
def q2_station_day_map(lines, counter=lambda g, n, v=1: None):
    """Job-1 mapper: key = station|date for each valid ENTRY tap, value = 1."""
    for line in lines:
        rec = parse(line)
        if rec is None:
            counter("Transit", "MalformedRecords")
            continue
        if rec[2] != "ENTRY":
            continue
        ts, station, _, _ = rec
        yield f"{station}|{ts[:10]}\t1"


def q2_job2_map(lines, counter=lambda g, n, v=1: None):
    """Job-2 mapper: input 'station|date <TAB> n'  ->  output 'date <TAB> station|n'."""
    for line in lines:
        key, _, val = line.rstrip("\n").partition("\t")
        station, date = key.split("|")
        yield f"{date}\t{station}|{val}"


def topn_reduce(sorted_lines, n=5):
    """Job-2 reducer / combiner: keep the N largest (count, station) per date.
       Safe as a combiner because top-N of partial top-N's equals top-N of the union."""
    cur, heap = None, []

    def flush():
        heap.sort(key=lambda t: (-t[0], t[1]))
        return [f"{cur}\t{st}|{cnt}" for cnt, st in heap[:n]]

    for line in sorted_lines:
        date, _, val = line.rstrip("\n").partition("\t")
        st, _, cnt = val.partition("|")
        if date != cur:
            if cur is not None:
                yield from flush()
            cur, heap = date, []
        heap.append((int(cnt), st))
        heap.sort(key=lambda t: (-t[0], t[1]))
        del heap[n:]
    if cur is not None:
        yield from flush()
