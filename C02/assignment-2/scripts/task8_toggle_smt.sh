#!/usr/bin/env bash
# Enable/disable SMT (hyper-threading) on the Linux host, for the "with / without mitigation" experiment.
# Usage: sudo scripts/task8_toggle_smt.sh off | on | status
set -euo pipefail
CTL=/sys/devices/system/cpu/smt/control
case "${1:-status}" in
  off) echo off > "$CTL" ;;
  on)  echo on  > "$CTL" ;;
  status) ;;
  *) echo "usage: $0 on|off|status"; exit 1 ;;
esac
echo "SMT control: $(cat $CTL)   active: $(cat /sys/devices/system/cpu/smt/active)"
