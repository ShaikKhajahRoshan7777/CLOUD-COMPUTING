#!/usr/bin/env bash
# Runs every task in order and rebuilds screenshots (about 25 minutes on one core). Needs Java 17+ for Spark.
set -e
for t in 1 2 3 4 5 6; do
  echo "=== Task $t ==="
  python run_task$t.py | tee results/task${t}_console.txt
done
python make_screenshots.py
