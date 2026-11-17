"""Generates every diagram and graph used in the report -> ../figures/*.png"""
import json, os, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle
import model as M
plt.rcParams.update({"font.family": ["Liberation Serif", "DejaVu Serif"], "font.size": 9, "axes.grid": True, "grid.alpha": .3})
FIG = os.path.join(os.path.dirname(__file__), "..", "figures"); os.makedirs(FIG, exist_ok=True)
R = json.load(open(os.path.join(FIG, "..", "results", "experiments.json")))
RB = json.load(open(os.path.join(FIG, "..", "results", "real_bench.json")))
COL = {"KVM": "#1f4e79", "Docker": "#c55a11", "gVisor": "#548235", "Bare-metal": "#7f7f7f"}

def box(ax, x, y, w, h, txt, fc, tc="black", fs=8, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08", fc=fc, ec="#333", lw=.8))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=fs, color=tc, weight="bold" if bold else "normal")

def arch(name, title, hw, layers, boundary_txt, enforcer, fname, extra=None, bounds=(2,)):
    fig, ax = plt.subplots(figsize=(7.2, 4.1)); ax.set_xlim(0, 10); ax.set_ylim(0, 6.9); ax.axis("off")
    ax.set_title(title, fontsize=11, weight="bold", color="#1f3864")
    box(ax, .3, .2, 7.4, .8, hw, "#d9d9d9", fs=8.5, bold=True)
    y = 1.15
    for lab, fc, split in layers:
        h = .85
        if split:
            for i, t in enumerate(("T1: SIS / LMS", "T2: Dept / external")):
                box(ax, .3 + i * 3.75, y, 3.65, h, lab.replace("{t}", t), fc, fs=7.6)
        else: box(ax, .3, y, 7.4, h, lab, fc, bold=True, fs=8)
        y += h + .12
    ys = []
    for k in bounds:
        yb = 1.15 + k * .97 - .06; ys.append(yb)
        ax.plot([.15, 7.85], [yb, yb], "r--", lw=1.8)
        ax.text(7.95, yb + .05, "TRUST BOUNDARY", color="red", fontsize=7.5, weight="bold", va="bottom")
    ax.annotate(enforcer, xy=(7.7, ys[-1]), xytext=(7.95, 4.75), fontsize=7.4, color="#7030a0", va="top", arrowprops=dict(arrowstyle="->", color="#7030a0"))
    ax.text(7.95, 6.55, "Resource virtualization\n" + extra, fontsize=7.2, va="top", color="#1f3864", bbox=dict(fc="#eef3fa", ec="#9db7d9", boxstyle="round"))
    ax.text(.3, y + .02, boundary_txt, fontsize=7.6, style="italic", color="#444")
    fig.tight_layout(); fig.savefig(os.path.join(FIG, fname), dpi=200); plt.close(fig)

arch("A", "Approach A - Type-1 KVM/QEMU, hardware-assisted full virtualization", "HARDWARE: 64 cores (VT-x, EPT) | 512 GB RAM | NVMe SSD | 2 x 25 Gbps NIC",
     [("Host Linux + KVM kernel module (Type-1 hypervisor) | vhost-net, vhost-blk, Open vSwitch", "#b4c7e7", False),
      ("QEMU + virtio device model\n(one process per VM)", "#9dc3e6", True),
      ("Guest OS kernel\n({t})", "#c9e1b7", True),
      ("Runtime: JVM / Python", "#ffe699", True),
      ("Application: SIS / LMS / Spark", "#f8cbad", True)],
     "Each VM owns a private kernel; EPT page tables stop cross-VM memory access.", "Enforced by VT-x/EPT + KVM\n(small, hardware-backed TCB)", "arch_A_kvm.png",
     "CPU: VT-x, vCPU = thread\nRAM: EPT/NPT + balloon\nDisk: virtio-blk / qcow2\nNet: virtio-net + vhost + OVS", bounds=(2,))
arch("B", "Approach B - OS-level virtualization (Docker / runc containers)", "HARDWARE: 64 cores | 512 GB RAM | NVMe SSD | 2 x 25 Gbps NIC",
     [("SHARED Host Linux kernel: namespaces | cgroups v2 | seccomp | AppArmor | overlayfs | veth + bridge + netfilter", "#f4b183", False),
      ("containerd / runc\n(container runtime)", "#9dc3e6", True),
      ("Container user-space: libs + binaries\n({t})", "#c9e1b7", True),
      ("Runtime: JVM / Python", "#ffe699", True),
      ("Application: SIS / LMS / Spark", "#f8cbad", True)],
     "No guest kernel: every container issues system calls to the one host kernel.", "Enforced by kernel namespaces,\ncgroups, seccomp (large shared TCB)", "arch_B_docker.png",
     "CPU: CFS cgroup quota/shares\nRAM: cgroup memory limit\nDisk: overlayfs + volumes\nNet: veth pair -> bridge/NAT", bounds=(2,))
arch("C", "Approach C - Sandboxed container runtime (gVisor runsc, KVM platform)", "HARDWARE: 64 cores (VT-x, EPT) | 512 GB RAM | NVMe SSD | 2 x 25 Gbps NIC",
     [("Host Linux kernel (exposed to Sentry through ~70 filtered syscalls) + KVM platform", "#b4c7e7", False),
      ("runsc: SENTRY (user-space kernel)\n+ GOFER (file proxy) + netstack", "#d5a6e6", True),
      ("Container user-space: libs + binaries\n({t})", "#c9e1b7", True),
      ("Runtime: JVM / Python", "#ffe699", True),
      ("Application: exam-upload sandbox", "#f8cbad", True)],
     "Application syscalls never reach the host kernel directly: the Sentry re-implements them.", "Enforced by Sentry interception +\nseccomp on Sentry (small host surface)", "arch_C_gvisor.png",
     "CPU: Sentry tasks on host threads\nRAM: Sentry memory manager\nDisk: Gofer / directfs\nNet: user-space netstack", bounds=(1, 2))

# ---- final architecture (Task 12) -------------------------------------------
fig, ax = plt.subplots(figsize=(7.2, 4.4)); ax.set_xlim(0, 10); ax.set_ylim(0, 7); ax.axis("off")
ax.set_title("Redesigned EduCloud: tenant-separated host pools (Task 12)", fontsize=11, weight="bold", color="#1f3864")
pools = [("POOL S\nSIS / LMS / Exam portal\n7 hosts - KVM VMs\nSMT on, dedicated hosts\nTrusted internal tenants", "#bdd7ee", .15),
         ("POOL D\nDepartmental research\n8 hosts - KVM VMs\n(containers inside VMs)\nSemi-trusted internal tenants", "#c6e0b4", 3.4),
         ("POOL E\nExternal Spark / Hadoop\n6 hosts - KVM VMs, SMT OFF\nSR-IOV NIC for shuffle/HDFS\nUntrusted external tenants", "#f8cbad", 6.65)]
for t, c, x in pools: box(ax, x, 3.2, 3.1, 2.6, t, c, fs=8.2, bold=False)
box(ax, .15, 1.85, 9.6, 1.0, "Management plane: signed images (registry) | encrypted live migration (TLS/IPsec)\npatch automation | OVS micro-segmentation | monitoring (steal, exits, p95)", "#e7e6e6", fs=8)
box(ax, .15, .4, 9.6, 1.0, "Shared storage backend: per-tenant encrypted volumes, separate VLAN/VXLAN per pool\n2 x 25 Gbps fabric", "#d9d9d9", fs=8)
for x in (3.27, 6.52): ax.plot([x, x], [3.0, 6.0], "r--", lw=1.8)
ax.text(5, 6.3, "Red dashed lines = hard trust boundaries (no co-residency between pools)", ha="center", color="red", fontsize=8)
fig.tight_layout(); fig.savefig(os.path.join(FIG, "arch_final_pools.png"), dpi=200); plt.close(fig)

def series(key, app, n=None): return [r for r in R[key] if r["app"] == app]

# ---- graph 1: CPU throughput vs instances -------------------------------------
fig, ax = plt.subplots(figsize=(6.2, 3.4))
for app in ("Bare-metal", "KVM", "Docker", "gVisor"):
    s = series("cpu", app); ax.errorbar([r["n"] for r in s], [r["rel"] for r in s], yerr=[r["std"] for r in s], marker="o", capsize=3, label=app, color=COL[app])
ax.set_xscale("log", base=2); ax.set_xticks(M_N := [1, 2, 4, 8, 16]); ax.set_xticklabels(M_N)
ax.set_xlabel("Co-located instances (4 vCPU each, 16-pCPU test host)"); ax.set_ylabel("Per-instance CPU throughput\n(relative to bare-metal, n = 1)")
ax.set_title("Graph 1: CPU-bound throughput vs number of instances (mean +/- SD, 10 runs)", fontsize=9.5); ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph1_cpu.png"), dpi=200); plt.close(fig)

# ---- graph 2: p95 latency vs instances ----------------------------------------
fig, ax = plt.subplots(figsize=(6.2, 3.4))
for app in ("Bare-metal", "KVM", "Docker", "gVisor"):
    s = series("lat", app); ax.errorbar([r["n"] for r in s], [r["p95"] for r in s], yerr=[r["p95_sd"] for r in s], marker="s", capsize=3, label=app, color=COL[app])
ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xticks(M_N); ax.set_xticklabels(M_N)
ax.set_xlabel("Co-located instances"); ax.set_ylabel("95th-percentile request latency (ms)"); ax.set_title("Graph 2: Web-request p95 latency vs instances (registration-type load)", fontsize=9.5)
ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph2_latency.png"), dpi=200); plt.close(fig)

# ---- graph 3: network + disk per instance ------------------------------------
fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.2))
for app in ("KVM", "Docker", "gVisor"):
    s = series("net", app); axs[0].errorbar([r["n"] for r in s], [r["gbps"] for r in s], yerr=[r["sd"] for r in s], marker="o", capsize=3, label=app, color=COL[app])
    s = series("disk", app); axs[1].errorbar([r["n"] for r in s], [r["kiops"] for r in s], yerr=[r["sd"] for r in s], marker="o", capsize=3, label=app, color=COL[app])
