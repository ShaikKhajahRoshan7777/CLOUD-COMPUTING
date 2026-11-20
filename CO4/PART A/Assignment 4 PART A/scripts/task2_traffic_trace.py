"""Task 2.4 / 2.5 - desk-check of the traffic pipeline: validation, de-duplication, event-time windows, watermark, allowed lateness."""
WINDOW = 60            # seconds, tumbling, event time
WM_DELAY = 5           # watermark = max valid event time seen - 5 s
ALLOWED_LATENESS = 60  # seconds past window end (measured on the watermark)
MIN_V, MAX_V = 0, 200  # valid speed range km/h

EVENTS = [
    (1, "S1", "R7", 42,   "08:00:05", "08:00:06"),
    (2, "S2", "R7", 38,   "08:00:20", "08:00:21"),
    (3, "S1", "R7", 42,   "08:00:05", "08:00:07"),
    (4, "S3", "R9", None, "08:00:30", "08:00:31"),
    (5, "S2", "R7", -5,   "08:00:50", "08:00:51"),
    (6, "S4", "R9", 55,   "08:01:10", "08:01:12"),
    (7, "S1", "R7", 40,   "08:00:45", "08:01:40"),
    (8, "S5", "R9", 60,   "08:01:20", "08:01:21"),
]

def secs(s):
    h, m, x = map(int, s.split(":")); return h * 3600 + m * 60 + x

def clock(n):
    return f"{n // 3600:02d}:{n % 3600 // 60:02d}:{n % 60:02d}"

def run(events, lateness=ALLOWED_LATENESS, show=True):
    seen, win, closed, max_et, out = set(), {}, set(), None, []
    for no, sid, seg, spd, et, at in events:
        e = secs(et); ws = e - e % WINDOW; key = (seg, ws)
        wm_before = None if max_et is None else max_et - WM_DELAY
        if spd is None:
            dec = "REJECTED  missing speed -> dead-letter"
        elif not MIN_V <= spd <= MAX_V:
            dec = f"REJECTED  speed {spd} outside {MIN_V}-{MAX_V} -> dead-letter"
        elif (sid, e) in seen:
            dec = "MERGED    duplicate of (sensor, event time) - state unchanged"
        else:
            seen.add((sid, e))
            if key in closed:
                late_by = wm_before - (ws + WINDOW)
                if late_by <= lateness:
                    s = win.setdefault(key, [0, 0]); s[0] += spd; s[1] += 1
                    dec = f"LATE-ACCEPTED  window closed, watermark lag {late_by}s <= {lateness}s -> correction re-emitted"
                    out.append(f"CORRECTION {seg}@{clock(ws)} avg={s[0]/s[1]:.1f} n={s[1]}")
                else:
                    dec = f"LATE-DROPPED  lag {late_by}s > {lateness}s -> sent to batch archive"
            else:
                s = win.setdefault(key, [0, 0]); s[0] += spd; s[1] += 1
                dec = "ACCEPTED"
            max_et = e if max_et is None else max(max_et, e)
            wm = max_et - WM_DELAY
            for k in sorted(win):
                if k not in closed and k[1] + WINDOW <= wm:
                    closed.add(k); s = win[k]
                    out.append(f"FINAL  {k[0]}@{clock(k[1])} avg={s[0]/s[1]:.1f} n={s[1]}  (watermark {clock(wm)})")
        if show:
            st = "  ".join(f"{k[0]}@{clock(k[1])}=[sum {v[0]}, n {v[1]}]" for k, v in sorted(win.items()))
            print(f" E{no} {sid} {seg} spd={str(spd):>4} et={et} at={at}\n     -> {dec}\n     state: {st or '(empty)'}")
    return win, out

if __name__ == "__main__":
    print("=" * 78); print(" TASK 2.4 : DESK-CHECK  (1-min tumbling windows, event time)"); print("=" * 78)
    win, out = run(EVENTS)
    print("-" * 78); print(" Emitted results:"); [print("  ", o) for o in out]
    print("\n" + "=" * 78); print(" TASK 2.5 : CHALLENGE - change E7 speed 40 -> 52"); print("=" * 78)
    print(" Prediction : (R7, 08:00) is corrected from 40.0 to 44.0; only E7's decision matters.")
    mod = [e if e[0] != 7 else (7, "S1", "R7", 52, "08:00:45", "08:01:40") for e in EVENTS]
    w2, o2 = run(mod, show=False)
    s = w2[("R7", secs("08:00:00"))]; avg = s[0] / s[1]
    print(f" Observed   : (R7, 08:00) sum={s[0]} n={s[1]} avg={avg:.1f}")
    print(f" Prediction correct: {avg == 44.0}")
    print("\n Parameter test: allowed lateness 0 s instead of 60 s")
    w3, o3 = run(EVENTS, lateness=0, show=False)
    print(f"   E7 outcome -> (R7, 08:00) n={w3[('R7', secs('08:00:00'))][1]} (E7 dropped to archive; live view stays at 2 events)")
