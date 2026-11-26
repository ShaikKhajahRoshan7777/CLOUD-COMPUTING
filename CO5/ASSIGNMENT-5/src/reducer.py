#!/usr/bin/env python3
"""Hadoop Streaming reducer for Q1. Also used as the combiner (-combiner reducer.py)."""
import sys
from transit_mr import sum_reduce

if __name__ == "__main__":
    for out in sum_reduce(sys.stdin):
        sys.stdout.write(out + "\n")
