"""Task 11 - Day-4 design challenge: capacity, availability and cost evidence (Rs. lakh where stated)."""
import json
import math

print("=" * 74)
print(" TASK 11 - DAY-4 CAPACITY, AVAILABILITY AND COST EVIDENCE")
print("=" * 74)

# ---------------------------------------------------------------- 1. capacity
USERS = 25000 + 2000          # given students + staff
COLLEGE_STUDENTS = 40 * 3000  # assumption: 40 colleges x 3,000 students
CONCURRENCY = 0.10            # assumption: 10% of users active at the same moment in a peak
REQ_PER_USER_S = 0.2          # assumption: one request per user every 5 seconds
RPS_PER_INSTANCE = 120        # assumption: measured capacity of one API container
TARGET_UTIL = 0.70
LOAD_FACTOR = 10              # given: 10x current peak

base_peak_rps = USERS * CONCURRENCY * REQ_PER_USER_S
new_peak_rps = base_peak_rps * LOAD_FACTOR
inst_peak = math.ceil(new_peak_rps / (RPS_PER_INSTANCE * TARGET_UTIL))
zones = 3
# capacity with one zone down: remaining (zones-1) zones must carry all load
per_zone_needed = math.ceil(inst_peak / (zones - 1))
inst_with_az_loss = per_zone_needed * zones
inst_base = math.ceil(base_peak_rps * 0.25 / (RPS_PER_INSTANCE * TARGET_UTIL))  # off-peak = 25% of today's peak

print("\n 1) CAPACITY (10x load)")
print(f"    Current peak   = {USERS:,} users x {CONCURRENCY:.0%} x {REQ_PER_USER_S} req/s      = {base_peak_rps:,.0f} req/s")
print(f"    10x peak       = {base_peak_rps:,.0f} x {LOAD_FACTOR}                         = {new_peak_rps:,.0f} req/s")
print(f"    Instances      = {new_peak_rps:,.0f} / ({RPS_PER_INSTANCE} x {TARGET_UTIL})          = {inst_peak} API containers at peak")
print(f"    With 1 zone lost: {per_zone_needed} per zone x {zones} zones          = {inst_with_az_loss} containers provisioned at peak")
print(f"    Off-peak floor = {inst_base} containers  -> autoscale between {inst_base} and {inst_with_az_loss}")

# ------------------------------------------------------------ 2. availability
HOURS = 8760
target = 0.999
allowed_h = HOURS * (1 - target)
print("\n 2) AVAILABILITY (target 99.9%)")
print(f"    Allowed downtime = 8760 h x (1 - 0.999) = {allowed_h:.2f} h/year = {allowed_h * 60 / 12:.1f} min/month")

def series(*a):
    p = 1.0
    for x in a:
        p *= x
    return p

def parallel(a, n):
    return 1 - (1 - a) ** n

# Assumed component SLAs (typical published figures for managed cloud services)
LB, GATEWAY, DB_MULTI_AZ, INSTANCE = 0.9999, 0.9995, 0.9995, 0.995
EVENTS, BASE_REGIONAL_OUTAGE_H = 12, 2.0   # 12 peak events/yr; a regional outage lasts about 2 h
SAT_ORIG_MIN, SAT_REV_MIN = 30, 3          # saturation minutes per event: VM scale-out vs container autoscale
FAILOVER_COVER, RTO_MIN = 0.95, 10         # automated failover success probability; recovery time (minutes)

a_orig = series(LB, parallel(INSTANCE, 2), DB_MULTI_AZ)
sat_orig = EVENTS * SAT_ORIG_MIN / 60
down_orig = HOURS * (1 - a_orig) + sat_orig
a_rev1 = series(LB, GATEWAY, parallel(INSTANCE, 3), DB_MULTI_AZ)
sat_rev = EVENTS * SAT_REV_MIN / 60
down_rev1 = HOURS * (1 - a_rev1) + sat_rev
u_region = 1 - a_rev1
a_rev2_core = 1 - u_region * (1 - FAILOVER_COVER * a_rev1)
n_outages = u_region * HOURS / BASE_REGIONAL_OUTAGE_H
down_rev2 = HOURS * (1 - a_rev2_core) + n_outages * RTO_MIN / 60 + sat_rev

