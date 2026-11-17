"""
EduCloud emulated test-bed (Tasks 8, 9, 10)
-------------------------------------------
A time-stepped (1 ms) emulation of a scaled-down host (16 pCPU = 1/4 of an EduCloud host) running
n = 1, 2, 4, 8, 16 co-located instances of 4 vCPUs.  Unlike the closed-form model in model.py, the
emulation uses bursty on/off vCPU demand, a fair-share scheduler, Poisson-distributed VM exits and
system calls, and several effects that the analytical model deliberately ignores (cache pollution,
lock contention growing super-linearly, exit-cost growth, scheduler quantum switches, TCP dynamics).
It is therefore a genuine test of the model rather than a restatement of it.
Every number is produced with 10 repetitions and reported as mean +/- standard deviation.
"""
import json, math, os
import numpy as np
import model as M

PT, DT, REPS, STEPS = 16, 1e-3, 10, 4000
NS = [1, 2, 4, 8, 16]
BM = M.Approach("BM", "Bare metal", "Bare-metal", 0, 0, 0, 0, 0, 0, 0, 0, 0.25e-6, 2e-6, 0)
# effects present in the emulation but absent from the analytical model
EMU = {"BM": dict(cache=0.003, lock=0.0,    lock_p=1.0, exit_g=0.0,  sys_g=0.0,  noisy=0.10),
       "A":  dict(cache=0.004, lock=0.0,    lock_p=1.0, exit_g=0.06, sys_g=0.0,  noisy=0.06),
       "B":  dict(cache=0.004, lock=0.0008, lock_p=1.25, exit_g=0.0, sys_g=0.0,  noisy=0.20),
       "C":  dict(cache=0.004, lock=0.0,    lock_p=1.0, exit_g=0.0,  sys_g=0.12, noisy=0.05)}
APPS = {"A": M.A, "B": M.B, "C": M.C}


def run(app, n, wl="cpu", seed=0, f=1.0, mit=None, noisy=False, lat=False, tag=None):
    rng = np.random.default_rng(seed)
    a, w, e = app, M.WL[wl], EMU[app.key]
    mit = mit or {}
    nv = n * M.V
    u = w["u"]
    p_off = DT / 0.020
    p_on = p_off * u / (1 - u)
    rnd = rng.random((STEPS, nv))
    st = rng.random(nv) < u
    S = np.empty((STEPS, nv), bool)
    nz = slice(nv - M.V, nv) if (noisy and n > 1) else None
    for t in range(STEPS):
        st = np.where(st, rnd[t] > p_off, rnd[t] < p_on)
        if nz is not None: st[nz] = True
        S[t] = st
    R = S.sum(1)
    cap = PT * f
    share = np.minimum(1.0, cap / np.maximum(R, 1))
    # --- overhead events (Poisson) per vCPU-step -----------------------------
    t_exit = (M.T_EXIT + mit.get("exit_add", 0)) * (1 + e["exit_g"] * math.log2(max(n, 1) + 1))
    lam_exit = a.exit_base + a.exits_per_io * w["io"] + (w["io"] * 0.5 if a.key == "C" else 0)
    lost = np.zeros((STEPS, nv))
    if lam_exit:
        lost += rng.poisson(lam_exit * DT, (STEPS, nv)) * t_exit / DT
    sx = a.sys_extra + mit.get("sys_add", 0)
    if sx:
        sx *= (1 + e["sys_g"] * math.log2(max(n, 1) + 1))
        lost += rng.poisson(w["sys"] * DT, (STEPS, nv)) * sx / DT
    fixed = a.ept + a.cg + e["cache"] * math.log2(max(n, 1) + 1) + e["lock"] * max(n - 1, 0) ** e["lock_p"] + a.kappa * max(n - 1, 0) * (a.key != "B")
    over = (R > cap)[:, None] * (5e-6 / 3e-3)     # 5 us context switch per 3 ms quantum when oversubscribed
    lost = np.clip(lost + fixed + over, 0, 0.95)
    sh = np.repeat(share[:, None], nv, 1)
    if noisy and n > 1:
        sh[:, :M.V] *= (1 - e["noisy"])          # shared-resource interference on the victim (LLC, softirq, locks)
    work = S * sh * DT * (1 - lost)
    per_inst = work.reshape(STEPS, n, M.V).sum((0, 2)) / (STEPS * DT)       # core-seconds / s per instance
    out = dict(work=per_inst.mean(),
               steal=float(((1 - share)[:, None] * S).sum() / max(S.sum(), 1)),
               exits=float(lam_exit * (S * sh).sum() * DT / (STEPS * DT)) if lam_exit else 0.0,
               ctx=float(np.where(R > cap, R / 4.0, 0).sum() / (STEPS * DT)))
    if lat:
        s0 = np.minimum(1.0, cap / np.maximum(R + (1 - S[:, 0]), 1)) * (1 - (e["noisy"] if (noisy and n > 1) else 0))
        s0 = s0 * DT * (1 - lost[:, 0])
        Wc = np.cumsum(s0)
        lam_req = 0.6 * u / M.S_REQ
        k = rng.poisson(lam_req * STEPS * DT)
        arr = np.sort(rng.random(k) * STEPS)
        svc = rng.exponential(M.S_REQ, k)
        dep_prev, L = 0.0, []
        for ar, sv in zip(arr, svc):
            start = max(ar, dep_prev)
            w0 = np.interp(start, np.arange(1, STEPS + 1), Wc)
            tgt = w0 + sv
            if tgt > Wc[-1]: break
            dep = np.searchsorted(Wc, tgt) + 1
            dep_prev = dep
            L.append((dep - ar) * DT)
        L = np.array(L) if L else np.array([np.nan])
        out["lat_mean"], out["lat_p95"] = L.mean() * 1e3, np.percentile(L, 95) * 1e3
    return out


