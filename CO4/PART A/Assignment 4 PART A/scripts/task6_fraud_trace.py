"""Task 6 - fraud rules A and B, desk-check on E1-E8 and adversarial set X1-X7."""
from statistics import median
from collections import defaultdict

E = [("E1","B101","AC9","D1",2000,1),("E2","B102","AC9","D1",2000,2),("E3","B103","AC4","D2",1500,2),
     ("E4","B104","AC9","D1",2000,3),("E5","B105","AC7","D2",9000,3),("E6","B106","AC4","D2",1500,5),
     ("E7","B107","AC9","D1",2000,9),("E8","B108","AC2","D1",2100,9)]
X = [("X1","B301","AC21","D3",1000,1),("X2","B302","AC21","D3",1000,2),("X3","B303","AC22","D3",1000,3),
     ("X4","B304","AC22","D3",1000,4),("X5","B305","AC23","D3",1000,5),("X6","B306","AC23","D3",2900,6),
     ("X7","B307","AC24","D3",2950,6)]

def run(events, verbose=True):
    acct = defaultdict(dict)     # account -> {beneficiary: latest day}
    dist = defaultdict(list)     # district -> earlier amounts
    seen, flags = set(), {}
    for ev, ben, ac, d, amt, day in events:
        if ev in seen: continue
        seen.add(ev)
        acct[ac] = {b: dd for b, dd in acct[ac].items() if dd >= day - 6}   # window = day-6 .. day
        acct[ac][ben] = day
        n = len(acct[ac]); a = n >= 3
        if dist[d]:
            m = median(dist[d]); b = amt > 3 * m; btxt = f"median {m:g}, limit {3*m:g}"
        else:
            b = False; btxt = "no earlier payment -> skip"
        dist[d].append(amt)
        f = [r for r, hit in (("A", a), ("B", b)) if hit]
        if f: flags[ev] = f
        if verbose:
            print(f" {ev} {ben} {ac} {d} amt={amt:<5} day={day}\n     A: {ac} distinct in window = {n} -> {'FLAG' if a else 'ok'}   B: {btxt} -> {'FLAG' if b else 'ok'}")
    return flags

print("=" * 76); print(" TASK 6 STAGE 5 : DESK-CHECK E1-E8"); print("=" * 76)
fl = run(E)
print("-" * 76); print(" Flagged:", {k: "Rule " + "+".join(v) for k, v in fl.items()})
assert fl == {"E4": ["A"], "E5": ["B"]}
print("\n" + "=" * 76); print(" TASK 6 STAGE 6 : ATTACK SET X1-X7 (predicted: nothing flagged)"); print("=" * 76)
fx = run(X)
print("-" * 76); print(f" Flagged: {fx or 'NONE'}  -> both rules fail against split accounts and just-under-3x amounts")
