"""Task 2 engines: Solution A (batch) and Solution B (event-time streaming with watermark + de-duplication).

An event is a dict:  id, segment, speed, ts (event time, seconds), arrival (processing time, seconds).
Both engines compute the ONE-MINUTE AVERAGE SPEED per segment (tumbling event-time windows).
Pure logic only - no I/O - so both can be tested on hand-made data.
"""
import json, time

WINDOW = 60


def window_start(ts):
    return int(ts // WINDOW) * WINDOW


# ------------------------------------------------------------------ Solution A : batch
def batch_engine(events):
    """Whole stored data set at once: de-duplicate by event id, group by (segment, window)."""
    seen, acc = set(), {}
    for e in events:
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        k = (e["segment"], window_start(e["ts"]))
        s, c = acc.get(k, (0.0, 0))
        acc[k] = (s + e["speed"], c + 1)
    return {k: round(s / c, 4) for k, (s, c) in acc.items()}


# ------------------------------------------------------------------ Solution B : streaming
class StreamEngine:
    """Event-time tumbling windows, watermark, de-duplication with bounded retention.

    watermark  = max(event time seen) - allowed_lateness
    an event is DROPPED if its window end <= watermark (window already closed: 'too late')
    a window is EMITTED (append mode) when watermark >= window end
    dedup state: an id is forgotten when its event time < max_ts - dedup_ttl
                 (dedup_ttl=None -> keep each id until its window has closed = safe default)
    """

    def __init__(self, allowed_lateness=10, dedup_ttl=None):
        self.L, self.ttl = allowed_lateness, dedup_ttl
        self.max_ts = float("-inf")
        self._last_evict = float("-inf")
        self.windows = {}              # (segment, wstart) -> [sum, count]
        self.seen = {}                 # id -> event ts
        self.emitted = {}              # (segment, wstart) -> (avg, arrival_time_of_emission)
        self.dropped_late, self.dup_dropped, self.dup_counted = [], [], []
        self._ever = set()             # diagnostics only (NOT operational state): ids ever accepted
        self.peak_state = 0

    @property
    def watermark(self):
        return self.max_ts - self.L

    def process(self, e):
        self.max_ts = max(self.max_ts, e["ts"])
        wm = self.watermark
        k = (e["segment"], window_start(e["ts"]))
        if k[1] + WINDOW <= wm:                                # window already closed
            self.dropped_late.append(e)
        elif e["id"] in self.seen:
            self.dup_dropped.append(e)
        else:
            if e["id"] in self._ever:
                self.dup_counted.append(e)                     # a duplicate that slipped through de-dup
            self._ever.add(e["id"])
            self.seen[e["id"]] = e["ts"]
            w = self.windows.setdefault(k, [0.0, 0])
            w[0] += e["speed"]; w[1] += 1
        self._advance(e["arrival"])

    def _advance(self, now):
        wm = self.watermark
        if self.windows:
            for k in [k for k in self.windows if k[1] + WINDOW <= wm]:
                s, c = self.windows.pop(k)
                self.emitted[k] = (round(s / c, 4), now)
        if self.max_ts - self._last_evict >= 1.0:              # evict at most once per event-second
            self._last_evict = self.max_ts
            horizon = (wm - WINDOW) if self.ttl is None else (self.max_ts - self.ttl)
            for i in [i for i, t in self.seen.items() if t < horizon]:
                del self.seen[i]
        self.peak_state = max(self.peak_state, len(self.windows) + len(self.seen))

    def finish(self, now=None):
        """End of input: flush open windows (equivalent to a +infinity watermark)."""
        for k, (s, c) in list(self.windows.items()):
            self.emitted[k] = (round(s / c, 4), now)
        self.windows.clear()
        return {k: v[0] for k, v in self.emitted.items()}

    # --- checkpointing for restart experiments
    def snapshot(self):
        return json.dumps({"L": self.L, "ttl": self.ttl, "max_ts": self.max_ts, "windows": [[list(k), v] for k, v in self.windows.items()],
                           "seen": self.seen, "emitted": [[list(k), v] for k, v in self.emitted.items()]})

    @classmethod
    def restore(cls, blob):
        d = json.loads(blob)
        o = cls(d["L"], d["ttl"]); o.max_ts = d["max_ts"]
        o.windows = {tuple(k): v for k, v in d["windows"]}
        o.seen = d["seen"]; o.emitted = {tuple(k): tuple(v) for k, v in d["emitted"]}
        return o


def stream_engine(events, allowed_lateness=10, dedup_ttl=None):
    eng = StreamEngine(allowed_lateness, dedup_ttl)
    for e in events:
        eng.process(e)
    res = eng.finish(events[-1]["arrival"] if events else 0)
    return res, eng


def first_difference(events, batch, **cfg):
    """Replay the stream; return (stream result, engine, differing keys, culprit events in arrival order).
    Culprits = events dropped as late, or duplicate ids that were counted again."""
    res, eng = stream_engine(events, **cfg)
    diff = sorted(k for k in set(batch) | set(res) if batch.get(k) != res.get(k))
    cul = [(e, "LATE: window already closed by the watermark -> event dropped") for e in eng.dropped_late]
    cul += [(e, "DUPLICATE: id already evicted from de-dup state -> counted twice") for e in eng.dup_counted]
    return res, eng, diff, sorted(cul, key=lambda c: c[0]["arrival"])