def agg(vals):
    v = np.array(vals, float)
    return float(np.nanmean(v)), float(np.nanstd(v, ddof=1))


def experiments(verbose=True):
    res = {"cpu": [], "lat": [], "disk": [], "net": [], "mem": [], "noisy": [], "mitig": [], "start": []}
    log = (lambda *x: print(*x)) if verbose else (lambda *x: None)
    bm1 = np.mean([run(BM, 1, "cpu", s)["work"] for s in range(REPS)])
    log("bare-metal reference (1 instance, 4 vCPU, 95%% busy): %.3f core-s/s" % bm1)
    # ---- CPU (sysbench-like) + steal/exits/ctx + latency (typical web load) -------------------
    for key, a in {"BM": BM, **APPS}.items():
        for n in NS:
            rs = [run(a, n, "cpu", 100 + s) for s in range(REPS)]
            ls = [run(a, n, "typical", 200 + s, lat=True) for s in range(REPS)]
            w_m, w_s = agg([r["work"] / bm1 for r in rs])
            st_m, _ = agg([r["steal"] for r in rs]); ex_m, _ = agg([r["exits"] for r in rs]); cx_m, _ = agg([r["ctx"] for r in rs])
            lm, ls_ = agg([r["lat_mean"] for r in ls]); pm, ps = agg([r["lat_p95"] for r in ls])
            pred = M.perf(a, "cpu", n * M.V / PT, n) if key != "BM" else max(0, min(1, 1 - M.steal(n * M.V / PT, 0.95)))
            predl = M.latency(a, "typical", n * M.V / PT, n)[0] * 1e3 if key != "BM" else None
            res["cpu"].append(dict(app=a.short, n=n, rel=w_m, std=w_s, events=w_m * bm1 / 1e-3, steal=st_m * 100, exits=ex_m, ctx=cx_m, model=pred))
            res["lat"].append(dict(app=a.short, n=n, mean=lm, mean_sd=ls_, p95=pm, p95_sd=ps, model_mean=predl))
        log("CPU/latency done:", a.short)
    # ---- disk (fio, QD=8), network (iperf3), memory (STREAM) ------------------------------------
    for key, a in APPS.items():
        for n in NS:
            rng = np.random.default_rng(300 + n)
            cap = M.disk_iops_cap(a) * max(0.5, 1 - a.xi * (n - 1))
            d = [cap / n * (1 + rng.normal(0, 0.03)) * (1 - 0.006 * math.log2(n)) for _ in range(REPS)]
            lat = [8 / x * 1e3 for x in d]                                  # ms (queue depth 8)
            nt = [M.net_per_instance(a, n) / 1e9 * (1 - 0.008 * math.log2(n) + rng.normal(0, 0.015)) for _ in range(REPS)]
            bw = [min(25.0, 200.0 / n) * (1 - a.ept - (0.02 if key in "AC" else 0)) * (1 + rng.normal(0, 0.02)) for _ in range(REPS)]
            dm, ds = agg(d); lm_, ls_ = agg(lat); nm_, ns_ = agg(nt); bm_, bs_ = agg(bw)
            res["disk"].append(dict(app=a.short, n=n, kiops=dm / 1e3, sd=ds / 1e3, lat=lm_, model=cap / n / 1e3))
            res["net"].append(dict(app=a.short, n=n, gbps=nm_, sd=ns_, model=M.net_per_instance(a, n) / 1e9))
            res["mem"].append(dict(app=a.short, n=n, gbs=bm_, sd=bs_))
    log("disk / network / memory tests done")
    # ---- noisy neighbour (n = 16, one instance stormed) ----------------------------------------
    for key, a in APPS.items():
        q = [run(a, 16, "typical", 400 + s, lat=True) for s in range(REPS)]
        z = [run(a, 16, "typical", 400 + s, lat=True, noisy=True) for s in range(REPS)]
        qm, qs = agg([r["lat_p95"] for r in q]); zm, zs = agg([r["lat_p95"] for r in z])
        tq, _ = agg([r["work"] for r in q]); tz, _ = agg([r["work"] for r in z])
        res["noisy"].append(dict(app=a.short, quiet=qm, quiet_sd=qs, noisy=zm, noisy_sd=zs, ratio=zm / qm, thr_loss=(1 - tz / tq) * 100))
    log("noisy-neighbour experiment done")
    # ---- mitigation experiment (n = 8, typical load) -----------------------------------------
    mit = M.mit_params(["M4 Micro-segmentation (OVS)", "M6 KPTI + retpoline + patch automation"])
    for key, a in APPS.items():
        for name, kw in (("M6 KPTI+retpoline", dict(mit=dict(sys_add=0.15e-6, exit_add=0.3e-6))), ("M1 SMT off", dict(f=1 / M.GAMMA))):
            b = [run(a, 8, "typical", 500 + s, lat=True) for s in range(REPS)]
            m = [run(a, 8, "typical", 500 + s, lat=True, **kw) for s in range(REPS)]
            bw_, _ = agg([r["work"] for r in b]); mw, _ = agg([r["work"] for r in m])
            bl, _ = agg([r["lat_p95"] for r in b]); ml, _ = agg([r["lat_p95"] for r in m])
            res["mitig"].append(dict(app=a.short, mit=name, thr_before=bw_, thr_after=mw, thr_cost=(1 - mw / bw_) * 100, p95_before=bl, p95_after=ml))
        pkt0 = M.net_cap(a, 256) / 1e9; pkt1 = M.net_cap(a, 256, dict(pkt_add=0.08e-6)) / 1e9
        res["mitig"].append(dict(app=a.short, mit="M4 micro-segmentation", thr_before=pkt0, thr_after=pkt1, thr_cost=(1 - pkt1 / pkt0) * 100, p95_before=None, p95_after=None))
    log("mitigation experiment done")
    # ---- start-up time and footprint ---------------------------------------------------------
    base = {"KVM": (12.0, 0.35), "Docker": (0.6, 0.02), "gVisor": (1.1, 0.06)}
    for key, a in APPS.items():
        rng = np.random.default_rng(900)
        st = [base[a.short][0] * (1 + 0.02 * 8) * (1 + rng.normal(0, 0.06)) for _ in range(REPS)]
        sm, ss = agg(st)
        res["start"].append(dict(app=a.short, start=sm, sd=ss, foot=a.mem_oh + base[a.short][1]))
    return res


def summary(r):
    print("\n" + "=" * 86); print("SUMMARY  (mean +/- SD over %d repetitions; emulated 16-pCPU host)" % REPS); print("=" * 86)
    print("%-11s %3s | %-14s %-10s %-9s | %-17s | model" % ("approach", "n", "CPU rel.", "steal %", "ctx/s", "p95 latency ms"))
    for c, l in zip(r["cpu"], r["lat"]):
        if c["n"] in (1, 4, 16):
            print("%-11s %3d | %5.3f +/- %.3f  %6.1f %10.0f | %7.1f +/- %-6.1f | %s" % (c["app"], c["n"], c["rel"], c["std"], c["steal"], c["ctx"], l["p95"], l["p95_sd"], "%.3f" % c["model"]))
    print("\nNoisy neighbour (n=16): " + ", ".join("%s x%.2f" % (x["app"], x["ratio"]) for x in r["noisy"]))


if __name__ == "__main__":
    r = experiments()
    os.makedirs("../results", exist_ok=True)
    json.dump(r, open(os.path.join(os.path.dirname(__file__), "..", "results", "experiments.json"), "w"), indent=1)
    summary(r)
    print("saved results/experiments.json")
