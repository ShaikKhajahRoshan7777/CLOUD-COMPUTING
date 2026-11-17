"""Mitigation cost model (Task 7). Costs are (assumed) planning figures - re-estimate them
from your Task 9 with/without-mitigation measurements."""
from dataclasses import dataclass

from .config import APPROACHES, HOST, Host
from . import models


@dataclass(frozen=True)
class Mitigation:
    name: str
    threat: str
    residual: str
    cores_factor: float = 1.0   # usable CPU multiplier (SMT off = 0.9, as in the brief's example)
    h_add: float = 0.0          # extra CPU overhead fraction
    net_factor: float = 1.0     # usable network multiplier
    fleet_factor: float = 1.0   # fleet-wide density multiplier (stranded capacity of dedicated pools)
    transient: bool = False     # cost only applies while the mitigation is active (e.g. during migration)


def kpti_h_add(syscalls_per_s: float = 200_000, extra_us: float = 0.25) -> float:
    """Kernel page-table isolation: extra cost per system call x call rate."""
    return syscalls_per_s * extra_us * 1e-6          # 200k/s * 0.25 us = 5 %


MITIGATIONS = [
    Mitigation("Disable SMT", "cross-VM cache/side-channel (same core)",
               "LLC / memory-bus channels remain", cores_factor=0.90),
    Mitigation("KPTI / kernel page-table isolation", "guest kernel memory disclosure (Meltdown-class)",
               "Spectre-class leaks remain", h_add=kpti_h_add()),
    Mitigation("Dedicated host pool for SIS", "noisy neighbour + co-residency with external tenants",
               "management plane and network attacks remain", fleet_factor=0.75),
    Mitigation("Micro-segmentation (virtual firewall)", "virtual-network sniffing / spoofing",
               "mis-configured rules, compromised endpoint", h_add=0.005, net_factor=0.97),
    Mitigation("Encrypted live migration", "migration traffic exposing guest memory",
               "key management failures", h_add=0.08, transient=True),
    Mitigation("Signed + scanned images", "image tampering / VM sprawl with unpatched guests",
               "signed image can still be vulnerable"),
]


def evaluate(m: Mitigation, approach_key: str = "vm", host: Host = HOST, *, u: float = 0.5,
             D: float = 0.10, instances_planned: int = 25) -> dict:
    """Density and degradation before/after a mitigation for one approach."""
    a = APPROACHES[approach_key]
    base = models.density(host, a, u=u, D=D)
    mod = models.density(host, a, u=u, D=D, cores_factor=m.cores_factor, h_add=m.h_add,
                         net_factor=m.net_factor)
    n_before = base["N_host"]
    # a transient cost (migration) does not change steady-state density; it must be scheduled off-peak
    n_after = n_before if m.transient else int(mod["N_host"] * m.fleet_factor)
    cores = host.cores * m.cores_factor
    d_before = 1 - models.perf_factor(instances_planned, u, host.cores, a.h_cpu)
    d_after = 1 - models.perf_factor(instances_planned, u, cores, a.h_cpu + m.h_add)
    return {"mitigation": m.name, "approach": approach_key,
            "N_host_before": n_before, "N_host_after": n_after,
            "density_cost_pct": round((1 - n_after / n_before) * 100, 1) if n_before else None,
            f"degradation_at_{instances_planned}_inst_before_pct": round(d_before * 100, 2),
            f"degradation_at_{instances_planned}_inst_after_pct": round(d_after * 100, 2),
            "meets_SLA_after": d_after <= D, "transient": m.transient, "threat": m.threat, "residual_risk": m.residual}
