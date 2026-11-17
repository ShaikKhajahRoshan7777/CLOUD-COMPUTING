"""Analytical performance model (Task 3, reused by Tasks 4, 6, 7, 10, 12).

Notation
--------
C   physical cores            r   vCPU:pCPU overcommit ratio
h   fraction of CPU consumed by virtualization overhead
s   steal fraction (ready to run, but no physical CPU available)
u   mean CPU utilisation of one instance (in cores, 1 vCPU each)
N   number of co-located instances on one host
D   allowed performance degradation (SLA), e.g. 0.10
"""
import math
from .config import Approach, Host


def _floor(x: float) -> int:
    return int(math.floor(x + 1e-9))


# ---------------------------------------------------------------- overhead sources
def exit_overhead_fraction(exits_per_s: float, t_exit_us: float = 1.5) -> float:
    """h_exit = E * t_exit.  100 000 exits/s * 1.5 us = 0.15 -> 15 % of a core."""
    return exits_per_s * t_exit_us * 1e-6


def exits_per_s_for_overhead(h: float, t_exit_us: float = 1.5) -> float:
    """Inverse of the above: exit rate that corresponds to an overhead h."""
    return h / (t_exit_us * 1e-6)


def syscall_overhead_fraction(syscalls_per_s: float, t_sys_us: float = 0.2,
                              slowdown: float = 1.0) -> float:
    """Extra CPU lost when each system call costs `slowdown` x the native cost
    (e.g. gVisor-style interception or KPTI).  slowdown = 1 means no extra cost."""
    return syscalls_per_s * (slowdown - 1.0) * t_sys_us * 1e-6


# ---------------------------------------------------------------- CPU
def effective_cpu(r: float, h: float, s: float = 0.0) -> float:
    """Effective per-vCPU capacity in physical-core equivalents: (1/r)(1-h)(1-s)."""
    return (1.0 / r) * (1.0 - h) * (1.0 - s)


def steal_fraction(n: int, u: float, cores: float) -> float:
    """Fair-share steal when aggregate demand n*u exceeds the cores available."""
    demand = n * u
    return 0.0 if demand <= cores else 1.0 - cores / demand


def perf_factor(n: int, u: float, cores: float, h: float) -> float:
    """Performance relative to bare metal: (1 - h) * (1 - steal(n))."""
    return (1.0 - h) * (1.0 - steal_fraction(n, u, cores))


def max_instances_cpu(cores: float, u: float, h: float, D: float, r: float | None = None) -> int:
    """Largest N with perf_factor >= 1 - D.

    (1-h) * min(1, C/(N u)) >= 1-D   =>   N <= C (1-h) / (u (1-D))   (needs h <= D)
    Optionally capped by the overcommit policy N <= r * C (1 vCPU per instance).
    """
    if h > D:
        return 0
    n = _floor(cores * (1.0 - h) / (u * (1.0 - D)))
    if r is not None:
        n = min(n, _floor(r * cores))
    return n


# ---------------------------------------------------------------- memory
def max_instances_mem(host: Host, mem_overhead_mb: float = 0.0, reserve: float | None = None,
                      instance_mem_gb: float | None = None) -> int:
    """Instances per host before ballooning / swapping / page sharing is needed."""
    reserve = host.ram_reserve_frac if reserve is None else reserve
    per = (host.vm_mem_gb if instance_mem_gb is None else instance_mem_gb) + mem_overhead_mb / 1024.0
    return _floor(host.ram_gb * (1.0 - reserve) / per)


# ---------------------------------------------------------------- network / storage
def net_share_gbps(n: int, line_gbps: float, h_io: float = 0.0) -> float:
    """Fair share per instance: L (1-h_io) / N."""
    return line_gbps * (1.0 - h_io) / n


def max_instances_shared(capacity: float, h_io: float, demand_per_instance: float, D: float) -> int:
    """Largest N with L(1-h_io)/N >= (1-D) * demand  (works for Gbps or MB/s)."""
    return _floor(capacity * (1.0 - h_io) / (demand_per_instance * (1.0 - D)))


# ---------------------------------------------------------------- density
def density(host: Host, appr: Approach, *, u: float = 0.5, D: float = 0.10, r: float | None = None,
            net_demand_gbps: float = 0.5, storage_demand_mbps: float = 50.0,
            cores_factor: float = 1.0, h_add: float = 0.0, net_factor: float = 1.0,
            instance_mem_gb: float | None = None) -> dict:
    """N_host = min(N_cpu, N_mem, N_net, N_storage); also reports the limiting resource.

    cores_factor, h_add and net_factor let Task 7 apply a mitigation
    (SMT off -> cores_factor 0.9, KPTI -> h_add, micro-segmentation -> net_factor).
    """
    cores = host.cores * cores_factor
    h = appr.h_cpu + h_add
    n_cpu = max_instances_cpu(cores, u, h, D, r)
    n_mem = max_instances_mem(host, appr.mem_overhead_mb, instance_mem_gb=instance_mem_gb)
    line = host.nic_gbps * host.tenant_nics * net_factor
    n_net = max_instances_shared(line, appr.h_io, net_demand_gbps, D)
    n_sto = max_instances_shared(host.storage_mbps, appr.h_io, storage_demand_mbps, D)
    limits = {"cpu": n_cpu, "memory": n_mem, "network": n_net, "storage": n_sto}
    limiting = min(limits, key=limits.get)
    return {**{f"N_{k}": v for k, v in limits.items()}, "N_host": limits[limiting], "limiting": limiting}


# ---------------------------------------------------------------- latency (Task 4)
def mm1_latency_ms(service_ms: float, rho: float) -> tuple[float, float]:
    """M/M/1 response time: mean = S/(1-rho); response time is exponential so p95 = mean * ln 20."""
    if rho >= 1.0:
        return math.inf, math.inf
    mean = service_ms / (1.0 - rho)
    return mean, mean * math.log(20.0)


def swap_service_factor(demand_gb: float, usable_gb: float, slowdown: float = 1000.0) -> float:
    """Average memory-access slow-down when demand exceeds RAM.
    A fraction p = (demand - usable)/demand of accesses hits swapped pages that are
    `slowdown` x slower (NVMe page-fault ~100 us vs DRAM ~100 ns)."""
    if demand_gb <= usable_gb:
        return 1.0
    p = (demand_gb - usable_gb) / demand_gb
    return (1.0 - p) + p * slowdown
