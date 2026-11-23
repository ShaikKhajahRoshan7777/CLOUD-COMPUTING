"""Fraud-link rule A: an account is flagged if, within ANY 7-day window (days d..d+6), it paid >= 3 DISTINCT beneficiaries.
Events are (account, day, beneficiary). Two implementations: NAIVE all-pairs O(n^2) and KEYED sliding-window O(n log n)."""
from collections import Counter, deque
import numpy as np

WINDOW_DAYS, MIN_DISTINCT = 7, 3


def naive(events):
    """For every event take its day as window start and compare against ALL events (no index, no grouping)."""
    flagged = set()
    for (a, d, _b) in events:
        if a in flagged:
            continue
        ben = set()
        for (a2, d2, b2) in events:
            if a2 == a and 0 <= d2 - d < WINDOW_DAYS:
                ben.add(b2)
        if len(ben) >= MIN_DISTINCT:
            flagged.add(a)
    return flagged


def keyed(acct, day, ben, chunk=1_000_000):
    """acct/day/ben are numpy int arrays. Sort by (account, day), then one pass with a deque + Counter per account.
    Returns (flagged set, max deque length seen, max distinct-beneficiary counter size)."""
    order = np.lexsort((day, acct)); acct, day, ben = acct[order], day[order], ben[order]
    flagged, cur, dq, cnt, maxq, maxc = set(), None, deque(), Counter(), 0, 0
    for s in range(0, len(acct), chunk):
        for a, d, b in zip(acct[s:s + chunk].tolist(), day[s:s + chunk].tolist(), ben[s:s + chunk].tolist()):
            if a != cur:
                cur, dq, cnt = a, deque(), Counter()
            dq.append((d, b)); cnt[b] += 1
            while d - dq[0][0] >= WINDOW_DAYS:
                _, ob = dq.popleft(); cnt[ob] -= 1
                if cnt[ob] == 0: del cnt[ob]
            if len(cnt) >= MIN_DISTINCT: flagged.add(a)
            if len(dq) > maxq: maxq = len(dq)
            if len(cnt) > maxc: maxc = len(cnt)
    return flagged, maxq, maxc


def keyed_events(events):
    names = sorted({e[0] for e in events}); idx = {n: i for i, n in enumerate(names)}
    bens = sorted({e[2] for e in events}); bidx = {n: i for i, n in enumerate(bens)}
    a = np.array([idx[e[0]] for e in events]); d = np.array([e[1] for e in events]); b = np.array([bidx[e[2]] for e in events])
    f, _, _ = keyed(a, d, b); return {names[i] for i in f}


def generate(n, seed=1, hot_share=0.0):
    rng = np.random.default_rng(seed); n_acc = max(n // 10, 1)
    acct = rng.integers(0, n_acc, n).astype(np.int32)
    if hot_share: acct[rng.random(n) < hot_share] = 0
    return acct, rng.integers(0, 365, n).astype(np.int32), rng.integers(0, 50, n).astype(np.int32)


def evidence(events, account):
    """Return (window start day, [(day, beneficiary), ...]) for the first 7-day window with >= 3 distinct beneficiaries."""
    mine = sorted((d, b) for (a, d, b) in events if a == account)
    for d0, _ in mine:
        win = [(d, b) for d, b in mine if 0 <= d - d0 < WINDOW_DAYS]
        if len({b for _, b in win}) >= MIN_DISTINCT:
            return d0, win
    return None, []
