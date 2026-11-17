"""Task 12 - Day-4 design challenge: re-evaluate and adapt (external Spark/Hadoop tenants, 3x peak, live migration)."""
import math, json
import model as M

SIS_N, DEPT_N, SPARK_N, HOSTS = 150, 250, 96, 16      # assumed instance mix (400 existing + 96 external Spark workers)

def analyse():
    out = {}
    # A. Impact: original design = one shared KVM pool, SMT on, all tenants mixed
    pk = M.density(M.A, "peak3x", mit=M.mit_params(M.ALWAYS_ON))
    out["orig_peak_density"] = pk
    out["orig_hosts_needed_400"] = math.ceil(400 / pk["n"])
    out["orig_risk"] = M.risk("A", M.ALWAYS_ON)
    out["orig_risk_external"] = M.risk("A", M.ALWAYS_ON)       # same hosts: external tenants share them
    # B. Big-data profile on the old design (VM vNIC path, 1500 B packets, 2 Gbit/s per worker)
    bd = M.density(M.A, "bigdata", b_req=2e9, S=1500, mit=M.mit_params(M.ALWAYS_ON))
    out["bigdata_vm_vnic"] = bd
    # C. Redesign: three host pools
    mS = list(M.ALWAYS_ON) + ["M2 Dedicated hosts (SIS pool)"]
    dS = M.density(M.A, "peak3x", mit=M.mit_params(mS)); HS = math.ceil(SIS_N / dS["n"])
    mE = list(M.ALWAYS_ON) + ["M1 Disable SMT", "M2 Dedicated hosts (SIS pool)"]
    f = 1 / M.GAMMA
    eN = M.density(M.A, "bigdata", f=f, D=0.25, b_req=2e9, S=1500, mit=M.mit_params(mE))
    # SR-IOV: virtual function bypasses vhost; the CPU path no longer limits the NIC -> line goodput, 2 NICs/host assumed
    n_io_sriov = int(2 * M.LINE_BPS * 1500 / (1500 + M.HDR) // 2e9)
    nE = min(eN["n_cpu"], eN["n_mem"], n_io_sriov); HE = math.ceil(SPARK_N / nE)
    dD = M.density(M.A, "typical", mit=M.mit_params(M.ALWAYS_ON)); HD = math.ceil(DEPT_N / dD["n"])
    out["pool_S"] = dict(n=dS["n"], hosts=HS, risk=M.risk("A", mS), limit=dS["limit"])
    out["pool_E"] = dict(n=nE, hosts=HE, n_cpu=eN["n_cpu"], n_io_vnic=eN["n_io"], n_io_sriov=n_io_sriov, risk=M.risk("A", mE))
    out["pool_D"] = dict(n=dD["n"], hosts=HD, risk=M.risk("A", M.ALWAYS_ON))
    out["total_hosts"] = HS + HE + HD
    out["available"] = HOSTS
    out["deficit"] = out["total_hosts"] - HOSTS
    dSo = M.density(M.A, "best", mit=M.mit_params(mS)); dDo = M.density(M.A, "best", mit=M.mit_params(M.ALWAYS_ON))
    out["offpeak"] = dict(S=math.ceil(SIS_N / dSo["n"]), D=math.ceil(DEPT_N / dDo["n"]), E=HE)
    out["offpeak"]["total"] = sum(out["offpeak"].values())
    # peak-week policy: preempt batch jobs -> E pool hosts re-assigned to S pool
    out["peak_policy_hosts"] = HS + HD
    return out

if __name__ == "__main__":
    r = analyse(); print(json.dumps(r, indent=1, default=str)); json.dump(r, open("../results/design.json", "w"), indent=1)
