"""Isolation-vs-performance trade-off (Task 6): exhaustive search of the decision space.

Decision variables : approach a, dedicated hosts z, SMT off s, overcommit r, SIS hosts k
Objective          : minimise J = alpha*Cost + beta*D + gamma*R
Constraints        : D <= D_max, memory fits (also after losing one host), k <= hosts,
                     vCPUs <= r*cores, SIS never on a shared-kernel container.
"""
from dataclasses import dataclass
from itertools import product
import math

from .config import APPROACHES, HOST, OVERCOMMIT_RATIOS, Host
from . import models


@dataclass(frozen=True)
class Scenario:
    n_sis: int = 150                 # (assumed) SIS / exam / core-LMS instances out of ~400
    u: float = 0.5                   # (assumed) mean CPU use per instance at normal load
    peak_multiplier: float = 1.0     # 3.0 for the registration-week design check
    external_cores_demand: float = 0.0   # cores used by co-located external tenants (0 if none)
    total_hosts: int = 16
    d_max: float = 0.10
    alpha: float = 0.2               # weight on cost
    beta: float = 0.4                # weight on performance degradation
    gamma: float = 0.4               # weight on security risk
    shared_cost_factor: float = 0.6  # (assumed) a shared host is "cheaper" than a dedicated one
    dedicated_risk_factor: float = 0.6   # (assumed) risk multiplier when hosts are dedicated
    smt_off_risk_factor: float = 0.8     # (assumed) risk multiplier when SMT is disabled
    smt_off_cores_factor: float = 0.9    # (assumed, from the assignment's worked example)


def evaluate(a_key: str, dedicated: int, smt_off: int, r: int, k: int,
             sc: Scenario, host: Host = HOST) -> dict:
    a = APPROACHES[a_key]
    cores = host.cores * (sc.smt_off_cores_factor if smt_off else 1.0)
    n = math.ceil(sc.n_sis / k)                       # SIS instances per host
    u = min(1.0, sc.u * sc.peak_multiplier)
    ext = 0.0 if dedicated else sc.external_cores_demand
    demand = n * u + ext
    steal = 0.0 if demand <= cores else 1.0 - cores / demand
    perf = (1.0 - a.h_cpu) * (1.0 - steal)
    D = 1.0 - perf
    mem_ok = n <= models.max_instances_mem(host, a.mem_overhead_mb)
    n_fail = math.ceil(sc.n_sis / (k - 1)) if k > 1 else math.inf
    failover_ok = n_fail <= models.max_instances_mem(host, a.mem_overhead_mb)
    cost = k * (1.0 if dedicated else sc.shared_cost_factor)
    risk = a.base_risk * (sc.dedicated_risk_factor if dedicated else 1.0) \
        * (sc.smt_off_risk_factor if smt_off else 1.0)
    J = sc.alpha * cost / sc.total_hosts + sc.beta * D / sc.d_max + sc.gamma * risk
    violations = []
    if D > sc.d_max: violations.append("degradation>SLA")
    if not mem_ok: violations.append("memory")
    if not failover_ok: violations.append("no N+1 failover")
    if n > r * cores: violations.append("overcommit policy")
    if a_key == "container": violations.append("isolation (shared kernel)")
    return dict(approach=a_key, dedicated=dedicated, smt_off=smt_off, overcommit=r, hosts=k,
                inst_per_host=n, degradation_pct=round(D * 100, 2), cost=round(cost, 2),
                risk=round(risk, 3), J=round(J, 4), feasible=not violations,
                violations=";".join(violations))


def search(sc: Scenario, host: Host = HOST) -> list[dict]:
    rows = [evaluate(a, z, s, r, k, sc, host)
            for a, z, s, r, k in product(APPROACHES, (0, 1), (0, 1), OVERCOMMIT_RATIOS,
                                         range(1, sc.total_hosts + 1))]
    return sorted(rows, key=lambda x: (not x["feasible"], x["J"]))
