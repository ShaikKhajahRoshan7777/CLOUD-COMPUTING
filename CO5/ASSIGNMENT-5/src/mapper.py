#!/usr/bin/env python3
"""Hadoop Streaming mapper for Q1 (tap-ins per station per hour). Reads stdin, writes stdout."""
import sys
from transit_mr import q1_map


def counter(group, name, v=1):                 # Hadoop Streaming counter protocol (stderr)
    sys.stderr.write(f"reporter:counter:{group},{name},{v}\n")


if __name__ == "__main__":
    for out in q1_map(sys.stdin, counter):
        sys.stdout.write(out + "\n")
