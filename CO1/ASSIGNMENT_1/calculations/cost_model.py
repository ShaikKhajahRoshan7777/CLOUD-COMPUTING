"""Task 10 - Three-year cost comparison (all figures in Rs. lakh; ILLUSTRATIVE ASSUMPTIONS, not vendor quotes)."""
import json

YEARS = 3
# component: (one-time / CapEx, per-year OpEx) -------------------------------
OPTIONS = {
    "On-premise (refresh)": {
        "Servers (12 x 4.0)": (48.0, 0), "Storage + network": (12.0, 0), "DR site build": (20.0, 0),
        "Power, cooling, facility": (0, 13.0), "Admin staff (3 x 6)": (0, 18.0),
        "AMC / support (10% of hardware)": (0, 8.0), "Software licences": (0, 12.0),
    },
    "IaaS-based": {
        "Migration (lift & shift)": (10.0, 0), "Reserved VMs (baseline)": (0, 16.0),
        "On-demand burst VMs": (0, 4.0), "Storage + backup": (0, 5.0), "Network / egress": (0, 3.0),
        "DR (pilot light)": (0, 4.0), "Software licences": (0, 12.0), "Admin staff (2 x 6)": (0, 12.0),
    },
    "PaaS/SaaS-based (full)": {
        "Migration + SIS re-platform": (30.0, 0), "PaaS app platform": (0, 12.0), "Managed database": (0, 7.0),
        "Storage": (0, 3.0), "Network": (0, 2.0), "Managed DR": (0, 3.0),
        "SaaS licences (LMS, Email, Library)": (0, 14.0), "Admin staff (1 x 6)": (0, 6.0),
    },
    "Recommended hybrid": {
        "Migration (phased)": (12.0, 0), "SIS on reserved IaaS VMs": (0, 7.5), "PaaS (Exam Portal + API)": (0, 7.5),
        "Managed database": (0, 5.0), "Storage + backup": (0, 3.0), "Network": (0, 2.0), "DR (pilot light)": (0, 4.0),
        "SaaS licences (LMS, Email, Library)": (0, 14.0), "Admin staff (1.5 x 6)": (0, 9.0),
    },
}

print("=" * 78)
print(" TASK 10 - THREE-YEAR COST COMPARISON (Rs. lakh)")
print("=" * 78)
summary = {}
for name, comps in OPTIONS.items():
    capex = sum(c for c, _ in comps.values())
    opex = sum(o for _, o in comps.values())
    total = capex + opex * YEARS
    summary[name] = {"capex": capex, "opex_year": opex, "year1": capex + opex,
                     "year2": capex + opex * 2, "total": total}
    print(f"\n {name}")
    for k, (c, o) in comps.items():
        print(f"    {k:<38} CapEx {c:>5.1f}   OpEx/yr {o:>5.1f}")
    print(f"    {'-' * 62}")
    print(f"    CapEx {capex:.1f} + OpEx {opex:.1f} x {YEARS} = {total:.1f} lakh")

print("\n" + "-" * 78)
print(f" {'Option':<26}{'CapEx/one-time':>15}{'OpEx / year':>14}{"3-year TCO":>13}{"Saving vs on-prem":>19}")
base = summary["On-premise (refresh)"]["total"]
for name, s in summary.items():
    sv = (base - s["total"]) / base * 100
    print(f" {name:<26}{s['capex']:>15.1f}{s['opex_year']:>14.1f}{s['total']:>13.1f}{sv:>18.1f}%")

json.dump({"summary": summary, "options": {n: {k: list(v) for k, v in c.items()} for n, c in OPTIONS.items()}},
          open("results_cost.json", "w"), indent=2)
