"""Stages B and C - linkage attack and k-anonymity by generalisation (pure functions)."""
import math
import numpy as np, pandas as pd

QI = ["PIN_Code", "Date_of_Birth", "Gender"]
DOB_LEVELS = ["exact date", "month", "year", "5-year band", "10-year band", "20-year band"]
DOB_WIDTH_DAYS = [1, 30, 365, 1826, 3652, 7305]
PIN_LEVELS = [6, 5, 4, 3, 0]                 # digits kept (0 = fully suppressed)


def predicted_reidentification(n, n_pins, dob_days, aux_share):
    cells = n_pins * dob_days * 2
    p_unique = math.exp(-(n - 1) / cells)                 # P(nobody else shares my cell), Poisson approximation
    return {"cells": cells, "p_unique": p_unique, "unique_records": n * p_unique, "reidentified": aux_share * n * p_unique}


def linkage_attack(release, aux, truth_names=None):
    """Join release and auxiliary data on the quasi-identifiers. A release record is re-identified when its
    quasi-identifier tuple matches exactly ONE auxiliary person and exactly ONE released record."""
    r = release.copy(); r["_rid"] = range(len(r))
    cls_r = r.groupby(QI)["_rid"].transform("size")
    cls_a = aux.groupby(QI)["Name"].transform("size")
    a = aux.assign(_n=cls_a)
    m = r[cls_r == 1].merge(a[a["_n"] == 1], on=QI, how="inner")
    res = {"matched": len(m)}
    if truth_names is not None:
        res["correct"] = int((truth_names.loc[m["_rid"].values].values == m["Name"].values).sum())
    return m, res


def generalise(df, pin_digits, dob_level):
    g = df.copy()
    g["PIN_Code"] = g["PIN_Code"].str[:pin_digits] + "*" * (6 - pin_digits) if pin_digits else "******"
    d = g["Date_of_Birth"]
    if dob_level == 1: g["Date_of_Birth"] = d.str[:7]
    elif dob_level == 2: g["Date_of_Birth"] = d.str[:4]
    elif dob_level >= 3:
        y = d.str[:4].astype(int); w = {3: 5, 4: 10, 5: 20}[dob_level]
        lo = (y // w) * w; g["Date_of_Birth"] = lo.astype(str) + "-" + (lo + w - 1).astype(str)
    return g


def k_of(df):
    sizes = df.groupby(QI)["Gender"].transform("size")
    return int(sizes.min()), sizes


def info_loss(pin_digits, dob_level):
    pin_loss = (6 - pin_digits) / 6
    dob_loss = (DOB_WIDTH_DAYS[dob_level] - 1) / (14610 - 1)
    return (pin_loss + dob_loss) / 2


def mape_group_means(orig, key_orig, key_gen, value="Amount"):
    """Utility: answer 'mean Amount per <key_orig>' from data that only retains <key_gen>.
    Returns mean absolute % error of the per-group mean."""
    true = orig.groupby(key_orig)[value].mean()
    approx_by_gen = orig.groupby(key_gen)[value].mean()
    mapping = pd.DataFrame({"o": key_orig, "g": key_gen}).drop_duplicates().set_index("o")["g"]
    est = mapping.reindex(true.index).map(approx_by_gen)
    return float((abs(est - true) / true).mean() * 100)
