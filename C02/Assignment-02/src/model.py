"""
EduCloud analytical performance + security model  (Tasks 2, 3, 4, 5, 6, 7, 12)
-------------------------------------------------------------------------------
Three architecturally distinct virtualization approaches are modelled:
    A  KVM/QEMU  : Type-1, hardware-assisted full virtualization (VM-based)
    B  Docker    : OS-level virtualization / runc containers (container-based)
    C  gVisor    : sandboxed container runtime (user-space kernel, runsc, KVM platform)

Host parameters from the assignment table are constants; every other number is a
stated ASSUMPTION (see the 'stated assumptions' block and the report, Task 3).
"""
import math
from dataclasses import dataclass

# ---------------- given host parameters (assignment table) ----------------
P        = 64          # physical cores per host
RAM_GB   = 512         # RAM per host
M_VM     = 8.0         # average memory demand per instance (GB)
T_EXIT   = 1.5e-6      # cost of one VM exit (s)
T_SYS    = 0.2e-6      # native system-call cost (s)
LINE_BPS = 25e9        # network line rate (bit/s)
RATIOS   = [1, 2, 4, 8]

# ---------------- stated assumptions --------------------------------------
V         = 4          # vCPUs per instance
HOST_RES  = 16.0       # GB reserved for host OS / hypervisor
GAMMA     = 1.25       # SMT throughput gain (the 64 "cores" are SMT-on capacity)
K_IO      = 4          # cores that process virtual I/O (vhost / softirq)
D_SLO     = 0.10       # service-level target: <= 10 % degradation
IOPS_DEV  = 1.0e6      # NVMe 4 KiB random-read capability per host
HDR       = 38         # Ethernet framing overhead per packet (bytes)


@dataclass
class Approach:
    key: str
    name: str
    short: str
    mem_oh: float        # GB per instance (QEMU, Sentry, runtime)
    ksm: float           # fraction of RAM shareable by page-sharing
    exit_base: float     # exits / s / vCPU (timers, IPIs, HLT ...)
    exits_per_io: float  # exits per I/O operation after virtio batching
    ept: float           # fixed nested/extended page-walk overhead (fraction)
    sys_extra: float     # extra seconds per syscall (interception)
    cg: float            # constant cgroup / seccomp / accounting overhead
    kappa: float         # contention overhead per extra co-located instance
    c_pkt: float         # CPU seconds per packet in the virtual NIC path
    c_io: float          # CPU seconds per storage I/O in the virtual block path
    xi: float            # I/O sharing contention per extra instance


A = Approach("A", "KVM/QEMU hardware-assisted VM", "KVM", 0.30, 0.15, 4000, 0.5, 0.015, 0.0, 0.000, 0.0002,
             0.25e-6 + T_EXIT / 16 + 0.15e-6, 2e-6 + T_EXIT / 4 + 1e-6, 0.004)
B = Approach("B", "Docker/runc container", "Docker", 0.05, 0.05, 0, 0.0, 0.000, 0.03e-6, 0.005, 0.0006,
             0.45e-6, 2.4e-6, 0.008)
C = Approach("C", "gVisor sandboxed container", "gVisor", 0.15, 0.10, 0, 0.0, 0.015, T_EXIT + 0.8e-6, 0.005, 0.0003,
             3.0e-6, 10e-6, 0.006)
APPROACHES = [A, B, C]

# workload profiles: u = average vCPU utilisation, sys = syscalls/s/vCPU, io = I/O ops/s/vCPU
WL = {
    "cpu":     dict(u=0.95, sys=2e3,   io=1e2,  label="CPU-bound"),
    "best":    dict(u=0.25, sys=20e3,  io=2e3,  label="Best case"),
    "typical": dict(u=0.50, sys=100e3, io=10e3, label="Typical (registration web + DB)"),
    "peak3x":  dict(u=0.75, sys=150e3, io=15e3, label="Registration peak (3x normal)"),
    "worst":   dict(u=0.90, sys=400e3, io=80e3, label="Worst case (I/O storm)"),
    "bigdata": dict(u=0.85, sys=250e3, io=60e3, label="Spark/Hadoop batch"),
}


# ---------------- CPU model ------------------------------------------------
def overhead(a, wl, n=1, mit=None):
    """Virtualization overhead fraction o (Task 3, eq. 2)."""
    m = mit or {}
    t_exit = T_EXIT + m.get("exit_add", 0.0)
    sys_x = a.sys_extra + m.get("sys_add", 0.0)
    w = WL[wl] if isinstance(wl, str) else wl
    o = (a.exit_base + a.exits_per_io * w["io"]) * t_exit if (a.exit_base or a.exits_per_io) else 0.0
    o += a.ept + w["sys"] * sys_x + a.cg + a.kappa * max(n - 1, 0)
    if a.key == "C":
        o += (w["io"] * 0.5) * T_EXIT          # gofer / KVM-platform transitions per I/O
    return min(o, 0.95)


