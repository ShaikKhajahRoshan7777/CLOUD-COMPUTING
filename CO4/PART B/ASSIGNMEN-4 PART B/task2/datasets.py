"""Datasets for Task 2 (all synthetic, seeded)."""
import random


def clean_ordered(n_minutes=5, segments=("A", "B", "C"), per_min=6, seed=1):
    """2.1 - ordered, clean, no duplicates: every event arrives 1 s after it happened."""
    rnd = random.Random(seed); ev, i = [], 0
    for m in range(n_minutes):
        for s in segments:
            for j in range(per_min):
                ts = m * 60 + j * 9 + (ord(s) - 65) * 2
                ev.append({"id": "e%d" % i, "segment": s, "speed": round(rnd.uniform(30, 80), 1), "ts": ts, "arrival": ts + 1}); i += 1
    return sorted(ev, key=lambda e: (e["arrival"], e["id"]))


def counterexample():
    """2.2 - student-designed, ONE segment (A), hand-placed events:
       e5 : out of order by 7 s but inside the 10 s watermark            -> stream keeps it (correct)
       e2 (2nd copy): DUPLICATE re-delivered at t=67 while window [0,60) is still open; with a short
            de-dup retention (30 s of event time) e2's id is already forgotten -> counted twice
       e6 : LATE - event time 50 s, arrives at t=95 after the watermark closed window [0,60) -> dropped
    """
    E = lambda i, ts, sp, arr: {"id": i, "segment": "A", "speed": sp, "ts": ts, "arrival": arr}
    ev = [E("e1", 5, 40, 6), E("e2", 20, 50, 21), E("e3", 35, 60, 36),
          E("e4", 65, 70, 66), E("e2", 20, 50, 67), E("e5", 58, 80, 68),
          E("e8", 100, 20, 101), E("e6", 50, 10, 102), E("e9", 130, 30, 131),
          E("e10", 190, 90, 191), E("e11", 200, 55, 201)]
    return sorted(ev, key=lambda e: (e["arrival"], e["id"]))


def realistic_jitter(n=200_000, seed=5, max_delay=120):
    """Large stream used for throughput / latency / state / restart / watermark studies.
       arrival = ts + delay; delay ~ 1 s for 95% of events, long tail (exponential, mean 12 s) for 5%.
       2% of events are re-delivered (duplicates) shortly after the original."""
    rnd = random.Random(seed); ev = []
    for i in range(n):
        ts = i * 0.05                                        # 20 events / s
        d = rnd.expovariate(1 / 12) if rnd.random() < 0.05 else rnd.uniform(0.2, 1.5)
        d = min(d, max_delay)
        e = {"id": "x%d" % i, "segment": "S%d" % rnd.randrange(8), "speed": round(rnd.uniform(20, 100), 1), "ts": ts, "arrival": ts + d}
        ev.append(e)
        if rnd.random() < 0.02:
            ev.append(dict(e, arrival=e["arrival"] + rnd.uniform(0.5, 3)))
    return sorted(ev, key=lambda e: (e["arrival"], e["id"]))
