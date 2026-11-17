"""Task 12 - Day-4 design challenge: external Spark/Hadoop tenants, 3x peak, live migration.

Compares the ORIGINAL hybrid design (everything shares hosts / NICs) with the MODIFIED
design (separate host pools, quotas, SR-IOV for research, separate migration NIC).
All numbers are (assumed) - adjust Day4Assumptions to match your own measurements.
"""
from dataclasses import dataclass
import math

from .config import APPROACHES, HOST, Host
from . import models


@dataclass(frozen=True)
class Day4Assumptions:
    sis_vms: int = 150                      # SIS / exam / core LMS instances
    internal_vms: int = 250                 # other departmental instances (400 total)
    u: float = 0.4                          # SIS CPU use per vCPU at normal load
    peak_multiplier: float = 3.0            # (given) registration week ~3x
    sis_net_gbps_per_host: float = 6.0      # SIS tenant traffic per SIS host at normal load
    research_net_gbps_per_host: float = 15.0   # sustained Spark shuffle traffic if co-located
    migration_gbps: float = 10.0            # live-migration stream when it shares the tenant NIC
    research_workers: int = 64              # external Spark/Hadoop workers
    worker_vcpu: int = 4
    worker_mem_gb: float = 32.0
    worker_util: float = 0.9                # batch jobs keep CPUs busy
    h_io_sriov: float = 0.02                # (assumed) virtual-switch cost removed by SR-IOV
    spare_hosts: int = 1                    # N+1 for patching / failure
    total_hosts: int = 16


def shared_design(a: Day4Assumptions, host: Host = HOST, approach: str = "vm",
                  migrating: bool = False) -> dict:
    """ORIGINAL design: external workers share SIS hosts and the tenant NIC (fair-share)."""
    ap = APPROACHES[approach]
    demand = a.sis_net_gbps_per_host * a.peak_multiplier + a.research_net_gbps_per_host \
        + (a.migration_gbps if migrating else 0.0)
    capacity = host.nic_gbps * host.tenant_nics * (1 - ap.h_io)
    net_ratio = min(1.0, capacity / demand)
    # CPU: SIS instances per host + research workers spread over all 16 hosts
    sis_per_host = math.ceil(a.sis_vms / a.total_hosts)
    workers_per_host = math.ceil(a.research_workers / a.total_hosts)
    u_peak = min(1.0, a.u * a.peak_multiplier)
    cpu_demand = sis_per_host * u_peak + workers_per_host * a.worker_vcpu * a.worker_util
    cpu_perf = (1 - ap.h_cpu) * (1 - models.steal_fraction(1, cpu_demand, host.cores))
    perf = min(net_ratio, cpu_perf)
    return {"design": "original (shared hosts)" + (" + migration" if migrating else ""),
            "net_demand_gbps": round(demand, 1), "net_capacity_gbps": round(capacity, 1),
            "net_ratio": round(net_ratio, 3), "cpu_demand_cores": round(cpu_demand, 1),
            "sis_perf": round(perf, 3), "sis_degradation_pct": round((1 - perf) * 100, 1),
            "meets_SLA": (1 - perf) <= 0.10, "student_data_isolated_from_external": False}


def pool_sizes(a: Day4Assumptions, host: Host = HOST) -> dict:
    """MODIFIED design: size the three host pools."""
    vm, mv = APPROACHES["vm"], APPROACHES["microvm"]
    u_peak = min(1.0, a.u * a.peak_multiplier)
    sis_n = models.density(host, vm, u=u_peak, net_demand_gbps=0.5)["N_host"]
    sis_hosts = math.ceil(a.sis_vms / sis_n) + a.spare_hosts
    int_n = models.density(host, vm, u=a.u)["N_host"]
    int_hosts = math.ceil(a.internal_vms / int_n)
    w_mem = models.max_instances_mem(host, mv.mem_overhead_mb, instance_mem_gb=a.worker_mem_gb)
    w_cpu = models.max_instances_cpu(host.cores, a.worker_vcpu * a.worker_util, mv.h_cpu, 0.10)
    w_per_host = min(w_mem, w_cpu)
    ext_hosts = math.ceil(a.research_workers / w_per_host)
    total = sis_hosts + int_hosts + ext_hosts
    nic = host.nic_gbps * host.tenant_nics
    return {"SIS pool hosts (Type-1 VMs)": sis_hosts, "SIS instances/host at peak": sis_n,
            "Internal pool hosts (VMs + containers)": int_hosts,
            "External pool hosts (micro-VMs)": ext_hosts, "workers/host (external)": w_per_host,
            "external NIC Gbps (virtual switch)": round(nic * (1 - mv.h_io), 2),
            "external NIC Gbps (SR-IOV)": round(nic * (1 - a.h_io_sriov), 2),
            "total hosts needed": total, "hosts available": a.total_hosts,
            "fits_in_16_hosts": total <= a.total_hosts}


def modified_design(a: Day4Assumptions, host: Host = HOST, migrating: bool = True) -> dict:
    """MODIFIED design: SIS pool has the tenant NIC to itself; migration uses the 2nd NIC."""
    ap = APPROACHES["vm"]
    demand = a.sis_net_gbps_per_host * a.peak_multiplier
    capacity = host.nic_gbps * host.tenant_nics * (1 - ap.h_io)
    net_ratio = min(1.0, capacity / demand)
    sizes = pool_sizes(a, host)
    sis_n = math.ceil(a.sis_vms / sizes["SIS pool hosts (Type-1 VMs)"])   # spread over the whole pool
    u_peak = min(1.0, a.u * a.peak_multiplier)
    cpu_perf = (1 - ap.h_cpu) * (1 - models.steal_fraction(sis_n, u_peak, host.cores))
    perf = min(net_ratio, cpu_perf)
    # Migration runs on the 2nd NIC (encrypted), so it does not touch the tenant NIC.
    # Its CPU cost (~8 %, see mitigation.py) only hits the source host and is scheduled off-peak.
    return {"design": "modified (separate pools)" + (" + migration" if migrating else ""),
            "net_demand_gbps": round(demand, 1), "net_capacity_gbps": round(capacity, 1),
            "net_ratio": round(net_ratio, 3), "cpu_demand_cores": round(sis_n * u_peak, 1),
            "sis_perf": round(perf, 3), "sis_degradation_pct": round((1 - perf) * 100, 1),
            "meets_SLA": (1 - perf) <= 0.10, "student_data_isolated_from_external": True}


def sis_net_ratio_curve(a: Day4Assumptions, multipliers, host: Host = HOST) -> list[dict]:
    """SIS bandwidth satisfaction vs registration-peak multiplier (for the Task 12 graph)."""
    ap = APPROACHES["vm"]
    cap = host.nic_gbps * host.tenant_nics * (1 - ap.h_io)
    rows = []
    for m in multipliers:
        sis = a.sis_net_gbps_per_host * m
        rows.append({"peak_multiplier": m,
                     "shared": min(1.0, cap / (sis + a.research_net_gbps_per_host)),
                     "shared_migrating": min(1.0, cap / (sis + a.research_net_gbps_per_host + a.migration_gbps)),
                     "separate_pools": min(1.0, cap / sis)})
    return rows