def steal(r, u, f=1.0):
    """Steal fraction sigma = max(0, 1 - f/(r*u))  (Task 3, eq. 1)."""
    return max(0.0, 1.0 - f / (r * u))


def perf(a, wl, r, n=1, f=1.0, mit=None):
    w = WL[wl]
    return (1 - steal(r, w["u"], f)) * (1 - overhead(a, wl, n, mit))


def cpu_capacity(a, wl, r, n=1, f=1.0, mit=None):
    """Effective per-VM CPU capacity in core-equivalents while busy (Task 3, eq. 3)."""
    return V * perf(a, wl, r, n, f, mit)


# ---------------- memory model ---------------------------------------------
def n_mem(a, ksm=False):
    per = M_VM * ((1 - a.ksm) if ksm else 1.0) + a.mem_oh
    return int((RAM_GB - HOST_RES) // per)


# ---------------- I/O + network model -------------------------------------
def net_cap(a, S=1500, mit=None):
    """Aggregate goodput cap (bit/s): min(line goodput, CPU-bound virtual NIC path)."""
    c = a.c_pkt + (mit or {}).get("pkt_add", 0.0)
    return min(LINE_BPS * S / (S + HDR), K_IO * S * 8 / c)


def net_per_instance(a, n, S=1500, demand=float("inf"), mit=None):
    W = net_cap(a, S, mit) * max(0.5, 1 - a.xi * (n - 1))
    return min(demand, W / n)


def disk_iops_cap(a):
    return min(IOPS_DEV, K_IO / a.c_io)


# ---------------- density model -------------------------------------------
def r_max(a, wl, f=1.0, D=D_SLO, mit=None):
    """Largest overcommit ratio meeting the <= D degradation SLO (Task 3, eq. 5); fixed point in n."""
    w = WL[wl]
    n = 0
    r = 0.0
    for _ in range(20):
        o = overhead(a, wl, max(n, 1), mit)
        if o >= D:
            return 0.0
        r = f * (1 - o) / (w["u"] * (1 - D))
        n = int(r * P // V)
    return r


def density(a, wl, f=1.0, D=D_SLO, b_req=0.1e9, S=256, mit=None):
    r = r_max(a, wl, f, D, mit)
    n_cpu = int(r * P // V)
    nm = n_mem(a)
    n_io = int(net_cap(a, S, mit) // b_req)
    lim = [n_cpu, nm, n_io]
    return dict(r_max=r, n_cpu=n_cpu, n_mem=nm, n_io=n_io, n=min(lim), limit=["CPU", "memory", "network"][lim.index(min(lim))])


# ---------------- latency model (M/M/1 per worker thread) ------------------
S_REQ = 2e-3   # 2 ms of CPU per request


def latency(a, wl, r, n=1, f=1.0, mit=None):
    pi = max(perf(a, wl, r, n, f, mit), 1e-3)
    s_eff = S_REQ / pi
    rho = min(0.98, 0.6 * WL[wl]["u"] / pi)          # 60 % of vCPU load is request work
    mean = s_eff / (1 - rho)
    return mean, mean * math.log(20)                  # mean, p95 of exponential response time


# ---------------- security model (Tasks 5 / 6 / 7) ------------------------
THREATS = [  # id, name, (C, I, A) impact severity on student records (1..5)
    ("T1", "Guest-to-host escape (VM escape / container breakout)", (5, 5, 4)),
    ("T2", "Cross-tenant side channel (cache / SMT / speculative)", (5, 2, 1)),
    ("T3", "Hypervisor / runtime / shared-kernel vulnerability", (5, 5, 5)),
    ("T4", "VM sprawl and unpatched guest kernels", (4, 4, 3)),
    ("T5", "Image tampering and uncontrolled image copying", (3, 5, 3)),
    ("T6", "Insecure live migration (memory in transit)", (5, 4, 2)),
    ("T7", "Virtual-network sniffing / spoofing", (4, 4, 2)),
]
EXPO = {  # exposure 1 (low) .. 5 (high), justified from the trust boundaries in the report
    "A": dict(T1=2, T2=4, T3=3, T4=4, T5=3, T6=3, T7=3),
    "B": dict(T1=5, T2=5, T3=5, T4=2, T5=3, T6=2, T7=4),
    "C": dict(T1=3, T2=4, T3=3, T4=2, T5=3, T6=2, T7=3),
}
MITIGATIONS = {  # name -> (threat multipliers, cost parameters)
    "M1 Disable SMT": ({"T2": 0.5}, dict(f=1 / GAMMA)),
    "M2 Dedicated hosts (SIS pool)": ({"T1": 0.25, "T2": 0.25, "T3": 0.25}, dict(pool=True)),
    "M3 Image signing + registry": ({"T5": 0.2}, dict(startup_s=1.2)),
    "M4 Micro-segmentation (OVS)": ({"T7": 0.3}, dict(pkt_add=0.08e-6)),
    "M5 Encrypted live migration": ({"T6": 0.2}, dict(mig_x=1.15)),
    "M6 KPTI + retpoline + patch automation": ({"T2": 0.8, "T4": 0.4}, dict(sys_add=0.15e-6, exit_add=0.3e-6)),
}


def impact(t):
    return sum(t[2]) / 3


def risk(key, mits=()):
    e = dict(EXPO[key])
    for m in mits:
        for t, k in MITIGATIONS[m][0].items():
            e[t] = max(1.0, e[t] * k)
    num = sum(e[t[0]] * impact(t) for t in THREATS)
    den = sum(5 * impact(t) for t in THREATS)
    return num / den                       # 0..1 normalised residual risk


def isolation(key, mits=()):
    return 1 - risk(key, mits)


# ---------------- Task 6: isolation-performance optimisation ---------------
def mit_params(mits):
    d = {}
    for m in mits:
        c = MITIGATIONS[m][1]
        for k in ("pkt_add", "sys_add", "exit_add"):
            d[k] = d.get(k, 0) + c.get(k, 0)
    return d


ALWAYS_ON = ("M3 Image signing + registry", "M4 Micro-segmentation (OVS)",
             "M5 Encrypted live migration", "M6 KPTI + retpoline + patch automation")


def optimise(n_inst=400, wl="typical", iso_min=0.0, lam=2.0, H_max=16, need_hw_boundary=False, always=ALWAYS_ON):
    rows = []
    for a in APPROACHES:
        for smt_off in (False, True):
            for dedicated in (False, True):
                mits = list(always) + (["M1 Disable SMT"] if smt_off else []) + (["M2 Dedicated hosts (SIS pool)"] if dedicated else [])
                f = 1 / GAMMA if smt_off else 1.0
                d = density(a, wl, f=f, mit=mit_params(mits))
                n = max(d["n"], 0)
                H = math.ceil(n_inst / n) if n > 0 else 99
                if dedicated:
                    H = math.ceil(H * 1.15)        # pool fragmentation: slack is not shared across pools
                rk = risk(a.key, mits)
                J = H / H_max + lam * rk
                feas = (n > 0) and H <= H_max and (1 - rk) >= iso_min and not (need_hw_boundary and a.key == "B")
                rows.append(dict(approach=a.short, smt_off=smt_off, dedicated=dedicated, n=n, H=H,
                                 risk=rk, iso=1 - rk, J=J, feasible=feas, limit=d["limit"]))
    return rows


def report():
    line = "-" * 78
    print("EDUCLOUD ANALYTICAL MODEL  (host: %d cores, %d GB RAM, %d vCPU/instance)" % (P, RAM_GB, V)); print(line)
    print("[CPU] per-instance effective capacity (core-equivalents) - typical load, u=%.2f, n=25 instances" % WL["typical"]["u"])
    print("%-8s" % "ratio" + "".join("%-12s" % a.short for a in APPROACHES))
    for r in RATIOS:
        print("%-8s" % ("%d:1" % r) + "".join("%-12.3f" % cpu_capacity(a, "typical", r, 25) for a in APPROACHES))
    print("%-8s" % "o (%)" + "".join("%-12.2f" % (100 * overhead(a, "typical", 25)) for a in APPROACHES)); print(line)
    print("[MEMORY] max instances/host before ballooning / swapping (and with page sharing)")
    for a in APPROACHES: print("  %-8s N_mem = floor((%d-%d)/(%.0f+%.2f)) = %d   with KSM = %d" % (a.short, RAM_GB, HOST_RES, M_VM, a.mem_oh, n_mem(a), n_mem(a, True)))
    print(line); print("[NETWORK / DISK] aggregate caps")
    for a in APPROACHES:
        print("  %-8s bulk 1500B: %5.1f Gbit/s | web 256B: %5.1f Gbit/s | disk: %7.0f IOPS | per-VM share n=8: %.2f Gbit/s" % (a.short, net_cap(a)/1e9, net_cap(a, 256)/1e9, disk_iops_cap(a), net_per_instance(a, 8)/1e9))
    print(line); print("[DENSITY] instances per host meeting <=10% degradation")
    print("%-26s" % "scenario" + "".join("%-22s" % a.short for a in APPROACHES))
    for w in ("best", "typical", "peak3x", "worst"):
        row = ""
        for a in APPROACHES:
            d = density(a, w); row += "%-22s" % ("%d (r<=%.2f, %s)" % (d["n"], d["r_max"], d["limit"]))
        print("%-26s" % WL[w]["label"][:25] + row)


if __name__ == "__main__":
    report()
