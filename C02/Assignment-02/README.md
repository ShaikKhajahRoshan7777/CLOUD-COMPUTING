# EduCloud CO2 - Virtualization Architecture Analysis (Cloud Computing & Big Data Analytics, CSA15)

Analyse, evaluate and validate virtualization architectures (KVM VM, Docker container, gVisor sandbox) for a
multi-tenant university private cloud, including the Day-4 design challenge (external Spark/Hadoop tenants).

## Folder map
| Path | Content |
|------|---------|
| `docs/EduCloud_CO2_Assignment.docx` | Final report (evaluation form + Tasks 1-12) |
| `src/model.py` | Analytical CPU / memory / I/O / density / security model (Tasks 2-7) |
| `src/simulate.py` | Emulated test-bed: 1-2-4-8-16 instances, noisy neighbour, mitigations (Tasks 8-10) |
| `src/real_bench.py` | REAL CPU / memory / disk / network micro-benchmarks on your own machine |
| `src/security_check.py` | Security-property validation (namespaces, cgroups, seccomp, CPU mitigations) |
| `src/tradeoff.py`, `src/design.py` | Task 6/7 optimisation and Task 12 redesign |
| `src/build_report.py` | Builds the Word report (form kept untouched + Tasks 1-12) from the result files |
| `src/make_figures.py`, `src/make_screenshots.py` | Diagrams, graphs and VS Code-style screenshots |
| `configs/`, `scripts/` | Docker, gVisor, libvirt configs and the real-hardware test scripts |
| `results/`, `figures/`, `screenshots/` | Generated data, images and logs |

## Run (VS Code terminal)
```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/run_all.py                                   # reproduces every result
```
Take your own screenshots in VS Code after `python src/model.py`, `python src/simulate.py`, `python src/real_bench.py`
and `python src/security_check.py`; replace the files in `screenshots/` if you want them from your own machine.

## Honest scope note
`simulate.py` is a time-stepped **emulation** (bursty vCPU demand, fair-share scheduler, Poisson VM exits/syscalls and
effects the analytical model ignores). `real_bench.py` produces **real** measurements of process co-location on the
machine that runs it. Hypervisor-level numbers on real KVM / Docker / gVisor are obtained with `scripts/run_real_tests.sh`
on a Linux host and can be substituted for the emulated tables.
