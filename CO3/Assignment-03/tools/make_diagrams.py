"""Generates all architecture / flow diagrams used in the report.  Run: python tools/make_diagrams.py"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "diagrams"
plt.rcParams["font.family"] = "Liberation Serif"
NAVY, TEAL, ORANGE, GREEN, RED, PURPLE, GREY = "#1F3A5F", "#0E8A8A", "#E07A1F", "#2E8B57", "#C0392B", "#6C4AB6", "#F2F5F9"


def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, w * 10); ax.set_ylim(0, h * 10); ax.axis("off")
    fig.patch.set_facecolor("white")
    ax.text(w * 5, h * 10 - 3, title, ha="center", va="top", fontsize=15, fontweight="bold", color=NAVY)
    return fig, ax


def box(ax, x, y, w, h, text, color=NAVY, fs=11, tc="white", sub=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=2", fc=color, ec="white", lw=1.5))
    if sub:
        ax.text(x + w / 2, y + h * 0.64, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold")
        ax.text(x + w / 2, y + h * 0.28, sub, ha="center", va="center", fontsize=fs - 2.5, color=tc, style="italic")
    else:
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold", linespacing=1.25)


def arrow(ax, p, q, color="#444", label=None, style="-|>", rad=0.0, ls="-", fs=9, off=(0, 1.6)):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle=style, mutation_scale=16, lw=1.8, color=color, linestyle=ls,
                                 connectionstyle=f"arc3,rad={rad}"))
    if label:
        ax.text((p[0] + q[0]) / 2 + off[0], (p[1] + q[1]) / 2 + off[1], label, ha="center", fontsize=fs, color=color, style="italic")


def save(fig, name):
    fig.savefig(OUT / name, dpi=170, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def q1():
    fig, ax = canvas(11, 5.6, "Q1 - Cloud Access Architecture:  Client -> Network -> Cloud Service")
    rows = [("Web Browser / Cloud Console", "Method 1: GUI over HTTPS", TEAL, 38), ("Mobile Application", "Method 2: Android / iOS app", ORANGE, 24),
            ("API / SDK / CLI", "Method 3: programmatic REST calls", PURPLE, 10)]
    for t, s, c, y in rows:
        box(ax, 3, y, 28, 10, t, c, 11, sub=s)
        arrow(ax, (32, y + 5), (46, 29))
    box(ax, 46, 20, 20, 18, "Internet / Network", NAVY, 12, sub="Wi-Fi - 4G/5G - LAN\nTLS encryption + DNS")
    arrow(ax, (67, 29), (79, 29), label="HTTPS request", off=(0, 2))
    arrow(ax, (79, 25), (67, 25), color=GREEN, label="response", off=(0, -3.4))
    box(ax, 79, 12, 28, 34, "Cloud Service", GREEN, 13, sub="Storage - Web App - API Gateway\nAuthentication - Data Centre")
    ax.text(55, 2.5, "Client = device + browser/app/code        Network = transport + security        Cloud = on-demand shared resources",
            ha="center", fontsize=9.5, color="#555")
    save(fig, "q1_access_architecture.png")


def q2():
    fig, ax = canvas(12.6, 5.8, "Q2 - User Request Mapped to Cloud Services (Web Application Interaction)")
    chain = [("User", "Edits document", TEAL), ("Browser", "Web client (JS)", ORANGE), ("Internet", "DNS + HTTPS", NAVY),
             ("Load Balancer\n+ Web Server", "Cloud front end", PURPLE), ("Application\nService", "Business logic", GREEN)]
    x = 3
    for i, (t, s, c) in enumerate(chain):
        box(ax, x, 30, 17, 15, t, c, 10.5, sub=s)
        if i:
            arrow(ax, (x - 3.4, 37.5), (x - 0.2, 37.5))
        ax.text(x + 8.5, 49, f"{i + 1}", ha="center", fontsize=12, color="white", fontweight="bold",
                bbox=dict(boxstyle="circle", fc=ORANGE, ec="none"))
        x += 20.5
    box(ax, 104, 40, 18, 12, "Storage\n(files, versions)", "#8E44AD", 10)
    box(ax, 104, 22, 18, 12, "Database\n(users, metadata)", "#B9770E", 10)
    arrow(ax, (101.5, 40), (104, 46)); arrow(ax, (101.5, 34), (104, 28))
    arrow(ax, (110, 13), (6, 13), color=GREEN, label="6. Response: updated page / saved status returned to user", off=(0, 2.2))
    ax.text(63, 4, "Platform A: Google Workspace (Google Cloud)          Platform B: Microsoft 365 (Azure)  -  same pattern, different services",
            ha="center", fontsize=9.5, color="#555")
    save(fig, "q2_interaction.png")


def q3():
    fig, ax = canvas(11, 4.4, "Q3 - Web API Communication Flow (REST over HTTPS)")
    box(ax, 3, 14, 22, 18, "Client", TEAL, 12, sub="Python program\nrequests.get()")
    box(ax, 44, 14, 22, 18, "Internet", NAVY, 12, sub="HTTPS - TLS")
    box(ax, 85, 14, 22, 18, "Cloud / Server", GREEN, 12, sub="pypi.org JSON API")
    arrow(ax, (26, 26), (43, 26), label="API REQUEST", off=(0, 2)); arrow(ax, (67, 26), (84, 26))
    arrow(ax, (84, 20), (67, 20), color=ORANGE); arrow(ax, (43, 20), (26, 20), color=ORANGE, label="API RESPONSE", off=(0, -3.4))
    ax.text(14, 8, "GET /pypi/flask/json\nAccept: application/json", ha="center", fontsize=9, family="DejaVu Sans Mono", color=TEAL)
    ax.text(96, 8, "200 OK  +  JSON body\n(404 if not found)", ha="center", fontsize=9, family="DejaVu Sans Mono", color=GREEN)
    save(fig, "q3_api_flow.png")


def q4():
    fig, ax = canvas(12.4, 6.2, "Q4 - Secure Cloud Access Flow with Attack Points and Countermeasures")
    steps = [("User", TEAL), ("Authentication\n(who are you?)", ORANGE), ("Network\n(HTTPS / TLS)", NAVY), ("Cloud Service", GREEN),
             ("Authorization\n(what can you do?)", PURPLE), ("Resource\n(data / files)", "#8E44AD")]
    x = 2
    for i, (t, c) in enumerate(steps):
        box(ax, x, 36, 16, 12, t, c, 10)
        if i:
            arrow(ax, (x - 3.8, 42), (x - 0.4, 42))
        x += 19.5
    attacks = [(10, "Device theft /\nmalware", "Device lock, antivirus,\nendpoint management"), (29.5, "Phishing / brute\nforce / weak password", "MFA, lockout policy,\nstrong passwords"), (49, "Eavesdropping /\nman-in-the-middle", "TLS 1.3, HSTS,\ncertificates"),
               (68.5, "DDoS /\nAPI abuse", "Rate limiting,\nWAF, firewall"), (88, "Privilege escalation /\ntoken theft", "RBAC, least privilege,\nshort-lived tokens"),
               (107.5, "Data leak /\nmisconfiguration", "Encryption at rest,\naudit logs, backups")]
    for ax_x, threat, fix in attacks:
        ax.text(ax_x, 53, "!", ha="center", va="center", fontsize=13, color="white", fontweight="bold", bbox=dict(boxstyle="circle", fc=RED, ec="none"))
        box(ax, ax_x - 9.2, 14, 18.4, 14, "", GREY, 9, tc="black")
        ax.text(ax_x, 24.5, threat, ha="center", va="center", fontsize=8.8, color=RED, fontweight="bold")
        ax.text(ax_x, 17.5, fix, ha="center", va="center", fontsize=8.5, color=GREEN)
        arrow(ax, (ax_x, 52), (ax_x, 49), color=RED, ls="--")
    ax.text(5, 31, "Threat (red)  /  Mitigation (green)", fontsize=9.5, color="#555", style="italic")
    save(fig, "q4_secure_flow.png")


def q5():
    fig, ax = canvas(12.2, 4.8, "Q5 - Cloud Collaboration Workflow")
    st = [("1. Create", "Shared folder\nand document", TEAL), ("2. Share", "Invite users\nassign roles", ORANGE), ("3. Co-edit", "Concurrent access\nlive cursors", GREEN),
          ("4. Review", "Comments and\nsuggestions", PURPLE), ("5. Version", "History and\nrestore", NAVY), ("6. Finalise", "Lock / publish\nread-only link", "#8E44AD")]
    x = 2
    for i, (t, s, c) in enumerate(st):
        box(ax, x, 18, 16.5, 17, t, c, 11, sub=s)
        if i:
            arrow(ax, (x - 3.6, 26.5), (x - 0.4, 26.5))
        x += 19.4
    ax.text(61, 9, "Roles: Owner (all rights)  -  Editor (read, comment, edit)  -  Commenter (read, comment)  -  Viewer (read only)",
            ha="center", fontsize=10, color=NAVY)
    save(fig, "q5_collab_workflow.png")


def q6():
    fig, ax = canvas(12, 6, "Q6 - Architecture: Cloud-Based Assignment Submission and Evaluation")
    box(ax, 2, 40, 20, 11, "Students", TEAL, 11, sub="Browser / mobile app")
    box(ax, 2, 22, 20, 11, "Faculty", ORANGE, 11, sub="Browser / mobile app")
    box(ax, 2, 5, 20, 11, "Admin", PURPLE, 11, sub="Console")
    for y in (45, 27, 10):
        arrow(ax, (23, y + 0.5), (36, 30))
    box(ax, 36, 18, 16, 24, "Internet\nHTTPS / TLS", NAVY, 11)
    arrow(ax, (53, 30), (62, 30))
    box(ax, 62, 36, 24, 14, "Auth Service", ORANGE, 11, sub="login - token - roles")
    box(ax, 62, 19, 24, 14, "Portal API / Web App", GREEN, 11, sub="upload - review - grade")
    box(ax, 62, 2, 24, 14, "Audit & Notification", PURPLE, 10.5, sub="logs - email alerts")
    arrow(ax, (74, 36), (74, 33.4)); arrow(ax, (74, 19), (74, 16.4))
    box(ax, 95, 26, 22, 22, "Shared Cloud\nStorage", "#8E44AD", 11, sub="submissions - versions\nfeedback - rubric")
    arrow(ax, (86.4, 26), (94.6, 33))
    save(fig, "q6_architecture.png")


def q6_mockup():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    fig.suptitle("Q6 - Prototype Mock-up (wireframes of the cloud portal)", fontsize=15, fontweight="bold", color=NAVY)
    for a in axes:
        a.set_xlim(0, 100); a.set_ylim(0, 60); a.axis("off")
    a = axes[0]
    a.add_patch(FancyBboxPatch((3, 3), 94, 52, boxstyle="round,pad=0.5", fc="#F8FAFC", ec=NAVY, lw=2))
    a.add_patch(FancyBboxPatch((3, 46), 94, 9, boxstyle="square,pad=0", fc=NAVY, ec=NAVY))
    a.text(50, 50.5, "SIMATS Assignment Portal  -  Login", ha="center", color="white", fontsize=11, fontweight="bold")
    for y, t in [(36, "Username: asha"), (26, "Password: ********")]:
        a.add_patch(FancyBboxPatch((20, y), 60, 6.5, boxstyle="round,pad=0.3", fc="white", ec="#999"))
        a.text(24, y + 3.2, t, va="center", fontsize=10)
    a.add_patch(FancyBboxPatch((35, 11), 30, 8, boxstyle="round,pad=0.3", fc=GREEN, ec=GREEN))
    a.text(50, 15, "Sign in (HTTPS)", ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    a.text(50, 5.5, "Token issued after authentication - role: editor", ha="center", fontsize=8.5, color="#555")
    b = axes[1]
    b.add_patch(FancyBboxPatch((3, 3), 94, 52, boxstyle="round,pad=0.5", fc="#F8FAFC", ec=NAVY, lw=2))
    b.add_patch(FancyBboxPatch((3, 46), 94, 9, boxstyle="square,pad=0", fc=NAVY, ec=NAVY))
    b.text(50, 50.5, "Assignment3.docx  -  Shared Workspace", ha="center", color="white", fontsize=11, fontweight="bold")
    rows = [("Version", "Author", "Status"), ("v1", "asha", "Draft submitted"), ("v2", "asha", "Final + screenshot")]
    for i, r in enumerate(rows):
        for j, t in enumerate(r):
            b.text(8 + j * 30, 40 - i * 7, t, fontsize=9.5, fontweight="bold" if i == 0 else "normal", color=NAVY if i == 0 else "black")
    b.add_patch(FancyBboxPatch((8, 12), 56, 10, boxstyle="round,pad=0.3", fc="#FFF4E5", ec=ORANGE))
    b.text(10, 17, "Faculty: add API screenshot (Q3)", va="center", fontsize=9)
    b.add_patch(FancyBboxPatch((70, 12), 24, 10, boxstyle="round,pad=0.3", fc=TEAL, ec=TEAL))
    b.text(82, 17, "Share / Roles", ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
    b.text(50, 5.5, "Editor: edit - Viewer: read only - Owner: share + delete", ha="center", fontsize=8.5, color="#555")
    save(fig, "q6_mockup.png")


def q7():
    fig, ax = canvas(12.5, 6.4, "Q7 - Final Joint Design: SIMATS Cloud Project Hub")
    cols = [("Users", "Students - Faculty\nMentors - Guests", TEAL, 2), ("Client", "Browser - Mobile app\nPython API client", ORANGE, 22),
            ("Internet", "HTTPS / TLS 1.3\nCDN + DNS", NAVY, 42), ("Cloud Platform", "Identity (SSO + MFA)\nLoad balancer", GREEN, 62)]
    for t, s, c, x in cols:
        box(ax, x, 36, 18, 16, t, c, 11, sub=s)
    for x in (20.4, 40.4, 60.4):
        arrow(ax, (x, 44), (x + 1.5, 44))
    box(ax, 82, 36, 18, 16, "App / API", PURPLE, 11, sub="REST API\nproject logic")
    arrow(ax, (80.4, 44), (81.6, 44))
    box(ax, 102, 36, 20, 16, "Shared Resources", "#8E44AD", 11, sub="files - tasks - versions\ncomments - audit")
    arrow(ax, (100.4, 44), (101.6, 44))
    bands = [("Security layer: authentication - RBAC authorization - encryption in transit and at rest - audit logging", RED, 24),
             ("Collaboration layer: shared workspace - concurrent editing - version history - comments - notifications", TEAL, 14),
             ("Scalability layer: auto-scaling - managed storage - multi-region backup - monitoring", NAVY, 4)]
    for t, c, y in bands:
        ax.add_patch(FancyBboxPatch((2, y), 120, 7, boxstyle="round,pad=0.3", fc=c, ec="white", alpha=0.92))
        ax.text(62, y + 3.5, t, ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    save(fig, "q7_final_architecture.png")


if __name__ == "__main__":
    for f in (q1, q2, q3, q4, q5, q6, q6_mockup, q7):
        f()
