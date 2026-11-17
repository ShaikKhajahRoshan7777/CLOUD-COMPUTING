"""Task 10 (and 11.8) - Illustrative 3-year cost comparison in INR.
All figures are planning assumptions copied from the written answer,
NOT provider quotations. Replace with real prices before submission.
"""

LAKH = 100_000

COSTS = {  # rupees, 3 years
    "On-premises": {
        "Hardware / compute & storage": 36 * LAKH,
        "Power, cooling, DC, network": 9 * LAKH,
        "Licences / subscriptions": 6 * LAKH,
        "Operations & administration": 18 * LAKH,
        "Backup / DR": 6 * LAKH,
    },
    "IaaS": {
        "Hardware / compute & storage": 75_000 * 36,
        "Power, cooling, DC, network": int(3.6 * LAKH),
        "Licences / subscriptions": 6 * LAKH,
        "Operations & administration": 12 * LAKH,
        "Backup / DR": int(4.5 * LAKH),
    },
    "PaaS/SaaS": {
        "Hardware / compute & storage": 18 * LAKH,
        "Power, cooling, DC, network": int(3.6 * LAKH),
        "Licences / subscriptions": 12 * LAKH,
        "Operations & administration": 6 * LAKH,
        "Backup / DR": int(4.5 * LAKH),
    },
}

# Task 11.8 - extra monthly cost of the revised (MODIFY) design
EXTRA_MONTHLY = {
    "Peak compute / API capacity": 30_000,
    "Cross-region backup / replication": 15_000,
    "Enhanced monitoring / security": 5_000,
}


def lakh(x):
    return f"Rs {x / LAKH:,.2f} lakh"


def main():
    totals = {name: sum(items.values()) for name, items in COSTS.items()}

    print("TASK 10 - 3-YEAR COST COMPARISON (illustrative)")
    for name, items in COSTS.items():
        print(f"\n{name}")
        for k, v in items.items():
            print(f"  {k:<32}{lakh(v):>20}")
        print(f"  {'TOTAL':<32}{lakh(totals[name]):>20}")

    base = totals["On-premises"]
    print("\nSavings vs on-premises")
    for name in ("IaaS", "PaaS/SaaS"):
        saving = base - totals[name]
        print(f"  {name:<10}: {lakh(saving)} ({saving / base * 100:.1f}% lower)")
    print(f"  PaaS/SaaS vs IaaS: {lakh(totals['IaaS'] - totals['PaaS/SaaS'])} lower")

    extra_year = sum(EXTRA_MONTHLY.values()) * 12
    extra_3yr = extra_year * 3
    revised = totals["PaaS/SaaS"] + extra_3yr
    print("\nTASK 11.8 - REVISED DESIGN COST")
    print(f"  Extra per month : Rs {sum(EXTRA_MONTHLY.values()):,}")
    print(f"  Extra per year  : Rs {extra_year:,}")
    print(f"  Extra 3 years   : {lakh(extra_3yr)}")
    print(f"  Revised 3-yr total = {lakh(totals['PaaS/SaaS'])} + {lakh(extra_3yr)} = {lakh(revised)}")


if __name__ == "__main__":
    main()
