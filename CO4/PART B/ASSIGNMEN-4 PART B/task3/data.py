"""Synthetic beneficiary + public auxiliary datasets (NO real personal data).

Beneficiaries : Name, ID_Number, PIN_Code, Date_of_Birth, Gender, Scheme, Amount   (N = 5,000, seed 2026)
Auxiliary     : Name, PIN_Code, Date_of_Birth, Gender  - a public list (e.g. an electoral-roll-like file)
                covering a random 60% of the same people.
Design        : 25 PIN codes x 14,610 possible birth dates x 2 genders = 730,500 cells for 5,000 people, so
                most people are unique on (PIN, DOB, Gender) - the classic re-identification set-up.
"""
import datetime as dt
import numpy as np, pandas as pd

PINS = ["600001", "600004", "600017", "600020", "600028",      # 4-digit prefix 6000
        "602105", "602106", "602117", "602101", "602102",      # 6021
        "603001", "603002", "603103", "603110", "603202",      # 6030 / 6031 groups
        "631501", "631502", "631551", "631561", "631605",      # 6315 / 6316
        "632001", "632002", "632104", "632115", "632301"]      # 6320 / 6321 / 6323
FIRST = ["Aarav", "Divya", "Karthik", "Meena", "Suresh", "Lakshmi", "Arjun", "Priya", "Ravi", "Kavitha", "Vijay", "Anitha",
         "Manoj", "Deepa", "Naveen", "Revathi", "Harish", "Sangeetha", "Gokul", "Nandhini"]
LAST = ["Kumar", "Raj", "Selvam", "Murugan", "Iyer", "Pillai", "Nair", "Reddy", "Babu", "Devi", "Krishnan", "Subramanian", "Rao", "Naidu"]
SCHEMES = ["Old-Age Pension", "Widow Pension", "Scholarship", "Farm Subsidy", "Health Cover"]
BASE_AMT = {"Old-Age Pension": 1200, "Widow Pension": 1000, "Scholarship": 2500, "Farm Subsidy": 4000, "Health Cover": 1800}
REF = dt.date(2026, 1, 1)


def make_beneficiaries(n=5000, seed=2026):
    rng = np.random.default_rng(seed)
    start = dt.date(1960, 1, 1); span = (dt.date(1999, 12, 31) - start).days + 1   # 14,610 days
    dob = [start + dt.timedelta(days=int(d)) for d in rng.integers(0, span, n)]
    pin = rng.choice(PINS, n)
    gender = rng.choice(["M", "F"], n)
    scheme = rng.choice(SCHEMES, n, p=[0.30, 0.15, 0.15, 0.25, 0.15])
    age = np.array([(REF - d).days / 365.25 for d in dob])
    pref = sorted({p[:4] for p in PINS}); fac = [0.85, 0.95, 1.0, 1.1, 1.25, 1.35, 0.9, 1.05, 1.2]
    region = {q: fac[i % len(fac)] for i, q in enumerate(pref)}
    amount = np.array([BASE_AMT[s] for s in scheme]) * (1 + 0.012 * (age - 40)) * np.array([region[p[:4]] for p in pin]) * rng.lognormal(0, 0.12, n)
    names = ["%s %s %d" % (FIRST[i % 20], LAST[(i * 7 + 3) % 14], i) for i in range(n)]      # unique synthetic names
    df = pd.DataFrame({"Name": names, "ID_Number": ["BEN%08d" % (10_000_000 + i * 37) for i in range(n)], "PIN_Code": pin,
                       "Date_of_Birth": [d.isoformat() for d in dob], "Gender": gender, "Scheme": scheme, "Amount": amount.round(2)})
    return df


def make_auxiliary(ben, share=0.60, seed=99):
    rng = np.random.default_rng(seed)
    idx = rng.choice(len(ben), int(len(ben) * share), replace=False)
    return ben.loc[np.sort(idx), ["Name", "PIN_Code", "Date_of_Birth", "Gender"]].reset_index(drop=True)
