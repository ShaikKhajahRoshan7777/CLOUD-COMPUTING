#!/usr/bin/env python3
"""TASK 3 - quantitative model: CPU, memory, network, storage and density tables + worked examples."""
import pandas as pd
from _common import save_table, RESULTS
from educloud import models
from educloud.config import APPROACHES, HOST, OVERCOMMIT_RATIOS


def main():
    # --- CPU: effective capacity per vCPU = (1/r)(1-h)(1-s)
    rows = []
    for r in OVERCOMMIT_RATIOS:
        row = {"overcommit": f"{r}:1", "ideal_share": 1 / r}
        for k, a in APPROACHES.items():
            row[f"{k}_h={a.h_cpu:.0%}"] = round(models.effective_cpu(r, a.h_cpu), 4)
        row["vm_h=5%_steal=10%"] = round(models.effective_cpu(r, APPROACHES["vm"].h_cpu, 0.10), 5)
        rows.append(row)
    save_table(pd.DataFrame(rows), "task3_cpu_capacity")

    # --- VM-exit cost: E * 1.5 us
    ex = [{"exits_per_s": e, "cpu_fraction_pct": round(models.exit_overhead_fraction(e, HOST.t_exit_us) * 100, 2)}
          for e in (10_000, 33_333, 100_000, 300_000)]
    save_table(pd.DataFrame(ex), "task3_vm_exit_cost")
    print(f"\nh = 5 % corresponds to {models.exits_per_s_for_overhead(0.05):,.0f} exits/s per vCPU")

    # --- memory
    mem = [{"approach": k, "per_instance_GB": HOST.vm_mem_gb + a.mem_overhead_mb / 1024,
            "N_max_no_reserve": models.max_instances_mem(HOST, a.mem_overhead_mb, reserve=0.0),
            "N_max_10pct_reserve": models.max_instances_mem(HOST, a.mem_overhead_mb)}
           for k, a in APPROACHES.items()]
    mem.insert(0, {"approach": "brief: 8 GB flat", "per_instance_GB": 8.0,
                   "N_max_no_reserve": models.max_instances_mem(HOST, 0, reserve=0.0),
                   "N_max_10pct_reserve": models.max_instances_mem(HOST, 0)})
    save_table(pd.DataFrame(mem), "task3_memory")

    # --- network share
    net = []
    for n in (1, 2, 4, 8, 16):
        row = {"instances": n, "ideal_gbps": models.net_share_gbps(n, HOST.nic_gbps)}
        for k, a in APPROACHES.items():
            row[f"{k}_gbps"] = round(models.net_share_gbps(n, HOST.nic_gbps, a.h_io), 3)
        net.append(row)
    save_table(pd.DataFrame(net), "task3_network_share")

    # --- steal/perf vs number of instances (u = 1 : CPU-bound instances)
    perf = []
    for n in (16, 32, 48, 64, 80, 96, 128):
        row = {"instances_on_host": n, "overcommit": round(n / HOST.cores, 2)}
        for k, a in APPROACHES.items():
            row[f"{k}_perf"] = round(models.perf_factor(n, 1.0, HOST.cores, a.h_cpu), 3)
        perf.append(row)
    save_table(pd.DataFrame(perf), "task3_perf_vs_instances")

    # --- density under the 10 % SLA
    dens = []
    for u in (0.25, 0.5, 1.0):
        for k, a in APPROACHES.items():
            dens.append({"u": u, "approach": k, **models.density(HOST, a, u=u)})
    save_table(pd.DataFrame(dens), "task3_density")
    print(f"\nResults written to {RESULTS}")


if __name__ == "__main__":
    main()
