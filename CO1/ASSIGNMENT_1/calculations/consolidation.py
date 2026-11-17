"""Task 4 - Server consolidation calculation (12 physical servers -> virtualised hosts)."""
import json
import math

# ------------------------------------------------------------- assumptions -
LEGACY_SERVERS = 12      # given in the scenario
AVG_UTIL = 0.15          # given: average CPU utilisation per legacy server
PEAK_UTIL = 0.95         # given: peak utilisation (admissions / exams)
TARGET_UTIL = 0.70       # given: target host utilisation
HYP_OVERHEAD = 0.10      # assumption: hypervisor + management overhead = 10 %
SPARE_HOSTS = 1          # assumption: N+1 spare for HA / live migration
NEW_HOST_FACTOR = 3.0    # sensitivity only: a modern host = 3x one legacy server

print("=" * 70)
print(" TASK 4 - SERVER CONSOLIDATION CALCULATION")
print("=" * 70)
print(f" Legacy servers          : {LEGACY_SERVERS} (host capacity assumed equal to one legacy server)")
print(f" Average / peak CPU use  : {AVG_UTIL:.0%} / {PEAK_UTIL:.0%}")
print(f" Target host utilisation : {TARGET_UTIL:.0%}")
print(f" Hypervisor overhead     : {HYP_OVERHEAD:.0%}      Spare hosts (N+1): {SPARE_HOSTS}")

# A) basic calculation exactly as asked in the assignment
avg_load = LEGACY_SERVERS * AVG_UTIL
basic = avg_load / TARGET_UTIL
print("\n A) BASIC CALCULATION")
print(f"    Total useful work = 12 x 15%            = {avg_load:.2f} server-equivalents")
print(f"    Hosts needed      = 1.80 / 0.70         = {basic:.2f}  ->  {math.ceil(basic)} hosts")

# B) refined calculation with overhead and redundancy
avg_load_ov = avg_load * (1 + HYP_OVERHEAD)
hosts_ov = avg_load_ov / TARGET_UTIL
active = math.ceil(hosts_ov)
final_hosts = active + SPARE_HOSTS
util_active = avg_load_ov / active * 100
print("\n B) REFINED CALCULATION (overhead + redundancy)")
print(f"    Work incl. overhead = 1.80 x 1.10       = {avg_load_ov:.3f}")
print(f"    Hosts needed        = {avg_load_ov:.3f} / 0.70     = {hosts_ov:.2f}  ->  {active} active hosts")
print(f"    Add N+1 spare       = {active} + {SPARE_HOSTS}               = {final_hosts} hosts in total")
print(f"    Utilisation of the {active} active hosts = {avg_load_ov:.3f} / {active} = {util_active:.0f}%  (within the 70% target)")

# C) peak-load check
peak_load = LEGACY_SERVERS * PEAK_UTIL * (1 + HYP_OVERHEAD)
peak_hosts = math.ceil(peak_load / TARGET_UTIL)
burst = peak_hosts - active
print("\n C) PEAK-LOAD CHECK (admissions / result / exam weeks)")
print(f"    Peak work           = 12 x 95% x 1.10   = {peak_load:.2f}")
print(f"    Hosts needed        = {peak_load:.2f} / 0.70     = {peak_load / TARGET_UTIL:.2f}  ->  {peak_hosts} hosts")
print(f"    Burst capacity      = {peak_hosts} - {active}              = {burst} hosts, rented only for the peak weeks")

# D) sensitivity - newer, faster hosts
modern = math.ceil(hosts_ov / NEW_HOST_FACTOR)
print("\n D) SENSITIVITY: if each new host is 3x a legacy server")
print(f"    Hosts = {hosts_ov:.2f} / 3 = {hosts_ov / NEW_HOST_FACTOR:.2f} -> {modern} host(s) + {SPARE_HOSTS} spare = {modern + SPARE_HOSTS} (host utilisation stays ~{avg_load_ov / (modern * NEW_HOST_FACTOR) * 100:.0f}%)")

print("\n " + "-" * 66)
print(f" RESULT: 12 physical servers  ->  {final_hosts} virtualised hosts ({active} active + {SPARE_HOSTS} spare)")
print(f"         = {(1 - final_hosts / LEGACY_SERVERS) * 100:.0f}% fewer machines; utilisation 15% -> {util_active:.0f}%")
print(f"         Peak weeks need {burst} extra hosts -> use cloud elasticity, not owned hardware.")

json.dump({"avg_load": avg_load, "basic_hosts": math.ceil(basic), "basic_raw": round(basic, 2),
           "avg_load_ov": round(avg_load_ov, 3), "hosts_ov_raw": round(hosts_ov, 2), "active": active,
           "final_hosts": final_hosts, "util_active": round(util_active, 1),
           "peak_load": round(peak_load, 2), "peak_raw": round(peak_load / TARGET_UTIL, 2),
           "peak_hosts": peak_hosts, "burst": burst, "modern_hosts": modern},
          open("results_consolidation.json", "w"), indent=2)
