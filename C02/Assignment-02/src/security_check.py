"""
Security-property validation (Task 8): inspect isolation primitives that EduCloud relies on.
Works on any Linux host / container / VM.  Run:  python security_check.py
"""
import glob, os, platform, subprocess

def read(p, default="n/a"):
    try: return open(p).read().strip()
    except Exception: return default

print("=" * 72); print("EduCloud isolation & mitigation validation"); print("=" * 72)
print("1) KERNEL SHARING  (containers share the host kernel, VMs do not)")
print("   kernel release :", platform.release()); print("   machine        :", platform.machine())
cpuinfo = read("/proc/cpuinfo", "")
print("   hypervisor flag:", "PRESENT (this system is itself a guest/VM)" if "hypervisor" in cpuinfo else "absent (bare metal or flag hidden)")
print("\n2) NAMESPACE ISOLATION  (/proc/self/ns)")
for ns in sorted(glob.glob("/proc/self/ns/*")):
    try: print("   %-8s -> %s" % (os.path.basename(ns), os.readlink(ns)))
    except Exception as e: print("   %-8s -> unreadable (%s)" % (os.path.basename(ns), e))
print("\n3) CGROUP RESOURCE LIMITS")
cg = read("/proc/self/cgroup"); print("   membership     :", cg.splitlines()[0] if cg != "n/a" else cg)
for f in ("/sys/fs/cgroup/cpu.max", "/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/pids.max"):
    print("   %-26s: %s" % (f, read(f)))
print("\n4) PROCESS CONFINEMENT")
for line in read("/proc/self/status", "").splitlines():
    if line.split(":")[0] in ("Seccomp", "NoNewPrivs", "CapEff", "Uid"): print("  ", line.replace("\t", " "))
print("\n5) CPU VULNERABILITY MITIGATIONS (side-channel defences)")
vdir = "/sys/devices/system/cpu/vulnerabilities"
if os.path.isdir(vdir):
    for f in sorted(os.listdir(vdir)): print("   %-26s: %s" % (f, read(os.path.join(vdir, f))[:60]))
else: print("   /sys/devices/system/cpu/vulnerabilities not exposed in this environment")
print("   SMT active     :", read("/sys/devices/system/cpu/smt/active"), "(1 = SMT on, 0 = off)")
print("\n6) VERDICT")
print("   Kernel shared with other tenants on this host: YES for containers (one kernel); NO for VMs (one kernel per guest)")
print("   Isolation enforcers: namespaces + cgroups + seccomp (containers); VT-x/EPT + hypervisor (VMs); Sentry user-space kernel (gVisor)")
