#!/usr/bin/env python3
"""TASK 6 - isolation vs performance trade-off: exhaustive search of the decision space.

Minimise J = alpha*Cost + beta*D + gamma*R  subject to the SLA / memory / failover / isolation
constraints in educloud/tradeoff.py.  Run with --peak 3 --external 30 for the Day-4 conditions.
"""
import argparse
import pandas as pd
from _common import save_table
from educloud.tradeoff import Scenario, search


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--peak", type=float, default=1.0, help="registration peak multiplier (3 for Day-4)")
    ap.add_argument("--external", type=float, default=0.0,
                    help="cores burnt by external tenants on a SHARED host (Day-4)")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()

    sc = Scenario(peak_multiplier=a.peak, external_cores_demand=a.external)
    rows = search(sc)
    df = pd.DataFrame(rows)
    cols = [c for c in df.columns if c != "overcommit"]
    top = df.sort_values(["feasible", "J", "overcommit"], ascending=[False, True, True]) \
            .drop_duplicates(subset=cols).head(a.top)          # keep lowest r among identical designs
    save_table(top, f"task6_best_designs_peak{a.peak:g}_ext{a.external:g}")

    print("\nBest feasible design per approach:")
    best = df[df.feasible].groupby("approach", as_index=False).first()
    print(best.to_string(index=False))
    print("\nWhy designs are rejected (count by first violation):")
    print(df[~df.feasible].violations.str.split(";").str[0].value_counts().to_string())

    print("\nSensitivity to weights (alpha, beta, gamma) -> best design")
    rows = []
    for w in [(0.6, 0.2, 0.2), (0.2, 0.4, 0.4), (0.1, 0.3, 0.6), (0.1, 0.6, 0.3)]:
        sc2 = Scenario(peak_multiplier=a.peak, external_cores_demand=a.external,
                       alpha=w[0], beta=w[1], gamma=w[2])
        b = search(sc2)[0]
        rows.append({"alpha": w[0], "beta": w[1], "gamma": w[2], **{k: b[k] for k in
                     ("approach", "dedicated", "smt_off", "overcommit", "hosts", "degradation_pct", "J")}})
    save_table(pd.DataFrame(rows), f"task6_sensitivity_peak{a.peak:g}_ext{a.external:g}")


if __name__ == "__main__":
    main()
