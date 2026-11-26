#!/usr/bin/env python3
"""A2.1 / B1.2 - HDFS capacity planning with every step shown."""
import math

TB = 1024 ** 4
MB = 1024 ** 2
DAILY_TB, DAYS, BLOCK_MB, REPL = 2, 90, 128, 3
DN_TB, HEADROOM, OBJ_BYTES = 24, 0.25, 150

daily_bytes = DAILY_TB * TB
blocks_day = math.ceil(daily_bytes / (BLOCK_MB * MB))
raw_day_tb = DAILY_TB * REPL
raw_90_tb = raw_day_tb * DAYS
usable_per_dn = DN_TB * (1 - HEADROOM)
dn = math.ceil(raw_90_tb / usable_per_dn)
blocks_90 = blocks_day * DAYS
nn_bytes = blocks_90 * OBJ_BYTES

print("A2.1 CAPACITY PLANNING")
print(f"1) blocks/day      = {DAILY_TB} TB / {BLOCK_MB} MB = {daily_bytes // MB:,} MB / {BLOCK_MB} = {blocks_day:,}")
print(f"2) raw storage/day = {DAILY_TB} TB x {REPL} = {raw_day_tb} TB ; 90 days = {raw_day_tb} x {DAYS} = {raw_90_tb} TB")
print(f"3) usable per DN   = {DN_TB} TB x (1-{HEADROOM}) = {usable_per_dn:.0f} TB ; DataNodes = {raw_90_tb}/{usable_per_dn:.0f} = {raw_90_tb/usable_per_dn:.1f} -> {dn}")
print(f"4) block objects 90d = {blocks_day:,} x {DAYS} = {blocks_90:,} ; NameNode heap = {blocks_90:,} x {OBJ_BYTES} B = {nn_bytes:,} B = {nn_bytes/MB:.1f} MiB")

print("\nTINY-FILE EFFECT (same 2 TB/day stored as 1 MB files)")
files_day = daily_bytes // MB
files_90 = files_day * DAYS
objs = files_90 * 2                      # one file object + one block object per tiny file
print(f"files/day = {files_day:,} ; 90 days = {files_90:,}")
print(f"objects   = {files_90:,} files + {files_90:,} blocks = {objs:,}")
print(f"NameNode heap = {objs:,} x {OBJ_BYTES} B = {objs*OBJ_BYTES/1024**3:.1f} GiB  "
      f"(vs {nn_bytes/MB:.1f} MiB with 128 MB blocks = {objs*OBJ_BYTES/nn_bytes:.0f}x more)")

print("\nB1.2 CROSS-CHECK: a 1 GB test log file")
gb = 1 * 1024 ** 3
print(f"blocks = ceil({gb // MB} MB / {BLOCK_MB} MB) = {math.ceil(gb/(BLOCK_MB*MB))} ; replicas stored = {math.ceil(gb/(BLOCK_MB*MB))*REPL}")
print("a 300 MB file -> blocks = ceil(300/128) = 3 (128 + 128 + 44 MB); last block only occupies 44 MB on disk")
