"""Task 5 - MapReduce shape (map -> combine -> partition/shuffle -> reduce) on a small sample, plus data-movement estimates."""
from collections import defaultdict
SPLITS = [  # (segment, hour, speed) extracted from (sensor, segment, speed, event time)
    [("R7", "08", 42), ("R7", "08", 38), ("R7", "08", 40), ("R9", "08", 55)],
    [("R7", "08", 60), ("R9", "08", 60), ("R9", "08", 50), ("R9", "08", 40), ("R9", "08", 45)],
]
SEGMENTS = ["R7", "R9"]; R = 2
print("=" * 74); print(" TASK 5.1 : MAP -> COMBINE -> SHUFFLE -> REDUCE (sample)"); print("=" * 74)
combined = []
for i, split in enumerate(SPLITS, 1):
    emitted = [((s, h), (v, 1)) for s, h, v in split]
    comb = defaultdict(lambda: [0, 0])
    for k, (v, c) in emitted: comb[k][0] += v; comb[k][1] += c
    print(f" Mapper {i}: emitted {len(emitted)} pairs -> after combiner {len(comb)} pairs {dict(comb)}")
    combined += [(k, tuple(v)) for k, v in comb.items()]
parts = defaultdict(list)
for k, v in combined: parts[SEGMENTS.index(k[0]) % R].append((k, v))
print(" Partition rule: reducer = index(segment) mod 2")
final = {}
for p, items in sorted(parts.items()):
    agg = defaultdict(lambda: [0, 0])
    for k, (sm, c) in items: agg[k][0] += sm; agg[k][1] += c
    for k, (sm, c) in agg.items(): final[k] = sm / c
    print(f" Reducer {p}: received {items}")
print(" Output (segment, hour) -> average:", {k: round(v, 2) for k, v in final.items()})
r9 = [v for s in SPLITS for sg, h, v in s if sg == "R9"]
avg_of_avg = (55 + (60 + 50 + 40 + 45) / 4) / 2
print(f"\n Correct R9 average (sum/count)   = {sum(r9)/len(r9):.2f}")
print(f" Wrong 'average of averages'      = {avg_of_avg:.2f}   <- why the combiner must carry (sum, count)")

print("\n" + "=" * 74); print(" TASK 5.1/5.2 : DATA-MOVEMENT ESTIMATES (assumptions, not measurements)"); print("=" * 74)
events_day, bytes_ev, segs = 4.32e9, 40, 5000
pairs_nocomb = events_day
pairs_comb = 24 * segs
print(f" Shuffle pairs without combiner : {pairs_nocomb:,.0f}")
print(f" Shuffle pairs with combiner    : {pairs_comb:,.0f}   (24 mappers x {segs} segments)")
print(f" Estimated reduction            : {pairs_nocomb/pairs_comb:,.0f} x")
data_gb = events_day * bytes_ev / 1e9
print(f"\n Dataset ~ {data_gb:,.1f} GB/day.  20 iterations:")
print(f"   MapReduce  : reads {20*data_gb:,.1f} GB from disk + writes intermediate/output each pass")
print(f"   In-memory  : reads {data_gb:,.1f} GB once, then 19 passes from memory")
print(f"   Disk reads avoided: {19*data_gb:,.1f} GB ({19/20*100:.0f} %)")
