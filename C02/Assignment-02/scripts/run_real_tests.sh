#!/usr/bin/env bash
# Real-hardware version of Tasks 8-9 (run on a Linux host with KVM, Docker and gVisor installed).
# Usage: sudo bash scripts/run_real_tests.sh      -> results/real_<approach>_<n>.txt
set -e
mkdir -p results/real
for N in 1 2 4 8 16; do
  for REP in 1 2 3 4 5 6 7 8 9 10; do
    # B: Docker/runc
    docker compose -f configs/docker-compose.yml up -d --scale bench_runc=$N bench_runc
    docker compose -f configs/docker-compose.yml logs bench_runc > results/real/docker_${N}_${REP}.txt
    docker compose -f configs/docker-compose.yml down
    # C: gVisor/runsc
    docker compose -f configs/docker-compose.yml up -d --scale bench_runsc=$N bench_runsc
    docker compose -f configs/docker-compose.yml logs bench_runsc > results/real/gvisor_${N}_${REP}.txt
    docker compose -f configs/docker-compose.yml down
    # A: KVM  (clone N guests from the golden qcow2, start, run bench_inside.sh over ssh)
    for i in $(seq 1 $N); do virt-clone --original educloud-bench-01 --name vm$i --auto-clone >/dev/null; virsh start vm$i; done
    sleep 20; for i in $(seq 1 $N); do ssh vm$i 'bash -s' < scripts/bench_inside.sh > results/real/kvm_${N}_${REP}_vm$i.txt & done; wait
    for i in $(seq 1 $N); do virsh destroy vm$i; virsh undefine vm$i --remove-all-storage; done
  done
done
# Noisy neighbour: add one instance running  stress-ng --cpu 4 --io 4 --vm 2 --vm-bytes 2G  and repeat the n=16 run.
# Mitigation: repeat n=8 with  `echo off > /sys/devices/system/cpu/smt/control`  (SMT off) and with  mitigations=auto / mitigations=off boot flags.
