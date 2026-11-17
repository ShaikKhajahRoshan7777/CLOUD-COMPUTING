#!/usr/bin/env python3
"""TASK 4 - best / typical / worst case predictions from the Task 3 model.

Per instance:   S   = S0 / ((1-h)(1-steal)) * swap_factor       (service time grows with overhead,
                                                                  steal time and swapping)
                rho = lambda * S = u * S / S0                    (lambda = u / S0 requests per ms)
                mean latency = S / (1 - rho),  p95 = mean * ln 20  (M/M/1 response time)
S0 = 10 ms is an assumed bare-metal request CPU time.
"""
import math
import pandas as pd
from _common import save_table
from educloud import models
from educloud.config import APPROACHES, HOST

S0_MS = 10.0
USABLE_GB = HOST.ram_gb * (1 - HOST.ram_reserve_frac)

# mig = share of host CPU taken by encrypted migration + dirty-page re-copy (assumed 30 % for a bulk evacuation)
# name: dict(n=instances/host, u=CPU use per instance, noisy=cores burnt by a noisy neighbour,
#            mem_gb=aggregate guest memory demand, mig=CPU fraction taken by live migration)
SCENARIOS = {
    "best: light load, no noise":              dict(n=16, u=0.20, noisy=0.0,  mem_gb=16 * 8.0,  mig=0.0),
    "typical: registration-week web+DB":       dict(n=25, u=0.60, noisy=0.0,  mem_gb=25 * 8.0,  mig=0.0),
    "worst-A: noisy neighbour (CPU)":          dict(n=25, u=0.60, noisy=60.0, mem_gb=25 * 8.0,  mig=0.0),
    "worst-B: memory overcommit + swapping":   dict(n=25, u=0.60, noisy=0.0,  mem_gb=25 * 8.0 * 2.3, mig=0.0),
    "worst-C: bulk live migration at peak":    dict(n=50, u=0.90, noisy=0.0,  mem_gb=50 * 8.0,  mig=0.30),
}


def main():
    rows = []
    for scen, p in SCENARIOS.items():
        for k, a in APPROACHES.items():
            footprint = p["mem_gb"] + p["n"] * a.mem_overhead_mb / 1024
            swap = models.swap_service_factor(footprint, USABLE_GB)
            cores = HOST.cores * (1 - p["mig"])
            steal = models.steal_fraction(1, p["n"] * p["u"] + p["noisy"], cores)
            service = S0_MS / ((1 - a.h_cpu) * (1 - steal)) * swap
            rho = p["u"] * service / S0_MS
            mean, p95 = models.mm1_latency_ms(service, rho)
            rows.append({"condition": scen, "approach": k, "steal_pct": round(steal * 100, 1),
                         "swap_slowdown_x": round(swap, 1), "service_ms": round(service, 2),
                         "rho": round(rho, 3),
                         "mean_ms": "saturated" if math.isinf(mean) else round(mean, 1),
                         "p95_ms": "saturated" if math.isinf(p95) else round(p95, 1)})
    save_table(pd.DataFrame(rows), "task4_conditions")


if __name__ == "__main__":
    main()
