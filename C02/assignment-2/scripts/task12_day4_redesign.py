#!/usr/bin/env python3
"""TASK 12 - Day-4 challenge: compare ORIGINAL (shared hosts) vs MODIFIED (separate pools)."""
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from _common import save_table, RESULTS
from educloud import day4


def main():
    a = day4.Day4Assumptions()

    # B. evaluation of the original design under the new conditions
    rows = [day4.shared_design(a), day4.shared_design(a, migrating=True),
            day4.modified_design(a, migrating=True)]
    save_table(pd.DataFrame(rows), "task12_design_comparison")

    # C. revised architecture - pool sizing and effect on density
    sizes = day4.pool_sizes(a)
    save_table(pd.DataFrame([sizes]).T.reset_index().rename(columns={"index": "item", 0: "value"}),
               "task12_pool_sizing")

    # D. evidence: SIS bandwidth satisfaction vs registration-peak multiplier
    mult = [1 + 0.25 * i for i in range(0, 13)]
    curve = pd.DataFrame(day4.sis_net_ratio_curve(a, mult))
    save_table(curve.round(3), "task12_peak_curve")
    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.plot(curve.peak_multiplier, curve.shared * 100, "o-", label="original: shared host + NIC")
    ax.plot(curve.peak_multiplier, curve.shared_migrating * 100, "s--", label="original + live migration")
    ax.plot(curve.peak_multiplier, curve.separate_pools * 100, "^-", label="modified: separate pools")
    ax.axhline(90, color="red", ls=":", label="SLA: >= 90 % of demand")
    ax.axvline(a.peak_multiplier, color="grey", ls=":")
    ax.set_xlabel("registration-week load (x normal)")
    ax.set_ylabel("SIS network demand satisfied (%)")
    ax.set_title("Task 12: SIS network headroom with external Spark/Hadoop tenants")
    ax.legend(fontsize=8)
    ax.grid(alpha=.3)
    fig.tight_layout()
    fig.savefig(RESULTS / "task12_peak_curve.png", dpi=150)
    print(f"\nFigure saved to {RESULTS / 'task12_peak_curve.png'}")
    print("\nAssumptions used:", a)


if __name__ == "__main__":
    main()
