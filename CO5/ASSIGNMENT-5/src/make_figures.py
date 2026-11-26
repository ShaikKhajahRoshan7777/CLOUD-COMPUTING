#!/usr/bin/env python3
"""Generate all report figures into ../figures (matplotlib)."""
import os, json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = os.path.join(ROOT, "figures")
RES = os.path.join(ROOT, "results")
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "Times New Roman", "DejaVu Serif"], "font.size": 10})
NAVY, TEAL, ORANGE, GREY, RED, GREEN = "#1F3A5F", "#2A9D8F", "#E76F51", "#8D99AE", "#C0392B", "#2E8B57"


def box(ax, x, y, w, h, text, fc, tc="white", fs=9, bold=True):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec="none"))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal")


def arrow(ax, x1, y1, x2, y2, c=NAVY):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=c, lw=1.4))


def ecosystem():
    fig, ax = plt.subplots(figsize=(8.2, 4.1)); ax.set_xlim(0, 16); ax.set_ylim(0, 8); ax.axis("off")
    ax.text(8, 7.6, "Transit analytics pipeline mapped to the Hadoop ecosystem", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    box(ax, 0.2, 5.6, 2.8, 1.2, "Fare table\n(MySQL)", GREY)
    box(ax, 0.2, 3.3, 2.8, 1.2, "Gate logs\n(120 stations)", GREY)
    box(ax, 4.2, 5.6, 2.4, 1.2, "Sqoop", ORANGE)
    box(ax, 4.2, 3.3, 2.4, 1.2, "Flume /\nKafka", ORANGE)
    box(ax, 7.6, 3.9, 3.4, 2.2, "HDFS (core)\nNameNode +\nDataNodes", NAVY, fs=8.5)
    box(ax, 12.0, 5.6, 3.6, 1.2, "MapReduce on YARN\n(core)", TEAL)
    box(ax, 12.0, 3.3, 3.6, 1.2, "Oozie workflow\n(nightly schedule)", ORANGE)
    box(ax, 7.8, 0.9, 3.0, 1.2, "ZooKeeper\n(NameNode HA)", ORANGE)
    box(ax, 12.0, 0.9, 3.6, 1.2, "Hive / Parquet\n(reports)", ORANGE)
    for a in [(3.0, 6.2, 4.2, 6.2), (3.0, 3.9, 4.2, 3.9), (6.6, 6.2, 7.8, 5.5), (6.6, 3.9, 7.8, 4.6), (10.8, 5.4, 12.0, 6.0), (13.8, 5.6, 13.8, 4.5), (13.8, 3.3, 13.8, 2.1), (9.3, 2.1, 9.3, 3.9)]:
        arrow(ax, *a)
    ax.text(0.2, 0.3, "Navy/teal = core Hadoop (HDFS, YARN, MapReduce)    Orange = wider ecosystem    Grey = external sources", fontsize=8.5, color="#333")
    fig.savefig(os.path.join(FIG, "A1_ecosystem.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def replicas():
    fig, ax = plt.subplots(figsize=(8.2, 4.2)); ax.set_xlim(0, 16); ax.set_ylim(0, 8.4); ax.axis("off")
    ax.text(8, 8.0, "Rack-aware replica placement (replication factor 3) and write pipeline", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    for x, name in ((0.3, "Rack 1"), (5.7, "Rack 2"), (11.1, "Rack 3")):
        ax.add_patch(Rectangle((x, 1.0), 4.6, 5.2, fc="#F1F5F9", ec=GREY, lw=1.2, ls="--"))
        ax.text(x + 2.3, 5.8, name, ha="center", fontweight="bold", color=NAVY)
    box(ax, 0.8, 3.7, 3.6, 1.2, "DataNode 1\nReplica 1 (client's node)", GREEN, fs=8.5)
    box(ax, 0.8, 1.5, 3.6, 1.2, "DataNode 2", GREY, fs=8.5)
    box(ax, 6.2, 3.7, 3.6, 1.2, "DataNode 3\nReplica 2 (remote rack)", ORANGE, fs=8.5)
    box(ax, 6.2, 1.5, 3.6, 1.2, "DataNode 4\nReplica 3 (same rack as R2)", ORANGE, fs=8.5)
    box(ax, 11.6, 3.7, 3.6, 1.2, "DataNode 5", GREY, fs=8.5)
    box(ax, 11.6, 1.5, 3.6, 1.2, "DataNode 6", GREY, fs=8.5)
    arrow(ax, 4.4, 4.3, 6.2, 4.3, RED); arrow(ax, 8.0, 3.7, 8.0, 2.7, RED)
    ax.text(5.3, 4.55, "pipeline 1", color=RED, fontsize=8, ha="center"); ax.text(8.9, 3.2, "pipeline 2", color=RED, fontsize=8)
    ax.text(8, 0.35, "1 off-rack hop only: survives a whole-rack failure while cutting cross-rack write traffic to one transfer.", ha="center", fontsize=8.5, color="#333")
    fig.savefig(os.path.join(FIG, "A2_replica_placement.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def sequence():
    fig, ax = plt.subplots(figsize=(8.2, 6.6)); ax.set_xlim(0, 16); ax.set_ylim(-1, 22); ax.axis("off")
    ax.text(8, 21.4, "Life of the Q1 job on YARN (sequence diagram)", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    names = ["Client", "Resource\nManager", "Node\nManager", "App\nMaster", "Map\ncontainers", "Reduce\ncontainers", "HDFS"]
    xs = [1.2, 3.6, 6.0, 8.4, 10.8, 13.0, 15.0]
    for x, n in zip(xs, names):
        box(ax, x - 0.95, 19.3, 1.9, 1.3, n, NAVY, fs=7.5)
        ax.plot([x, x], [0.3, 19.3], color=GREY, lw=0.9, ls="--")
    steps = [(0, 1, "1 submit job / getApplicationId"), (0, 6, "2 copy job jar, config, split info"), (1, 2, "3 start AM container"),
             (2, 3, "4 launch ApplicationMaster"), (3, 1, "5 register + request containers (data-local)"),
             (1, 4, "6 allocate map containers"), (4, 6, "7 read input split (local block)"),
             (4, 4, "8 map -> combine -> spill (local disk)"), (4, 3, "9 progress / heartbeat"),
             (3, 5, "10 launch reducers after maps finish"), (5, 4, "11 shuffle: fetch map outputs"),
             (5, 5, "12 merge-sort + reduce"), (5, 6, "13 write part-r-xxxxx (OutputCommitter)"),
             (3, 0, "14 job complete, status SUCCEEDED"), (3, 1, "15 unregister AM, release containers")]
    y = 18.2
    for a, b, t in steps:
        if a == b:
            ax.annotate("", xy=(xs[a] + 0.5, y - 0.35), xytext=(xs[a], y), arrowprops=dict(arrowstyle="-|>", color=TEAL, lw=1.2, connectionstyle="arc3,rad=-1.2"))
            ax.text(xs[a] + (0.95 if xs[a] < 12 else -0.5), y - 0.25, t, fontsize=7.6, va="center", ha=("left" if xs[a] < 12 else "right"), color="#111", bbox=dict(fc="white", ec="none", pad=0.6))
        else:
            arrow(ax, xs[a], y, xs[b], y, RED if a > b else NAVY)
            ax.text((xs[a] + xs[b]) / 2, y + 0.18, t, fontsize=7.6, ha="center", va="bottom", color="#111", bbox=dict(fc="white", ec="none", pad=0.4))
        y -= 1.22
    fig.savefig(os.path.join(FIG, "A4_sequence_diagram.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def scaling():
    d = json.load(open(os.path.join(RES, "scaling.json")))
    fig, axs = plt.subplots(1, 2, figsize=(8.2, 3.5))
    for r, c, m in ((1, NAVY, "o"), (2, TEAL, "s"), (4, ORANGE, "^")):
        pts = [x for x in d if x["reducers"] == r]
        axs[0].plot([p["size_mb"] for p in pts], [p["time"] for p in pts], marker=m, color=c, label=f"{r} reducer(s)")
    axs[0].set_xlabel("Input size (MB)"); axs[0].set_ylabel("Elapsed time (s)"); axs[0].set_title("Time vs input size", fontweight="bold", color=NAVY); axs[0].grid(alpha=.3); axs[0].legend()
    pts = [x for x in d if x["reducers"] == 1]
    axs[1].bar([str(p["size_mb"]) for p in pts], [p["maps"] for p in pts], color=TEAL)
    for i, p in enumerate(pts): axs[1].text(i, p["maps"] + .1, str(p["maps"]), ha="center")
    axs[1].set_xlabel("Input size (MB)"); axs[1].set_ylabel("Map tasks (= splits)"); axs[1].set_title("Map tasks = ceil(size / 16 MB)", fontweight="bold", color=NAVY)
    fig.suptitle("Scaling behaviour of the Q1 job (local emulation)", fontweight="bold", y=1.03)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "B3_scaling.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def skew():
    d = json.load(open(os.path.join(RES, "skew.json")))
    keys = list(d.keys()); fig, axs = plt.subplots(1, len(keys), figsize=(8.2, 3.0), sharey=True)
    for ax, k in zip(axs, keys):
        v = [x["input_records"] for x in d[k]]; tot = sum(v)
        ax.bar(["R0", "R1", "R2", "R3"], [100 * a / tot for a in v], color=[RED if a == max(v) and max(v) / tot > .4 else TEAL for a in v])
        ax.set_title(k.replace(" / ", "\n"), fontsize=8.5, fontweight="bold", color=NAVY); ax.axhline(25, color=GREY, ls="--", lw=1)
    axs[0].set_ylabel("% of reduce input records")
    fig.suptitle("Reducer load: uniform vs skewed input (4 reducers; dashed = ideal 25%)", fontweight="bold", y=1.04)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "B3_skew.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def combiner():
    d = json.load(open(os.path.join(RES, "combiner.json")))
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    labels = ["Map output\nrecords", "Reduce input\nrecords", "Shuffle bytes\n(/10)"]
    wo = [d["without"]["Map output records"], d["without"]["Reduce input records"], d["without"]["Reduce shuffle bytes"] / 10]
    wi = [d["with"]["Map output records"], d["with"]["Reduce input records"], d["with"]["Reduce shuffle bytes"] / 10]
    x = range(3)
    ax.bar([i - .19 for i in x], wo, .38, color=ORANGE, label="Without combiner"); ax.bar([i + .19 for i in x], wi, .38, color=TEAL, label="With combiner")
    ax.set_xticks(list(x)); ax.set_xticklabels(labels); ax.legend(); ax.grid(axis="y", alpha=.3)
    ax.set_title(f"Combiner cuts shuffle volume by {d['reduction_pct']:.1f}%", fontweight="bold", color=NAVY)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "B2_combiner.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


def gantt():
    d = json.load(open(os.path.join(RES, "scheduler.json")))
    fig, axs = plt.subplots(2, 1, figsize=(8.2, 3.6), sharex=True)
    for ax, pol, title in zip(axs, ("fifo", "capacity"), ("FIFO (single queue)", "Capacity scheduler (batch 70% / adhoc 30%)")):
        jobs = d[pol]["jobs"]
        for i, j in enumerate(jobs):
            c = NAVY if j["name"].startswith("batch") else ORANGE
            ax.barh(i, j["finish"] - j["submit"], left=j["submit"], color=c, alpha=.35, height=.55)
            ax.barh(i, j["finish"] - j["first"], left=j["first"], color=c, height=.55)
            ax.text(j["finish"] + 0.8, i, f"{j['finish']-j['submit']:.0f} min", va="center", fontsize=8.5)
        ax.set_yticks(range(len(jobs))); ax.set_yticklabels([j["name"] for j in jobs], fontsize=8.5); ax.invert_yaxis(); ax.set_title(title, fontweight="bold", color=NAVY, fontsize=10); ax.grid(axis="x", alpha=.3)
    axs[1].set_xlabel("Time (minutes)  -  light bar = waiting, dark bar = running")
    fig.suptitle("Turnaround of batch and ad-hoc jobs (scheduler model)", fontweight="bold", y=1.02)
    fig.tight_layout(); fig.savefig(os.path.join(FIG, "B4_scheduler.png"), dpi=200, bbox_inches="tight"); plt.close(fig)


if __name__ == "__main__":
    for f in (ecosystem, replicas, sequence, scaling, skew, combiner, gantt):
        f()
    print("figures written to", FIG)
