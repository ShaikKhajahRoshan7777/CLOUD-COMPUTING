"""Task 4 - Server consolidation calculation (12 servers, 15% avg, 70% target)."""
import math


def hosts_needed(servers=12, avg_util=0.15, target_util=0.70):
    demand = servers * avg_util            # server-equivalents of average load
    exact = demand / target_util           # hosts at target utilisation
    return demand, exact, math.ceil(exact)


if __name__ == "__main__":
    demand, exact, hosts = hosts_needed()
    print("TASK 4 - SERVER CONSOLIDATION")
    print(f"Step 1: total average demand = 12 x 0.15 = {demand:.2f} server-equivalents")
    print("Step 2: usable capacity per new host = 1 x 0.70 = 0.70")
    print(f"Step 3: hosts = {demand:.2f} / 0.70 = {exact:.4f} -> round up = {hosts}")
    print(f"N+1 resilient design: {hosts + 1} hosts (survives one host failure)")
    print("Note: average-load only; validate peak CPU, memory, IOPS and network.")