for a_, yl, t in ((axs[0], "Gbit/s per instance (iperf3, 1500 B)", "(a) Network"), (axs[1], "kIOPS per instance (fio, 4 KiB)", "(b) Disk")):
    a_.set_xscale("log", base=2); a_.set_xticks(M_N); a_.set_xticklabels(M_N); a_.set_yscale("log"); a_.set_xlabel("Co-located instances"); a_.set_ylabel(yl); a_.set_title(t, fontsize=9.5); a_.legend(fontsize=8)
fig.suptitle("Graph 3: Shared-device throughput per instance", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph3_io.png"), dpi=200); plt.close(fig)

# ---- graph 4: noisy neighbour -------------------------------------------------
fig, ax = plt.subplots(figsize=(6.0, 3.2)); x = np.arange(3); nz = R["noisy"]
ax.bar(x - .18, [r["quiet"] for r in nz], .36, yerr=[r["quiet_sd"] for r in nz], capsize=3, label="Quiet neighbours", color="#9dc3e6")
ax.bar(x + .18, [r["noisy"] for r in nz], .36, yerr=[r["noisy_sd"] for r in nz], capsize=3, label="With noisy neighbour", color="#f4b183")
ax.set_xticks(x); ax.set_xticklabels([r["app"] for r in nz]); ax.set_yscale("log"); ax.set_ylabel("Victim p95 latency (ms), n = 16"); ax.legend()
for i, r in enumerate(nz): ax.text(i + .18, r["noisy"] * 1.25, "x%.2f" % r["ratio"], ha="center", fontsize=8, weight="bold")
ax.set_title("Graph 4: Noisy-neighbour interference", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph4_noisy.png"), dpi=200); plt.close(fig)

# ---- graph 5: density by scenario (model) ------------------------------------
fig, ax = plt.subplots(figsize=(6.4, 3.3)); sc = ["best", "typical", "peak3x", "worst"]; w = .26
for i, a in enumerate(M.APPROACHES):
    ax.bar(np.arange(4) + (i - 1) * w, [M.density(a, s)["n"] for s in sc], w, label=a.short, color=COL[a.short])
ax.set_xticks(range(4)); ax.set_xticklabels(["Best", "Typical", "Peak (3x)", "Worst"]); ax.set_ylabel("Instances per host meeting <= 10 % degradation")
ax.axhline(25, color="red", ls="--", lw=1); ax.text(3.35, 25.8, "25 = today's average", color="red", fontsize=7.5, ha="right")
ax.set_title("Graph 5: Modelled density per host under the 10 % SLO", fontsize=9.5); ax.legend(); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph5_density.png"), dpi=200); plt.close(fig)

# ---- graph 6: theory vs experiment -------------------------------------------
fig, ax = plt.subplots(figsize=(4.6, 3.8))
for app in ("KVM", "Docker", "gVisor"):
    s = series("cpu", app); ax.scatter([r["model"] for r in s], [r["rel"] for r in s], label=app, color=COL[app], s=28)
ax.plot([0, 1], [0, 1], "k--", lw=1, label="y = x (perfect model)"); ax.set_xlabel("Model prediction  Pi = (1 - steal)(1 - o)"); ax.set_ylabel("Emulated measurement (relative)")
ax.set_title("Graph 6: CPU model vs experiment", fontsize=9.5); ax.legend(fontsize=8); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph6_model_vs_exp.png"), dpi=200); plt.close(fig)

# ---- graph 7: isolation vs density trade-off ---------------------------------
fig, ax = plt.subplots(figsize=(6.2, 3.5))
for r in M.optimise(wl="typical"):
    if r["n"] == 0: continue
    mk = "o" if not r["dedicated"] else "D"; ax.scatter(r["n"], r["iso"], color=COL[r["approach"]], marker=mk, s=70 if r["smt_off"] else 45, edgecolor="k", linewidth=1.2 if r["smt_off"] else .3)
ax.axhline(.75, color="red", ls="--"); ax.text(ax.get_xlim()[0] + .3, .755, "SIS isolation requirement I >= 0.75", color="red", fontsize=8)
ax.set_xlabel("Density (instances per host at <= 10 % degradation)"); ax.set_ylabel("Isolation score I = 1 - residual risk")
ax.set_title("Graph 7: Isolation-performance trade-off (o shared, D dedicated pool, large/outlined = SMT off)", fontsize=8.8)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], marker="o", ls="", color=COL[k], label=k) for k in ("KVM", "Docker")], fontsize=8, loc="lower left"); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph7_tradeoff.png"), dpi=200); plt.close(fig)

