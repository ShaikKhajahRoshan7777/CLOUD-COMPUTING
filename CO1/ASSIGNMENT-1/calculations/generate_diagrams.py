"""Generates the report figures as PNG files into docs/figures/.
Usage:  python calculations/generate_diagrams.py     (needs matplotlib)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = os.path.join(os.path.dirname(__file__), "..", "docs", "figures")
os.makedirs(OUT, exist_ok=True)


def box(ax, x, y, w, h, text, color="#dbeafe", fs=9):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                fc=color, ec="#1e3a8a", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs)


def arrow(ax, x1, y1, x2, y2):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="#334155", lw=1.3))


def timeline():
    stages = ["Mainframe\n1950s", "Mini-\ncomputer\n1960s", "PC\n1970s", "Client-\nServer\n1980s",
              "Cluster\n1990s", "Grid\n1990s-00s", "Utility\n2000s", "Cloud\n2000s+"]
    fig, ax = plt.subplots(figsize=(13, 3.2))
    ax.set_xlim(0, len(stages) * 1.6); ax.set_ylim(0, 2); ax.axis("off")
    for i, s in enumerate(stages):
        color = "#fde68a" if s.startswith("Client") else ("#bbf7d0" if s.startswith("Cloud") else "#dbeafe")
        box(ax, i * 1.6 + 0.1, 0.6, 1.2, 0.9, s, color, fs=9)
        if i < len(stages) - 1:
            arrow(ax, i * 1.6 + 1.32, 1.05, (i + 1) * 1.6 + 0.08, 1.05)
    ax.text(3 * 1.6 + 0.7, 0.3, "University today", ha="center", fontsize=9, color="#92400e")
    ax.set_title("Figure 2.1: Evolution of Computing to Cloud", fontsize=12)
    fig.savefig(os.path.join(OUT, "fig_2_1_evolution.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)


def architecture():
    fig, ax = plt.subplots(figsize=(10, 11))
    ax.set_xlim(0, 10); ax.set_ylim(-1.2, 14); ax.axis("off")
    layers = [
        ("Students / Staff / Admin / 40 Affiliated Colleges / Mobile App", "#f1f5f9"),
        ("DNS + DDoS Protection + WAF   (Security-as-a-Service)", "#fecaca"),
        ("Load Balancer   (managed, health checks)", "#dbeafe"),
        ("Web / Mobile App Tier   (auto-scaled containers - PaaS)", "#dbeafe"),
        ("API Gateway   (OAuth/OIDC, per-college scopes, rate limits)", "#fde68a"),
        ("Service Tier:  SIS | LMS | Library | Exam | Fees", "#dbeafe"),
        ("Cache + Message Queue   (absorb 10x bursts)", "#e9d5ff"),
        ("Private Database Tier   (DBaaS, multi-zone)", "#bbf7d0"),
        ("Object / File Storage   (documents, reports, backups, logs)", "#bbf7d0"),
        ("Backup / Replication Pipeline", "#e5e7eb"),
        ("Secondary Region - Disaster Recovery   (DRaaS)", "#fed7aa"),
    ]
    h, gap, y = 0.9, 0.35, 13.0
    for i, (text, c) in enumerate(layers):
        box(ax, 0.8, y - h, 8.4, h, text, c, fs=10)
        if i < len(layers) - 1:
            arrow(ax, 5, y - h, 5, y - h - gap + 0.02)
        y -= h + gap
    ax.set_title("Figure 8.1: Smart Campus Cloud Architecture", fontsize=13)
    fig.savefig(os.path.join(OUT, "fig_8_1_architecture.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)


def responsibility():
    layers = ["Application", "Middleware / Runtime", "Operating System",
              "Virtualisation", "Servers / Storage / Network"]
    # 1 = customer manages, 0 = provider manages
    models = {"On-premises": [1, 1, 1, 1, 1], "IaaS": [1, 1, 1, 0, 0],
              "PaaS": [1, 0, 0, 0, 0], "SaaS": [0, 0, 0, 0, 0]}
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.axis("off"); ax.set_xlim(0, len(models) * 2.2); ax.set_ylim(0, len(layers) + 1)
    for j, (m, vals) in enumerate(models.items()):
        ax.text(j * 2.2 + 1.0, len(layers) + 0.4, m, ha="center", fontweight="bold")
        for i, v in enumerate(vals):
            y = len(layers) - 1 - i
            ax.add_patch(plt.Rectangle((j * 2.2, y), 2.0, 0.9,
                                       fc="#fca5a5" if v else "#86efac", ec="white"))
            ax.text(j * 2.2 + 1.0, y + 0.45, "Customer" if v else "Provider", ha="center", va="center", fontsize=8)
    for i, l in enumerate(layers):
        ax.text(-0.1, len(layers) - 1 - i + 0.45, l, ha="right", va="center", fontsize=9)
    ax.set_title("Figure 6.1: IaaS vs PaaS vs SaaS - who manages what", fontsize=12)
    fig.savefig(os.path.join(OUT, "fig_6_1_service_models.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)


def cost_chart():
    labels = ["On-premises", "IaaS", "PaaS/SaaS", "PaaS/SaaS\n(revised, Day-4)"]
    vals = [75.0, 53.1, 44.1, 62.1]
    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, vals, color=["#94a3b8", "#60a5fa", "#4ade80", "#fbbf24"])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 1, f"{v:.1f}", ha="center")
    ax.set_ylabel("3-year cost (Rs lakh)")
    ax.set_title("Illustrative 3-Year Cost Comparison")
    fig.savefig(os.path.join(OUT, "fig_10_1_cost.png"), dpi=160, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    timeline(); architecture(); responsibility(); cost_chart()
    print("Figures written to", os.path.abspath(OUT))
