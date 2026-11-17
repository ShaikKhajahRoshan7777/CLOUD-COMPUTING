"""Generates every figure used in the report (matplotlib).  Run:  python calculations/make_diagrams.py"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

plt.rcParams["font.family"] = ["Liberation Serif", "DejaVu Serif"]
OUT = os.path.join(os.path.dirname(__file__), "..", "diagrams")
NAVY, BLUE, TEAL, ORANGE, GREEN, GREY, RED, GOLD = "#1F3864", "#2E75B6", "#1B8A8F", "#E07B39", "#4C9F50", "#6B7280", "#C0392B", "#C9A227"
LIGHT = {"navy": "#DCE6F5", "blue": "#DDEBF7", "teal": "#D5F0F0", "orange": "#FCE4D2", "green": "#DDF0DD", "grey": "#EEF0F3", "gold": "#FBF1CC", "red": "#F8DAD6"}


def box(ax, x, y, w, h, text, fc="#DDEBF7", ec=BLUE, fs=9, bold=False, color="black", lw=1.4, r=0.08):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.0,rounding_size={r}", fc=fc, ec=ec, lw=lw))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", color=color, linespacing=1.25)


def arrow(ax, p, q, color=GREY, style="-|>", lw=1.5, ls="-", rad=0.0):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=12, color=color, lw=lw, ls=ls,
                                 connectionstyle=f"arc3,rad={rad}"))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


# ---------------------------------------------------------------- Figure: timeline
def timeline():
    fig, ax = plt.subplots(figsize=(11, 4.6))
    ax.set_xlim(0, 11); ax.set_ylim(0, 4.6); ax.axis("off")
    stages = [("1950s", "Mainframes", "Centralised,\nbatch jobs", NAVY),
              ("1960s-70s", "Minicomputers", "Departmental,\ncheaper", BLUE),
              ("1980s", "Personal\nComputers", "Desktop,\nstand-alone", TEAL),
              ("1990s", "Client-Server", "LAN, dedicated\nservers", GREEN),
              ("1990s-2000s", "Clusters &\nGrid", "Many nodes\nshared", GOLD),
              ("2000s", "Utility\nComputing", "Pay-per-use\nmetering", ORANGE),
              ("2006 onward", "Cloud\nComputing", "Elastic, self-\nservice, global", RED)]
    ax.plot([0.5, 10.5], [2.3, 2.3], color=GREY, lw=3, zorder=1)
    n = len(stages)
    for i, (yr, name, desc, c) in enumerate(stages):
        x = 0.9 + i * (9.2 / (n - 1))
        ax.scatter([x], [2.3], s=260, color=c, zorder=3, edgecolor="white", linewidth=2)
        up = i % 2 == 0
        ax.plot([x, x], [2.3, 3.0 if up else 1.6], color=c, lw=1.5)
        yb = 3.0 if up else 0.55
        ax.add_patch(FancyBboxPatch((x - 0.72, yb), 1.44, 1.05, boxstyle="round,pad=0,rounding_size=0.08", fc="white", ec=c, lw=1.8))
        ax.text(x, yb + 0.80, name, ha="center", va="center", fontsize=9.5, fontweight="bold", color=c, linespacing=1.1)
        ax.text(x, yb + 0.30, desc, ha="center", va="center", fontsize=8, color="#333", linespacing=1.1)
        ax.text(x, 2.3 + (-0.0), "", ha="center")
        ax.text(x, 2.08 if up else 2.52, yr, ha="center", va="center", fontsize=8, color=c, fontweight="bold")
    ax.add_patch(FancyBboxPatch((0.1, 0.0), 5.0, 0.36, boxstyle="round,pad=0,rounding_size=0.05", fc=LIGHT["red"], ec=RED, lw=1.2))
    ax.text(2.6, 0.18, "University's current system = Client-Server stage (12 dedicated servers)", ha="center", va="center", fontsize=8.3, color=RED, fontweight="bold")
    ax.text(5.5, 4.45, "Evolution of Computing Infrastructure Towards Cloud", ha="center", fontsize=13, fontweight="bold", color=NAVY)
    save(fig, "fig_timeline.png")


# ---------------------------------------------------------------- Figure: virtualization stacks
def virtualization():
    fig, ax = plt.subplots(figsize=(11, 3.9)); ax.set_xlim(0, 11); ax.set_ylim(-0.3, 3.6); ax.axis("off")
    def stack(x0, title, layers, tcolor):
        ax.text(x0 + 1.55, 3.25, title, ha="center", fontsize=10.5, fontweight="bold", color=tcolor)
        y = 0.2
        for text, fc, ec in layers:
            box(ax, x0, y, 3.1, 0.62, text, fc=fc, ec=ec, fs=8.8); y += 0.72
    stack(0.15, "Type-1 (bare-metal)", [("Physical hardware (CPU, RAM, disk, NIC)", LIGHT["grey"], GREY), ("Hypervisor  (ESXi, KVM, Hyper-V, Xen)", LIGHT["orange"], ORANGE),
          ("VM 1: Guest OS + SIS app", LIGHT["blue"], BLUE), ("VM 2: Guest OS + Library app", LIGHT["blue"], BLUE)], ORANGE)
    stack(3.95, "Type-2 (hosted)", [("Physical hardware", LIGHT["grey"], GREY), ("Host operating system (Windows / Linux)", LIGHT["grey"], GREY),
          ("Hypervisor  (VirtualBox, VMware Workstation)", LIGHT["orange"], ORANGE), ("Guest VMs: OS + application", LIGHT["blue"], BLUE)], ORANGE)
    stack(7.75, "OS-level (containers)", [("Physical hardware", LIGHT["grey"], GREY), ("Host OS kernel (shared)", LIGHT["grey"], GREY),
          ("Container engine  (Docker / containerd)", LIGHT["green"], GREEN), ("Containers: App + libraries only", LIGHT["teal"], TEAL)], GREEN)
    ax.text(5.5, -0.22, "Heavier isolation  <-------------------------------------------->  Lighter, faster start-up", ha="center", fontsize=8.5, color=GREY, style="italic")
    save(fig, "fig_virtualization.png")


def consolidation_chart():
    r = json.load(open(os.path.join(os.path.dirname(__file__), "results_consolidation.json")))
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4.0), gridspec_kw={"width_ratios": [1.0, 1.1]})
    a1.bar(["Before\n(12 physical servers)", "After\n(3 active hosts)"], [15, r["util_active"]], color=[RED, GREEN], width=0.5)
    a1.axhline(70, color=NAVY, ls="--", lw=1.3); a1.text(1.45, 72, "target 70%", color=NAVY, fontsize=9, ha="right")
    a1.text(0, 15 + 2, "15%", ha="center", fontweight="bold", fontsize=11)
    a1.text(1, r["util_active"] - 8, f'{r["util_active"]:.0f}%', ha="center", fontweight="bold", fontsize=12, color="white")
    a1.set_ylim(0, 100); a1.set_ylabel("Average CPU utilisation (%)"); a1.set_title("Utilisation", fontweight="bold", color=NAVY)
    labels = ["Today\n(owned)", "Average\n(3 + 1 spare)", "Peak weeks\n(3 + 15 burst)"]
    a2.bar(labels, [12, r["final_hosts"], r["peak_hosts"]], color=[RED, GREEN, ORANGE], width=0.5)
    for i, v in enumerate([12, r["final_hosts"], r["peak_hosts"]]): a2.text(i, v + 0.4, str(v), ha="center", fontweight="bold", fontsize=11)
    a2.set_ylim(0, 21); a2.set_ylabel("Hosts / servers required"); a2.set_title("Hosts required", fontweight="bold", color=NAVY)
    for a in (a1, a2):
        a.spines[["top", "right"]].set_visible(False)
    fig.tight_layout(); save(fig, "fig_consolidation.png")


def service_layers():
    fig, ax = plt.subplots(figsize=(10.5, 4.6)); ax.set_xlim(0, 10.5); ax.set_ylim(0, 4.6); ax.axis("off")
    layers = ["Application", "Data", "Runtime / Middleware", "Operating System", "Virtualization", "Servers & Storage", "Networking"]
    # 1 = customer manages, 0 = provider manages
    cols = {"On-premise": [1, 1, 1, 1, 1, 1, 1], "IaaS": [1, 1, 1, 1, 0, 0, 0], "PaaS": [1, 1, 0, 0, 0, 0, 0], "SaaS": [0, 0, 0, 0, 0, 0, 0]}
    ax.text(0.1, 4.2, "Layer", fontweight="bold", fontsize=10, color=NAVY)
    for j, (name, vals) in enumerate(cols.items()):
        x = 2.6 + j * 2.0
        ax.text(x + 0.9, 4.2, name, ha="center", fontweight="bold", fontsize=10.5, color=NAVY)
        for i, v in enumerate(vals):
            y = 3.55 - i * 0.5
            box(ax, x, y, 1.8, 0.42, "You manage" if v else "Provider manages", fc=LIGHT["orange"] if v else LIGHT["blue"], ec=ORANGE if v else BLUE, fs=8.3, r=0.05)
    for i, l in enumerate(layers):
        ax.text(0.1, 3.76 - i * 0.5, l, va="center", fontsize=9.5)
    box(ax, 0.1, 0.0, 2.3, 0.3, "Orange = university's duty", fc=LIGHT["orange"], ec=ORANGE, fs=8.3, r=0.04)
    box(ax, 2.6, 0.0, 2.3, 0.3, "Blue = cloud provider's duty", fc=LIGHT["blue"], ec=BLUE, fs=8.3, r=0.04)
    save(fig, "fig_service_layers.png")


def _bar(ax, x, y, w, h, text, fc, ec, fs=8.5, bold=False):
    box(ax, x, y, w, h, text, fc=fc, ec=ec, fs=fs, bold=bold, r=0.06)


def architecture():
    fig, ax = plt.subplots(figsize=(12, 8.2)); ax.set_xlim(0, 12); ax.set_ylim(0, 8.2); ax.axis("off")
    # users
    _bar(ax, 0.3, 7.35, 2.6, 0.6, "Students & staff\n(4 campuses, browsers)", LIGHT["grey"], GREY)
    _bar(ax, 3.1, 7.35, 2.6, 0.6, "Campus networks\n(secure VPN link)", LIGHT["grey"], GREY)
    _bar(ax, 5.9, 7.35, 2.6, 0.6, "Admins & faculty\n(SSO + MFA)", LIGHT["grey"], GREY)
    ax.text(10.2, 7.65, "Hybrid deployment:\nVPN-linked campuses +\npublic-cloud workloads", ha="center", va="center", fontsize=8.5, color=NAVY, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", fc=LIGHT["gold"], ec=GOLD))
    for x in (1.6, 4.4, 7.2): arrow(ax, (x, 7.35), (x, 6.95))
    _bar(ax, 0.3, 6.35, 8.2, 0.55, "DNS  +  CDN  +  Web Application Firewall  (managed edge services)", LIGHT["teal"], TEAL, bold=True)
    arrow(ax, (4.4, 6.35), (4.4, 6.0))
    _bar(ax, 0.3, 5.45, 8.2, 0.55, "Load Balancer  (health checks, TLS termination, spans Zone-1 and Zone-2)", LIGHT["teal"], TEAL, bold=True)
    # region
    ax.add_patch(FancyBboxPatch((0.2, 0.85), 8.4, 4.45, boxstyle="round,pad=0,rounding_size=0.1", fc="#FAFBFD", ec=NAVY, lw=2, ls="--"))
    ax.text(0.4, 5.08, "PRIMARY REGION  (private virtual network, subnets, security groups)", fontsize=8.8, fontweight="bold", color=NAVY, va="center")
    _bar(ax, 0.4, 4.2, 8.0, 0.55, "API LAYER  -  REST gateway:  /results   /fees   /library      [PaaS]", LIGHT["orange"], ORANGE, bold=True)
    arrow(ax, (7.6, 5.45), (7.6, 4.78))
    for i, zx in enumerate((0.4, 4.5)):
        ax.add_patch(FancyBboxPatch((zx, 1.25), 3.9, 2.75, boxstyle="round,pad=0,rounding_size=0.08", fc="white", ec=BLUE, lw=1.6))
        ax.text(zx + 1.95, 3.82, f"AVAILABILITY ZONE {i + 1}", ha="center", fontsize=8.5, fontweight="bold", color=BLUE)
        _bar(ax, zx + 0.15, 2.95, 3.6, 0.55, "SIS application servers (VMs)  [IaaS]", LIGHT["blue"], BLUE)
        _bar(ax, zx + 0.15, 2.3, 3.6, 0.55, "Exam Portal containers, auto-scaling  [PaaS]", LIGHT["green"], GREEN)
        _bar(ax, zx + 0.15, 1.4, 3.6, 0.75, "Managed database\n" + ("PRIMARY (read / write)" if i == 0 else "STANDBY (sync replica)") + "  [PaaS]", LIGHT["gold"], GOLD)
    arrow(ax, (4.3, 1.8), (4.6, 1.8), color=GOLD, lw=2, style="<|-|>")
    for x in (2.35, 6.45): arrow(ax, (x, 4.2), (x, 4.0))
    _bar(ax, 0.4, 0.95, 8.0, 0.22, "Object storage + encrypted backups / snapshots  [IaaS]", LIGHT["grey"], GREY, fs=8)
    # SaaS column
    ax.add_patch(FancyBboxPatch((8.95, 3.3), 2.85, 2.0, boxstyle="round,pad=0,rounding_size=0.1", fc="#FBFFFB", ec=GREEN, lw=1.8))
    ax.text(10.37, 5.1, "SaaS (provider-managed)", ha="center", fontsize=9, fontweight="bold", color=GREEN)
    for j, t in enumerate(("Learning Mgmt System", "Email & collaboration", "Library system")):
        _bar(ax, 9.1, 4.45 - j * 0.45, 2.55, 0.37, t, LIGHT["green"], GREEN, fs=8.5)
    arrow(ax, (8.6, 4.5), (8.95, 4.5), color=GREEN, lw=1.5, style="<|-|>")
    # DR region
    ax.add_patch(FancyBboxPatch((8.95, 0.85), 2.85, 2.25, boxstyle="round,pad=0,rounding_size=0.1", fc="#FFF9F6", ec=RED, lw=1.8, ls="--"))
    ax.text(10.37, 2.9, "DR REGION (pilot light)", ha="center", fontsize=9, fontweight="bold", color=RED)
    _bar(ax, 9.1, 2.15, 2.55, 0.5, "DB replica (async)", LIGHT["red"], RED, fs=8.5)
    _bar(ax, 9.1, 1.55, 2.55, 0.5, "Backup copies + images", LIGHT["red"], RED, fs=8.5)
    _bar(ax, 9.1, 0.95, 2.55, 0.5, "Standby stack (scale on failover)", LIGHT["red"], RED, fs=8)
    arrow(ax, (8.4, 1.8), (9.1, 2.3), color=RED, lw=1.8, ls="--")
    ax.text(8.78, 2.6, "async", fontsize=7, color=RED, ha="center")
    # cross-cutting
    _bar(ax, 0.3, 0.12, 11.5, 0.5, "Security & operations:  IAM / SSO + MFA   |   TLS in transit, AES-256 at rest   |   Monitoring, logging & alerts   |   Daily backups, RPO 15 min / RTO 4 h", LIGHT["navy"], NAVY, fs=8.5, bold=True)
    save(fig, "fig_architecture.png")


def revised_architecture():
    fig, ax = plt.subplots(figsize=(12, 8.4)); ax.set_xlim(0, 12); ax.set_ylim(0, 8.4); ax.axis("off")
    _bar(ax, 0.3, 7.55, 2.5, 0.6, "Mobile app\n(students, parents)", LIGHT["orange"], ORANGE)
    _bar(ax, 3.0, 7.55, 2.5, 0.6, "Web users\n(27,000 on campus)", LIGHT["grey"], GREY)
    _bar(ax, 5.7, 7.55, 3.2, 0.6, "40 affiliated colleges\n(tenants, API clients)", LIGHT["orange"], ORANGE, bold=True)
    for x in (1.55, 4.25, 7.3): arrow(ax, (x, 7.55), (x, 7.2))
    _bar(ax, 0.3, 6.65, 8.6, 0.55, "Global DNS (health-check failover)  +  CDN  +  WAF / DDoS shield", LIGHT["teal"], TEAL, bold=True)
    arrow(ax, (4.6, 6.65), (4.6, 6.3))
    _bar(ax, 0.3, 5.75, 8.6, 0.55, "API GATEWAY:  OAuth2 / JWT (tenant_id claim) | per-tenant rate limit & quota | versioned /api/v1", LIGHT["orange"], ORANGE, bold=True)
    ax.add_patch(FancyBboxPatch((0.2, 0.85), 8.8, 4.65, boxstyle="round,pad=0,rounding_size=0.1", fc="#FAFBFD", ec=NAVY, lw=2, ls="--"))
    ax.text(0.4, 5.28, "PRIMARY REGION  -  THREE availability zones", fontsize=8.8, fontweight="bold", color=NAVY, va="center")
    arrow(ax, (7.6, 5.75), (7.6, 5.17))
    _bar(ax, 0.4, 4.35, 5.4, 0.8, "CONTAINER ORCHESTRATION (managed Kubernetes)\nAPI pods: results, fees, library  -  autoscale 2 to 99 pods  [PaaS]", LIGHT["green"], GREEN, bold=True)
    _bar(ax, 6.0, 4.35, 2.8, 0.8, "Serverless functions\nreceipts, SMS/e-mail, reports\n[FaaS - XaaS]", LIGHT["teal"], TEAL)
    _bar(ax, 0.4, 3.45, 2.6, 0.7, "In-memory cache\n(results, library search)", LIGHT["blue"], BLUE)
    _bar(ax, 3.2, 3.45, 2.6, 0.7, "Message queue\n(fee events, async jobs)", LIGHT["blue"], BLUE)
    _bar(ax, 6.0, 3.45, 2.8, 0.7, "SIS core (VMs, 3 zones)\nlegacy logic  [IaaS]", LIGHT["blue"], BLUE)
    for x in (1.7, 4.5, 7.4): arrow(ax, (x, 4.35), (x, 4.17))
    _bar(ax, 0.4, 1.9, 4.2, 1.2, "Managed DATABASE (DBaaS)\nmulti-AZ primary + standby\nrow-level security by tenant_id", LIGHT["gold"], GOLD, bold=True)
    _bar(ax, 4.8, 1.9, 4.0, 1.2, "2 x read replicas\n(result look-ups, reports)\n+ point-in-time recovery", LIGHT["gold"], GOLD)
    arrow(ax, (4.6, 2.5), (4.8, 2.5), color=GOLD, lw=2)
    for x in (1.7, 4.5, 7.4): arrow(ax, (x, 3.45), (x, 3.12))
    _bar(ax, 0.4, 1.0, 8.4, 0.7, "Object storage (documents, backups)  |  Secrets vault + KMS keys per tenant  |  Central logs, metrics, tracing", LIGHT["grey"], GREY, fs=8.3)
    # SaaS
    ax.add_patch(FancyBboxPatch((9.3, 4.2), 2.5, 1.9, boxstyle="round,pad=0,rounding_size=0.1", fc="#FBFFFB", ec=GREEN, lw=1.8))
    ax.text(10.55, 5.9, "SaaS (unchanged)", ha="center", fontsize=9, fontweight="bold", color=GREEN)
    for j, t in enumerate(("LMS", "Email", "Library")):
        _bar(ax, 9.45, 5.25 - j * 0.45, 2.2, 0.37, t, LIGHT["green"], GREEN, fs=8.5)
    # region B
    ax.add_patch(FancyBboxPatch((9.3, 0.85), 2.5, 3.1, boxstyle="round,pad=0,rounding_size=0.1", fc="#FFF9F6", ec=RED, lw=1.8, ls="--"))
    ax.text(10.55, 3.75, "REGION B - WARM STANDBY", ha="center", fontsize=8.6, fontweight="bold", color=RED)
    for j, t in enumerate(("API pods (min 2)", "DB replica (async)", "Cache + queue", "Backups, images")):
        _bar(ax, 9.45, 3.1 - j * 0.55, 2.2, 0.45, t, LIGHT["red"], RED, fs=8.3)
    arrow(ax, (8.8, 2.4), (9.45, 2.55), color=RED, lw=1.8, ls="--")
    _bar(ax, 0.3, 0.12, 11.5, 0.5, "Security:  per-tenant isolation | WAF | TLS 1.2+ / AES-256 | audit logs   |   Targets: 99.9% availability, RPO 5 min, RTO 15 min", LIGHT["navy"], NAVY, fs=8.5, bold=True)
    save(fig, "fig_revised_architecture.png")


def cost_chart():
    c = json.load(open(os.path.join(os.path.dirname(__file__), "results_cost.json")))["summary"]
    names = list(c.keys())
    short = ["On-premise\n(refresh)", "IaaS-based", "PaaS/SaaS\n(full)", "Recommended\nhybrid"]
    capex = [c[n]["capex"] for n in names]; opex3 = [c[n]["opex_year"] * 3 for n in names]
    fig, ax = plt.subplots(figsize=(8.6, 4.4))
    ax.bar(short, capex, color=NAVY, width=0.55, label="CapEx / one-time")
    ax.bar(short, opex3, bottom=capex, color=[BLUE, BLUE, BLUE, GREEN], width=0.55, label="OpEx for 3 years")
    for i, n in enumerate(names): ax.text(i, c[n]["total"] + 4, f"Rs. {c[n]['total']:.0f} L", ha="center", fontweight="bold", fontsize=10.5)
    ax.set_ylim(0, 270); ax.set_ylabel("3-year total cost of ownership (Rs. lakh)")
    ax.spines[["top", "right"]].set_visible(False); ax.legend(frameon=False, loc="upper right")
    ax.set_title("Three-year cost comparison", fontweight="bold", color=NAVY)
    fig.tight_layout(); save(fig, "fig_cost.png")


def roadmap():
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    items = [("Phase 0: Assess, landing zone, VPN, IAM", 0, 2, NAVY), ("Phase 1: Email -> SaaS (low risk, quick win)", 1, 2, GREEN),
             ("Phase 2: Library -> SaaS", 2.5, 2, GREEN), ("Phase 3: LMS -> SaaS (before new semester)", 4, 3, GREEN),
             ("Phase 4: Exam Portal -> PaaS containers + autoscale", 6, 3, ORANGE), ("Phase 5: SIS -> IaaS VMs, then API layer", 8, 3.5, BLUE),
             ("Phase 6: Decommission old servers; DR drill", 11, 1.5, RED)]
    for i, (t, s, d, c) in enumerate(items):
        y = len(items) - 1 - i
        ax.barh(y, d, left=s, color=c, height=0.55, alpha=0.92)
        ax.text(s + d + 0.12 if s + d < 9 else s - 0.12, y, t, va="center", ha="left" if s + d < 9 else "right", fontsize=8.8)
    ax.set_yticks([]); ax.set_xlim(0, 15); ax.set_xticks(range(0, 13)); ax.set_xlabel("Months from project start")
    ax.spines[["top", "right", "left"]].set_visible(False); ax.grid(axis="x", alpha=0.25)
    ax.set_title("Phased migration roadmap (12 months)", fontweight="bold", color=NAVY)
    fig.tight_layout(); save(fig, "fig_roadmap.png")


def availability_chart():
    d = json.load(open(os.path.join(os.path.dirname(__file__), "results_dayfour.json")))
    labels = ["Original\n(1 region, 2 zones)", "Revised-A\n(3 zones + gateway)", "Revised-B\n(A + 2nd region)"]
    vals = [d["down_orig"], d["down_rev1"], d["down_rev2"]]
    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    bars = ax.bar(labels, vals, color=[RED, ORANGE, GREEN], width=0.5)
    ax.axhline(d["allowed_h"], color=NAVY, ls="--", lw=1.6); ax.text(2.45, d["allowed_h"] + 0.35, f"99.9% limit = {d['allowed_h']} h/yr", ha="right", color=NAVY, fontsize=9.5)
    for b, v in zip(bars, vals): ax.text(b.get_x() + b.get_width() / 2, v + 0.3, f"{v:.1f} h", ha="center", fontweight="bold")
    ax.set_ylabel("Expected downtime (hours / year)"); ax.set_ylim(0, 14); ax.spines[["top", "right"]].set_visible(False)
    ax.set_title("Expected downtime vs. the 99.9% allowance", fontweight="bold", color=NAVY)
    fig.tight_layout(); save(fig, "fig_availability.png")


if __name__ == "__main__":
    timeline(); virtualization(); consolidation_chart(); service_layers()
    architecture(); revised_architecture(); cost_chart(); roadmap(); availability_chart()
