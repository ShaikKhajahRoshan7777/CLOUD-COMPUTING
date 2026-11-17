#!/usr/bin/env bash
echo "== SMT =="; cat /sys/devices/system/cpu/smt/active
echo "== Vulnerability mitigations =="; grep . /sys/devices/system/cpu/vulnerabilities/*
echo "== Kernel flags =="; cat /proc/cmdline