# ---- graph 8: mitigation cost -------------------------------------------------
fig, ax = plt.subplots(figsize=(6.2, 3.2)); ms = ["M6 KPTI+retpoline", "M1 SMT off"]; w = .26
for i, app in enumerate(("KVM", "Docker", "gVisor")):
    ax.bar(np.arange(2) + (i - 1) * w, [next(r["thr_cost"] for r in R["mitig"] if r["app"] == app and r["mit"] == m) for m in ms], w, label=app, color=COL[app])
ax.set_xticks(range(2)); ax.set_xticklabels(["M6 KPTI + retpoline", "M1 Disable SMT"]); ax.set_ylabel("Throughput cost (%)"); ax.legend()
ax.set_title("Graph 8: Measured cost of security mitigations (n = 8, typical load)", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph8_mitigation.png"), dpi=200); plt.close(fig)

# ---- graph 9: real benchmark -------------------------------------------------
fig, ax = plt.subplots(figsize=(6.0, 3.2)); n = [1, 2, 4, 8, 16]
for k, c in (("cpu", "#1f4e79"), ("disk", "#c55a11"), ("net", "#548235"), ("mem", "#7030a0")):
    ax.plot(n, [r["rel"] for r in RB[k]], marker="o", color=c, label=k.upper() + " (real)")
ax.plot(n, [1 / x for x in n], "k--", label="ideal 1/n share (model)"); ax.set_xscale("log", base=2); ax.set_yscale("log"); ax.set_xticks(n); ax.set_xticklabels(n)
ax.set_xlabel("Co-located worker processes on %d logical CPU" % RB["cpus"]); ax.set_ylabel("Per-process throughput (relative to n = 1)"); ax.legend(fontsize=8)
ax.set_title("Graph 9: Real micro-benchmark on the host machine", fontsize=9.5); fig.tight_layout(); fig.savefig(os.path.join(FIG, "graph9_real_bench.png"), dpi=200); plt.close(fig)
print("figures written:", sorted(os.listdir(FIG)))
