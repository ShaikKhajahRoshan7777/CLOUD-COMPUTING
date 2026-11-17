#!/usr/bin/env python3
"""TASK 7 - security benefit vs quantified performance / density cost of each mitigation."""
import pandas as pd
from _common import save_table
from educloud.mitigation import MITIGATIONS, evaluate


def main():
    for approach in ("vm", "container", "microvm"):
        rows = [evaluate(m, approach) for m in MITIGATIONS]
        save_table(pd.DataFrame(rows), f"task7_mitigations_{approach}")


if __name__ == "__main__":
    main()
