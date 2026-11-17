#!/usr/bin/env bash
# Workloads executed INSIDE each VM / container (identical for all approaches)
set -e
echo "cpu:    $(sysbench cpu --threads=4 --time=30 run | awk '/events per second/ {print $4}')"
echo "memory: $(sysbench memory --threads=4 --memory-block-size=1M --memory-total-size=50G run | awk '/MiB transferred/ {print $0}')"
fio --name=randread --rw=randread --bs=4k --iodepth=8 --size=1G --runtime=30 --time_based --direct=1 --output-format=terse | awk -F';' '{print "disk IOPS: "$8" | p95 clat(us): "$41}'
[ -n "$IPERF_SERVER" ] && iperf3 -c "$IPERF_SERVER" -t 30 -P 4 | tail -3
