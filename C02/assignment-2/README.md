# EduCloud – Virtualization Architecture Analysis (CSA15, CO2, Assignment 2)

Python code, models and experiment scripts for **"Analyse, Evaluate and Validate a Virtualization
Architecture for a Multi-Tenant University Private Cloud"**.
Student: *SHAIK KHAJAH ROSHAN* · Reg. no. *192511445* · SIMATS Engineering, Dept. of IT.

Three approaches are compared – **Type-1 VM (KVM/QEMU)**, **OS-level containers (Docker/Podman)** and
**micro-VM / sandbox (Kata Containers, gVisor)** – on the EduCloud host (64 cores, 512 GB, 2 × 25 Gbps),
including the Day-4 requirement (external Spark/Hadoop tenants, 3× peak, live migration, regulated isolation).

> **Honesty note.** Tasks 3, 4, 6, 7 and 12 are *analytical* – the overhead fractions `h` and a few
> other inputs are **assumptions** (tagged `(assumed)` in `educloud/config.py`). Tasks 8–10 need *real*
> measurements from your own machine. `make demo` generates **synthetic** data only to test the
> plotting pipeline – it is never a result and must not appear in the report.

## Quick start

```bash
git clone <your-repo-url> && cd educloud-virtualization-assignment
python3 -m venv .venv && source .venv/bin/activate
make install          # numpy, pandas, matplotlib
make test             # 21 unit tests
make model            # Tasks 3, 4, 6, 7, 12  -> tables + figures in results/
```

## Which file answers which task

| Task | Marks | What | Run |
|---|---|---|---|
| 1, 2 | 5+2 | Architectures, trust boundaries, dominant overhead (written analysis in the report) | `educloud/config.py` holds the per-approach parameters |
| 3 | 6 | CPU, memory, network, storage, density model | `python scripts/task3_model.py` (`educloud/models.py`) |
| 4 | 4 | Best / typical / worst case (M/M/1 latency + steal + swapping + migration) | `python scripts/task4_conditions.py` |
| 5 | 3 | Threat model (written analysis in the report) | – |
| 6 | 3 | Isolation–performance optimisation (exhaustive search of `J = αCost + βD + γR`) | `python scripts/task6_tradeoff.py [--peak 3 --external 30]` |
| 7 | 4 | Mitigation benefit vs cost (SMT off, KPTI, dedicated pool, micro-segmentation, encrypted migration, image signing) | `python scripts/task7_mitigations.py` |
| 8 | 4 | Test harness: sysbench / fio / iperf3 / stress-ng on 1→16 instances, noisy neighbour, security checks | `scripts/task8_run_benchmarks.py`, `scripts/task8_security_validation.py` |
| 9 | 3 | Mean ± SD tables, Graph 1 (throughput vs instances), Graph 2 (p95 under interference) | `python scripts/task9_analyze_results.py --machine "<your specs>"` |
| 10 | 4 | Predicted vs measured, APE, fitted `h`, scaling efficiency | `python scripts/task10_compare_theory_experiment.py --cores <N>` |
| 11 | 4 | Recommendation (written; uses Task 3/6/7/9 outputs) | – |
| 12 | 8 | Day-4: impact, original vs modified design, pool sizing, SR-IOV, evidence graph | `python scripts/task12_day4_redesign.py` |

## Running the real experiments (Tasks 8–10)

Use a Linux machine (nested virtualization is acceptable if you document it). Reduce the instance
counts proportionally if the hardware is limited and **state that limitation in the report**.

```bash
# 0. tools + image
sudo apt install -y sysbench fio iperf3 stress-ng sysstat docker.io
make image                                   # builds educloud-bench:latest (same image for every runtime)

# 1. bare-metal baseline (required for degradation figures)
python scripts/task8_run_benchmarks.py --approach baremetal --instances 1 --reps 5

# 2. containers (runc) – scaling 1→16, then noisy neighbour
python scripts/task8_run_benchmarks.py --approach docker --instances 1 2 4 8 16 --reps 5 --iperf-server 172.17.0.1
python scripts/task8_run_benchmarks.py --approach docker --scenario interference --instances 4 --noise none cpu disk --reps 5

# 3. sandboxed runtimes (install gVisor "runsc" / Kata and register them with Docker first)
python scripts/task8_run_benchmarks.py --approach gvisor --instances 1 2 4 8 16 --reps 5
python scripts/task8_run_benchmarks.py --approach kata   --instances 1 2 4 8 16 --reps 5

# 4. full VMs: create N identical libvirt guests (1 vCPU, 2 GB, tools installed, SSH key) then
python scripts/task8_run_benchmarks.py --approach kvm --instances 1 2 4 8 16 --reps 5 \
       --kvm-domains vm1,vm2,... --kvm-ips 192.168.122.11,192.168.122.12,... --iperf-server 192.168.122.1

# 5. one mitigation with/without (record the label)
sudo scripts/task8_toggle_smt.sh off
python scripts/task8_run_benchmarks.py --approach kvm --instances 8 --mitigation smt_off --reps 5
sudo scripts/task8_toggle_smt.sh on

# 6. security validation (kernel sharing, namespaces, cgroups, SMT/KPTI status) -> results/security_validation.json
python scripts/task8_security_validation.py

# 7. tables, graphs, theory-vs-experiment
python scripts/task9_analyze_results.py --machine "Ryzen 5 5600H, 16 GB, Ubuntu 24.04, kernel 6.8"
python scripts/task10_compare_theory_experiment.py --cores $(nproc)
```

Every instance gets identical resources (1 vCPU, 2 GB) and the same workload commands
(`educloud/workloads.py`), 5 repetitions, mean ± SD reported. Add `--dry-run` to any benchmark
command to print what would run.

**Take screenshots** of the terminal runs, `lsns` / `uname -r` output and the generated graphs –
the assignment's evidence chain has a "Screenshots" row.

## Repository layout

```
educloud/                 library: config, models, tradeoff, mitigation, day4, parsers, workloads, backends, stats
scripts/                  one script per task (+ benchmark runner, security validation, SMT toggle, demo data)
tests/                    unit tests (python -m unittest discover -s tests)
docker/Dockerfile.bench   benchmark image shared by docker / gVisor / Kata
data/results/             YOUR measured results.csv (commit it – it is your evidence)
results/                  generated tables and figures (git-ignored; copy the ones you use into the report)
.github/workflows/ci.yml  runs the tests and the model scripts on every push
```

## Key formulas (see `educloud/models.py`)

* CPU: `effective per-vCPU = (1/r)(1−h)(1−s)`; `h_exit = E · 1.5 µs`; `steal = max(0, 1 − C/(N·u))`
* Density under SLA `D`: `N_cpu = ⌊C(1−h) / (u(1−D))⌋` (needs `h ≤ D`), `N_mem = ⌊M(1−reserve)/(m + overhead)⌋`
* Network/storage: `share = L(1−h_io)/N`, `N ≤ L(1−h_io) / (demand(1−D))`
* Host density: `N_host = min(N_cpu, N_mem, N_net, N_storage)`
* Latency: `S = S0/((1−h)(1−s))·swap`, `ρ = u·S/S0`, `mean = S/(1−ρ)`, `p95 = mean·ln 20`
* Trade-off: minimise `J = α·Cost + β·D + γ·R` s.t. `D ≤ 10 %`, memory + N+1 failover, SIS never on shared-kernel containers
