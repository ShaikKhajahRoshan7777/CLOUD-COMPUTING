#!/usr/bin/env python3
"""B4.2 - discrete-event simulation: FIFO vs Capacity (batch 70 / adhoc 30).

This is a MODEL of the schedulers' behaviour (no preemption, task-level container grants),
used to compare queueing outcomes; real YARN timings must be captured on a cluster.
Cluster: 10 containers.  Batch job: 120 tasks x 5 min, submitted t=0.
Ad-hoc jobs: 3 jobs x 4 tasks x 1 min, submitted at t=10, 30, 50 min.
"""
import json, os, heapq

CONTAINERS = 10
BATCH = dict(name="batch-nightly", queue="batch", submit=0, tasks=120, dur=5)
ADHOC = [dict(name=f"adhoc-{i+1}", queue="adhoc", submit=t, tasks=4, dur=1) for i, t in enumerate((10, 30, 50))]


def simulate(policy):
    jobs = [dict(j, pending=j["tasks"], running=0, done=0, finish=None, first=None) for j in [BATCH] + ADHOC]
    share = {"batch": 7, "adhoc": 3}
    t, free, events = 0.0, CONTAINERS, []   # events: (finish_time, job_index)
    timeline = []
    while True:
        # grant containers
        while free > 0:
            elig = [j for j in jobs if j["submit"] <= t and j["pending"] > 0]
            if not elig:
                break
            if policy == "fifo":
                pick = min(elig, key=lambda j: j["submit"])
            else:  # capacity: queue furthest below its guarantee first
                used = {q: sum(j["running"] for j in jobs if j["queue"] == q) for q in share}
                pick = min(elig, key=lambda j: (used[j["queue"]] - share[j["queue"]], j["submit"]))
                if used[pick["queue"]] >= share[pick["queue"]]:          # over guarantee -> elastic use of idle capacity
                    pass
            pick["pending"] -= 1; pick["running"] += 1; free -= 1
            if pick["first"] is None: pick["first"] = t
            heapq.heappush(events, (t + pick["dur"], jobs.index(pick)))
            timeline.append((pick["name"], t, t + pick["dur"]))
        arrivals = [j["submit"] for j in jobs if j["submit"] > t]
        nxt = []
        if events: nxt.append(events[0][0])
        if arrivals: nxt.append(min(arrivals))
        if not nxt: break
        t = min(nxt)
        while events and events[0][0] <= t + 1e-9:
            ft, ji = heapq.heappop(events)
            jobs[ji]["running"] -= 1; jobs[ji]["done"] += 1; free += 1
            if jobs[ji]["done"] == jobs[ji]["tasks"]: jobs[ji]["finish"] = ft
    return jobs, timeline


if __name__ == "__main__":
    out = {}
    for pol in ("fifo", "capacity"):
        jobs, tl = simulate(pol)
        out[pol] = {"jobs": [{k: j[k] for k in ("name", "submit", "first", "finish")} for j in jobs], "timeline": tl}
        print(f"\n{pol.upper()} scheduler")
        print("%-15s %8s %11s %10s %12s" % ("job", "submit", "first start", "finish", "turnaround"))
        for j in jobs:
            print("%-15s %8.1f %11.1f %10.1f %12.1f" % (j["name"], j["submit"], j["first"], j["finish"], j["finish"] - j["submit"]))
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "results", "scheduler.json"), "w"))
