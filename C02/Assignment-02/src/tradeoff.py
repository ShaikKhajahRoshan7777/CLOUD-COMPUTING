"""Task 6 / 7 - isolation-performance trade-off and mitigation evaluation (analytical)."""
import model as M
print("TASK 6  decision table: 400 instances, typical load, 16 hosts, SIS needs isolation I >= 0.75 and a hardware boundary")
print("%-8s %-8s %-10s %4s %5s %7s %6s %7s  %s" % ("approach", "SMT off", "dedicated", "n/h", "hosts", "risk", "I", "J", "feasible"))
rows = M.optimise(wl="typical", iso_min=0.75, need_hw_boundary=True)
for r in rows:
    print("%-8s %-8s %-10s %4d %5s %7.3f %6.3f %7.3f  %s" % (r["approach"], r["smt_off"], r["dedicated"], r["n"], r["H"] if r["H"] < 99 else "inf", r["risk"], r["iso"], r["J"], "YES" if r["feasible"] else "no"))
best = min((r for r in rows if r["feasible"]), key=lambda r: r["J"])
print("\nOPTIMUM -> %s, SMT off=%s, dedicated pool=%s : %d hosts, risk %.3f, J=%.3f" % (best["approach"], best["smt_off"], best["dedicated"], best["H"], best["risk"], best["J"]))
print("\nTASK 7  mitigation cost from the model (KVM, typical load)")
base = M.density(M.A, "typical")["n"]
for m, (mult, cost) in M.MITIGATIONS.items():
    mp = M.mit_params([m]); f = cost.get("f", 1.0)
    n = M.density(M.A, "typical", f=f, mit=mp)["n"]
    print("  %-42s density %2d -> %2d  (%+.0f%%)  risk %.3f -> %.3f" % (m, base, n, 100 * (n - base) / base, M.risk("A"), M.risk("A", [m])))
