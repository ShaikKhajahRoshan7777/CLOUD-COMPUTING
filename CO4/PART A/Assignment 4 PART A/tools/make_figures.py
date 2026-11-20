"""Creates the diagrams used in the Word document (matplotlib only)."""
import os
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
plt.rcParams["font.family"] = ["Liberation Serif", "Times New Roman", "DejaVu Serif"]
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); OUT = f"{ROOT}/figures"; os.makedirs(OUT, exist_ok=True)
NAVY, TEAL, ORANGE, RED, GREY, GREEN, GOLD = "#1F3864", "#1B7F8C", "#E07B39", "#C0392B", "#EEF2F7", "#2E8B57", "#B8860B"

def box(ax, x, y, w, h, text, fc, tc="white", fs=9.5, bold=True, ec=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec=ec or fc, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", color=tc, fontsize=fs, fontweight="bold" if bold else "normal", wrap=True)

def arrow(ax, x1, y1, x2, y2, c="#444", style="-|>", lw=1.6):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style, mutation_scale=14, color=c, lw=lw))

def fig1():
    fig, ax = plt.subplots(figsize=(10, 4.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 4.4); ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.1, 0.35), 5.55, 3.1, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#FDECEA", ec=RED, lw=1.5, ls="--"))
    ax.add_patch(FancyBboxPatch((5.75, 0.35), 4.15, 3.1, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#E8F5EE", ec=GREEN, lw=1.5, ls="--"))
    ax.text(2.9, 3.62, "IDENTIFIED ZONE  (identifiers present, restricted)", ha="center", color=RED, fontsize=10, fontweight="bold")
    ax.text(7.8, 3.62, "DE-IDENTIFIED ZONE  (no identifiers)", ha="center", color=GREEN, fontsize=10, fontweight="bold")
    st = [("1  Secure\nIntake", NAVY), ("2  Validate &\nQuarantine", NAVY), ("3  De-identify\n& Separate", ORANGE), ("4  Analyse\nTrends", TEAL), ("5  Controlled\nSharing", TEAL)]
    xs = [0.3, 2.15, 3.95, 5.95, 8.0]
    for (t, c), x in zip(st, xs): box(ax, x, 1.55, 1.55, 1.2, t, c, fs=10)
    for a, b in zip(xs[:-1], xs[1:]): arrow(ax, a + 1.55, 2.15, b, 2.15)
    box(ax, 0.3, 0.5, 9.4, 0.65, "6  AUDIT, FAILURE & REPLAY  -  append-only audit store, retry x3, replay from Raw zone", GOLD, fs=10)
    for x in xs: arrow(ax, x + 0.77, 1.55, x + 0.77, 1.15, c=GOLD, lw=1.1)
    ax.text(5, 4.2, "Figure: Repaired HospitalAnalytics pipeline - six stages and two protection zones", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    fig.savefig(f"{OUT}/fig_task1_pipeline.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def fig2():
    fig, ax = plt.subplots(figsize=(10, 3.9)); ax.set_xlim(-2, 102); ax.set_ylim(-0.3, 4.2); ax.axis("off")
    X = lambda sec: sec * 50 / 60.0          # 60 s -> 50 units
    ax.add_patch(FancyBboxPatch((0, 1.2), 50, 1.5, boxstyle="round,pad=0.02", fc="#DCE9F7", ec=NAVY))
    ax.add_patch(FancyBboxPatch((50, 1.2), 50, 1.5, boxstyle="round,pad=0.02", fc="#E3F4EA", ec=GREEN))
    ax.text(25, 3.0, "Window 08:00:00 - 08:01:00", ha="center", fontsize=10.5, fontweight="bold", color=NAVY)
    ax.text(75, 3.0, "Window 08:01:00 - 08:02:00", ha="center", fontsize=10.5, fontweight="bold", color=GREEN)
    cmap = {"ok": GREEN, "dup": GOLD, "bad": RED, "late": ORANGE}
    lab = {"ok": "accepted", "dup": "merged (duplicate)", "bad": "rejected", "late": "late-accepted"}
    ev = [("E1", 5, "ok", 1.95), ("E2", 20, "ok", 1.95), ("E4", 30, "bad", 1.95), ("E5", 50, "bad", 1.95),
          ("E6", 70, "ok", 1.95), ("E8", 80, "ok", 1.95), ("E3", 5, "dup", 0.75), ("E7", 45, "late", 0.05)]
    for n, sec, k, y in ev:
        ax.scatter([X(sec)], [y], s=360, c=cmap[k], zorder=3, edgecolor="white")
        ax.text(X(sec), y, n, ha="center", va="center", color="white", fontsize=8.5, fontweight="bold", zorder=4)
    ax.plot([X(5), X(5)], [1.05, 1.65], color=GOLD, lw=1, ls=":"); ax.plot([X(45), X(45)], [0.3, 1.65], color=ORANGE, lw=1, ls=":")
    ax.text(X(5) + 3, 0.75, "E3 repeats E1 (same sensor + event time) -> merged", fontsize=8.5, color=GOLD, va="center")
    ax.text(X(45) + 3, 0.05, "E7: event 08:00:45, arrives 08:01:40; watermark lag 5 s <= 60 s -> correction", fontsize=8.5, color=ORANGE, va="center")
    ax.text(X(30), 2.35, "missing speed", ha="center", fontsize=7.5, color=RED); ax.text(X(50) - 1, 2.35, "speed -5", ha="center", fontsize=7.5, color=RED)
    for k, c in cmap.items(): ax.scatter([], [], c=c, s=60, label=lab[k])
    ax.legend(loc="lower center", ncol=4, frameon=False, fontsize=9, bbox_to_anchor=(0.5, -0.2))
    ax.text(50, 4.0, "Figure: Event-time placement of events E1-E8 into one-minute windows", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    fig.savefig(f"{OUT}/fig_task2_windows.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def fig3():
    fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.8))
    a.bar(["Weather\n(stored 0.96 GB)", "Imagery\n(200 GB)"], [0.96, 200], color=[TEAL, ORANGE]); a.set_yscale("log"); a.set_ylabel("GB / day (log scale)")
    for i, v in enumerate([0.96, 200]): a.text(i, v * 1.15, f"{v:g} GB", ha="center", fontweight="bold")
    a.set_title("Daily stored volume - imagery is 99.5%", fontsize=11, color=NAVY, fontweight="bold")
    labels = ["Base\n(200 GB)", "Imagery doubled\n(400 GB)"]; st = [4, 7]; sc = [1, 1]; x = [0, 1]; w = 0.35
    b.bar([i - w / 2 for i in x], st, w, color=NAVY, label="Nodes for storage"); b.bar([i + w / 2 for i in x], sc, w, color=GOLD, label="Nodes for 2 h scan")
    for i in x: b.text(i - w / 2, st[i] + 0.1, str(st[i]), ha="center", fontweight="bold"); b.text(i + w / 2, 1.1, "1", ha="center", fontweight="bold")
    b.set_xticks(x); b.set_xticklabels(labels); b.set_ylabel("Nodes"); b.set_ylim(0, 8.5); b.legend(frameon=False)
    b.set_title("Storage governs the cluster size", fontsize=11, color=NAVY, fontweight="bold")
    for ax in (a, b): ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle("Figure: Capacity evaluation for the agriculture and weather platform", fontsize=11, fontweight="bold", color=NAVY, y=1.02)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_task3_capacity.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def fig5():
    fig, ax = plt.subplots(figsize=(10, 4.6)); ax.set_xlim(0, 10); ax.set_ylim(0, 4.6); ax.axis("off")
    ax.text(5, 4.4, "Figure: MapReduce data flow and the cost of 20 iterations", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    names = [("Map", "emit ((segment, hour),\n(speed, 1))", NAVY), ("Combine", "local (sum, count)\nper key", TEAL), ("Partition\n+ Shuffle", "hash(key) mod R,\nsort and merge", ORANGE), ("Reduce", "sum sums, sum counts,\navg = S / N", GREEN), ("Output", "(segment, hour) -> avg\nreplicated file store", GOLD)]
    xs = [0.1, 2.1, 4.1, 6.1, 8.1]
    for (t, d, c), x in zip(names, xs):
        box(ax, x, 2.75, 1.75, 0.55, t.replace("\n", " "), c, fs=9.5); ax.text(x + 0.875, 2.35, d, ha="center", va="center", fontsize=8.3)
    for a, b in zip(xs[:-1], xs[1:]): arrow(ax, a + 1.75, 3.02, b, 3.02)
    ax.text(0.1, 1.55, "Intermediate map output is written to local disk of each mapper; final output to the replicated file store.", fontsize=8.8, style="italic")
    ax.barh([0.95, 0.35], [3456, 172.8], height=0.42, color=[RED, GREEN], left=0)
    ax.set_xlim(0, 10)
    # draw custom bars in axes coords
    ax.cla(); ax.set_xlim(0, 10); ax.set_ylim(0, 4.6); ax.axis("off")
    for (t, d, c), x in zip(names, xs):
        box(ax, x, 3.15, 1.75, 0.55, t.replace("\n", " "), c, fs=9.5); ax.text(x + 0.875, 2.65, d, ha="center", va="center", fontsize=8.3)
    for a, b in zip(xs[:-1], xs[1:]): arrow(ax, a + 1.75, 3.42, b, 3.42)
    ax.text(0.1, 4.2, "Figure: MapReduce data flow and the cost of 20 iterations", fontsize=11, fontweight="bold", color=NAVY)
    ax.text(0.1, 1.95, "Disk read over 20 passes of a 172.8 GB/day dataset (estimate):", fontsize=9.5, fontweight="bold")
    ax.add_patch(plt.Rectangle((0.1, 1.15), 9.0, 0.45, fc=RED)); ax.text(0.2, 1.37, "MapReduce: 3,456 GB (20 full reads)", va="center", color="white", fontweight="bold", fontsize=9.5)
    ax.add_patch(plt.Rectangle((0.1, 0.45), 9.0 * 172.8 / 3456, 0.45, fc=GREEN)); ax.text(0.1 + 9.0 * 172.8 / 3456 + 0.15, 0.67, "In-memory: 172.8 GB (1 read, 19 memory passes)", va="center", fontweight="bold", fontsize=9.5, color=GREEN)
    fig.savefig(f"{OUT}/fig_task5_dataflow.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def fig6():
    fig, ax = plt.subplots(figsize=(10, 5.2)); ax.set_xlim(0, 10); ax.set_ylim(0, 5.2); ax.axis("off")
    ax.text(5, 5.0, "Figure: Fraud detection and controlled sharing - zone separation", ha="center", fontsize=11, fontweight="bold", color=NAVY)
    ax.add_patch(FancyBboxPatch((0.1, 1.0), 6.0, 3.6, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#FDECEA", ec=RED, lw=1.5, ls="--"))
    ax.add_patch(FancyBboxPatch((6.4, 1.0), 3.5, 3.6, boxstyle="round,pad=0.02,rounding_size=0.1", fc="#E8F5EE", ec=GREEN, lw=1.5, ls="--"))
    ax.text(3.1, 4.38, "IDENTIFIED ZONE  (fraud analysts only)", ha="center", color=RED, fontsize=10, fontweight="bold")
    ax.text(8.15, 4.38, "DE-IDENTIFIED ZONE  (researchers)", ha="center", color=GREEN, fontsize=10, fontweight="bold")
    box(ax, 0.25, 2.9, 1.3, 0.9, "Departments\n(payment events)", GREY, tc=NAVY, ec=NAVY, fs=8.5)
    box(ax, 1.85, 2.9, 1.3, 0.9, "S1-S2 Ingest,\nvalidate, de-dup", NAVY, fs=8.5)
    box(ax, 3.45, 3.4, 1.3, 0.8, "S4 Rule A\nstate/account", TEAL, fs=8.5); box(ax, 3.45, 2.4, 1.3, 0.8, "S4 Rule B\nstate/district", TEAL, fs=8.5)
    box(ax, 4.95, 2.9, 1.0, 0.9, "S5 Alerts\n(analysts)", ORANGE, fs=8.5)
    box(ax, 1.85, 1.2, 1.9, 0.8, "S3 Raw event store\n(encrypted)", NAVY, fs=8.5)
    box(ax, 6.6, 2.9, 3.1, 0.9, "S6 De-identify: drop IDs, week + band,\nk >= 5 check, suppress", GREEN, fs=8.5)
    box(ax, 6.6, 1.5, 3.1, 0.8, "Research release (approved only)", GREEN, fs=8.5)
    arrow(ax, 1.55, 3.35, 1.85, 3.35); arrow(ax, 3.15, 3.5, 3.45, 3.8); arrow(ax, 3.15, 3.2, 3.45, 2.8); arrow(ax, 4.75, 3.8, 4.95, 3.5); arrow(ax, 4.75, 2.8, 4.95, 3.2)
    arrow(ax, 2.5, 2.9, 2.8, 2.0); arrow(ax, 3.75, 1.6, 6.6, 3.0, c=RED); arrow(ax, 8.15, 2.9, 8.15, 2.3, c=GREEN)
    box(ax, 0.25, 0.1, 9.65, 0.55, "S7 Access control + append-only audit (separate store)      |      S8 Replay from log, checkpoints, scale partitions 2x", GOLD, fs=9)
    fig.savefig(f"{OUT}/fig_task6_architecture.png", dpi=200, bbox_inches="tight"); plt.close(fig)

for f in (fig1, fig2, fig3, fig5, fig6): f()
print(sorted(os.listdir(OUT)))
