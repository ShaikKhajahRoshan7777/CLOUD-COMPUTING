"""Single source of truth for every parameter used by the models.

Values tagged (given) come straight from the assignment brief.
Values tagged (assumed) are modelling assumptions - state and justify them in
your report, and replace them with your own measurements where you can
(e.g. h_cpu / h_io / mem_overhead_mb from Task 9).
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Host:
    cores: int = 64                  # (given) physical cores per host
    ram_gb: float = 512.0            # (given)
    vm_mem_gb: float = 8.0           # (given) average VM memory demand
    nic_gbps: float = 25.0           # (given) per NIC line rate
    nics: int = 2                    # (given) NICs per host
    t_exit_us: float = 1.5           # (given) cost of one VM exit
    t_sys_us: float = 0.2            # (given) native system-call cost
    tenant_nics: int = 1             # (assumed) 1 NIC for tenant traffic, 1 for storage/migration
    storage_mbps: float = 3000.0     # (assumed) usable NVMe MB/s - replace with your fio baseline
    ram_reserve_frac: float = 0.10   # (assumed) RAM kept for host OS / hypervisor / margin


@dataclass(frozen=True)
class Approach:
    key: str
    label: str
    h_cpu: float            # (assumed) fraction of CPU lost to virtualization
    h_io: float             # (assumed) fraction of NIC/storage bandwidth lost to the virtual I/O path
    mem_overhead_mb: float  # (assumed) fixed memory footprint per instance beyond the workload
    base_risk: float        # (assumed) qualitative 0..1 risk score derived from the Task 5 threat table


OVERCOMMIT_RATIOS = (1, 2, 4, 8)   # (given) vCPU:pCPU

APPROACHES = {
    "vm": Approach("vm", "Type-1 VM (KVM/QEMU)", h_cpu=0.05, h_io=0.08,
                   mem_overhead_mb=1024, base_risk=0.25),
    "container": Approach("container", "OS-level container (Docker/Podman)", h_cpu=0.02, h_io=0.04,
                          mem_overhead_mb=120, base_risk=0.70),
    "microvm": Approach("microvm", "Micro-VM / sandbox (Kata/Firecracker)", h_cpu=0.07, h_io=0.10,
                        mem_overhead_mb=256, base_risk=0.20),
}

SLA_MAX_DEGRADATION = 0.10   # (given) <= 10 % degradation target
HOST = Host()

# Map benchmark back-ends (Task 8) onto the model approaches (Task 3).
MODEL_KEY = {"kvm": "vm", "docker": "container", "kata": "microvm", "gvisor": "microvm"}
