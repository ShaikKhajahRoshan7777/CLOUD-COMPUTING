"""Task 4 - failing case (linkage attack), repair (generalise + k-anonymity), regression check."""
from collections import defaultdict

RELEASE = [  # Name and ID_Number already dropped (original step 3)
    (1, "600117", "1985-03-14", "F", "Widow Pension", 1200),
    (2, "600042", "1988-11-02", "F", "Housing",       8000),
    (3, "600117", "1991-07-21", "M", "Scholarship",   5000),
    (4, "600089", "1993-01-30", "M", "Housing",       8000),
    (5, "600042", "1996-05-09", "M", "Farmer Aid",    3000),
    (6, "600089", "1984-12-25", "F", "Scholarship",   5000),
    (7, "600117", "1990-08-15", "M", "Farmer Aid",    3500),
]
VOTERS = [  # public auxiliary list
    ("Meena S",   "600117", "1985-03-14", "F"),
    ("Priya R",   "600042", "1988-11-02", "F"),
    ("Anil K",    "600089", "1993-01-30", "M"),
    ("Karthik V", "600117", "1991-07-21", "M"),
    ("Ravi T",    "600055", "1979-02-02", "M"),   # not a beneficiary
]
K = 3

def generalise(r):
    rid, pin, dob, g, sch, amt = r
    return (rid, pin[:3], f"{dob[:3]}0s", g, sch, amt)

def link(release, voters, rel_key, voter_key):
    for v in voters:
        yield v[0], [r for r in release if rel_key(r) == voter_key(v)]

print("=" * 74); print(" TASK 4.2 : LINKAGE ATTACK ON THE ORIGINAL RELEASE"); print("=" * 74)
for name, hits in link(RELEASE, VOTERS, lambda r: (r[1], r[2], r[3]), lambda v: (v[1], v[2], v[3])):
    tag = "RE-IDENTIFIED" if len(hits) == 1 else ("no match" if not hits else f"{len(hits)} candidates")
    detail = f" -> record {hits[0][0]}: {hits[0][4]}, Rs {hits[0][5]}" if len(hits) == 1 else ""
    print(f"  {name:<10} join on (PIN, DOB, Gender): {len(hits)} match  [{tag}]{detail}")
print("  First identification: Meena S joins to exactly one row (record 1) at the PIN+DOB+Gender join.")

print("\n" + "=" * 74); print(" TASK 4.3 : REPAIRED STEP 3 (generalise + k-anonymity check, k = 3)"); print("=" * 74)
REL2 = [generalise(r) for r in RELEASE]
groups = defaultdict(list)
for r in REL2: groups[(r[1], r[2], r[3])].append(r)
for g, rows in sorted(groups.items()):
    print(f"  group {g}: size {len(rows)}  distinct schemes {len({x[4] for x in rows})}")
ok = all(len(v) >= K for v in groups.values())
print(f"  every group >= {K}: {ok}   -> release permitted: {ok}")
for name, hits in link(REL2, VOTERS, lambda r: (r[1], r[2], r[3]), lambda v: (v[1][:3], v[2][:3] + "0s", v[3])):
    print(f"  {name:<10} join on (PIN3, decade, Gender): {len(hits)} candidates  max re-id probability {1/len(hits):.2f}" if hits else f"  {name:<10} no match")

print("\n" + "=" * 74); print(" TASK 4.4 : REGRESSION CHECK"); print("=" * 74)
print("  Case 1 - Ravi T (not a beneficiary): original 0 matches, repaired 0 matches -> still safe")
def mean_by(rel):
    d = defaultdict(list)
    for r in rel: d[r[4]].append(r[5])
    return {k: round(sum(v) / len(v), 1) for k, v in sorted(d.items())}
print("  Case 2 - average Amount per Scheme (analysis query):")
print("     original:", mean_by(RELEASE)); print("     repaired:", mean_by(REL2))
assert mean_by(RELEASE) == mean_by(REL2); print("  Identical -> usefulness preserved.")