rows = [("Original: 1 region, 2 zones, VM scale-out", a_orig, down_orig),
        ("Revised-A: 1 region, 3 zones + gateway", a_rev1, down_rev1),
        ("Revised-B: A + warm-standby 2nd region", a_rev2_core, down_rev2)]
print(f"    {'Design':<42}{'Component A':>12}{'Downtime h/yr*':>16}{'Effective A':>13}  Verdict")
for label, a, d in rows:
    eff = 1 - d / HOURS
    print(f"    {label:<42}{a * 100:>11.3f}%{d:>16.2f}{eff * 100:>12.3f}%  {'PASS' if eff >= target else 'FAIL'}")
print("    * includes saturation downtime during peak events (12/yr: 30 min for VM scale-out, 3 min for container autoscale)")
print("    Series: A = A1 x A2 x ...   Parallel: 1-(1-A)^n   Two regions: U = U_r x (1 - 0.95 x A_r)")

# -------------------------------------------------------------------- 3. cost
COMPUTE_1X = 14.0            # Rs lakh/yr to hold today's peak capacity statically (reserved pricing)
RESERVED_DISCOUNT = 0.6      # reserved price = 60% of on-demand price
BASE_SHARE, BURST_TIME = 0.30, 0.15   # 30% always-on reserved; burst capacity runs 15% of the year
static_10x = COMPUTE_1X * LOAD_FACTOR
autoscaled = static_10x * (BASE_SHARE + (1 - BASE_SHARE) * BURST_TIME / RESERVED_DISCOUNT)
other_orig = {"SaaS licences": 14.0, "Storage + backup": 3.0, "Network": 2.0, "DR": 4.0, "Admin staff": 9.0, "Managed DB": 5.0}
other_rev = {"SaaS licences": 14.0, "Storage + backup": 8.0, "Network + CDN": 6.0, "Multi-region DR": 8.0,
             "API gateway + WAF": 6.0, "Monitoring + security": 5.0, "Admin staff": 12.0, "Managed DB (multi-AZ + replicas)": 12.0}
orig_year = static_10x + sum(other_orig.values())
rev_year = autoscaled + sum(other_rev.values())
chargeback = 40 * 1.0   # assumption: Rs 1 lakh/yr per affiliated college for API access
print("\n 3) COST UNDER 10x LOAD (Rs. lakh per year)")
print(f"    Original design scaled statically : compute {static_10x:6.1f} + other {sum(other_orig.values()):5.1f} = {orig_year:6.1f}")
print(f"    Revised design with autoscaling   : compute {autoscaled:6.1f} + other {sum(other_rev.values()):5.1f} = {rev_year:6.1f}")
print(f"    Saving from redesign              : {orig_year - rev_year:6.1f} lakh/yr ({(orig_year - rev_year) / orig_year * 100:.0f}%)")
print(f"    Chargeback from 40 colleges @ Rs 1 lakh = {chargeback:.1f} lakh/yr -> net revised cost {rev_year - chargeback:.1f} lakh/yr")
print(f"    3-year revised cost (incl. 8.0 one-time migration, net of chargeback) = {8.0 + 3 * (rev_year - chargeback):.1f} lakh")

json.dump({"base_peak_rps": base_peak_rps, "new_peak_rps": new_peak_rps, "inst_peak": inst_peak,
           "per_zone": per_zone_needed, "inst_az_loss": inst_with_az_loss, "inst_base": inst_base,
           "allowed_h": round(allowed_h, 2), "a_orig": round(a_orig * 100, 3), "down_orig": round(down_orig, 1),
           "eff_orig": round((1 - down_orig / HOURS) * 100, 3), "a_rev1": round(a_rev1 * 100, 3),
           "down_rev1": round(down_rev1, 1), "eff_rev1": round((1 - down_rev1 / HOURS) * 100, 3),
           "a_rev2": round(a_rev2_core * 100, 4), "down_rev2": round(down_rev2, 2),
           "eff_rev2": round((1 - down_rev2 / HOURS) * 100, 3), "static_10x": static_10x,
           "autoscaled": round(autoscaled, 1), "orig_year": round(orig_year, 1), "rev_year": round(rev_year, 1),
           "other_orig": sum(other_orig.values()), "other_rev": sum(other_rev.values()),
           "chargeback": chargeback, "net_rev": round(rev_year - chargeback, 1),
           "three_year_rev": round(8.0 + 3 * (rev_year - chargeback), 1)},
          open("results_dayfour.json", "w"), indent=2)
