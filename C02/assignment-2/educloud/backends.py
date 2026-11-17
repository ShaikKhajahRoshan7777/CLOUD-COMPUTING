"""Execution back-ends: where the N co-located instances actually run.

  baremetal : N plain processes on the host (baseline)
  docker    : Docker / Podman containers (runc)
  gvisor    : Docker with --runtime=runsc  (sandboxed container)
  kata      : Docker with --runtime=kata   (micro-VM per container)
  kvm       : pre-defined libvirt guests reached over SSH (virsh start/destroy for start-up time)

Every instance gets the same allocation (1 vCPU, 2 GB RAM by default).
"""
import shlex
import subprocess
import time
from dataclasses import dataclass, field

from . import parsers


def sh(cmd: str, timeout: float = 600, check: bool = False) -> subprocess.CompletedProcess:
    """Run a shell command with stderr merged into stdout (stress-ng writes its table to stderr)."""
    return subprocess.run(cmd + " 2>&1", shell=True, capture_output=True, text=True,
                          timeout=timeout, check=check)


@dataclass
class Instance:
    name: str
    startup_s: float = float("nan")
    extra: dict = field(default_factory=dict)


class Backend:
    key = "base"
    data_dir = "/data"

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.instances: list[Instance] = []

    def start(self, n: int) -> list[Instance]: raise NotImplementedError
    def exec(self, inst: Instance, cmd: str, timeout: float = 600) -> str: raise NotImplementedError
    def stop(self) -> None: pass
    def memory_mb(self, inst: Instance) -> float: return float("nan")

    def read_steal(self, inst: Instance) -> tuple[float, float]:
        out = self.exec(inst, "head -1 /proc/stat", timeout=30)
        return parsers.parse_proc_stat(out.strip().splitlines()[0]) if not self.dry_run else (0.0, 1.0)

    def _run(self, cmd: str, timeout: float = 600) -> str:
        if self.dry_run:
            print(f"[dry-run] {cmd}")
            return ""
        return sh(cmd, timeout).stdout


class BareMetal(Backend):
    key = "baremetal"

    def __init__(self, dry_run=False, data_dir="/tmp/educloud-bare"):
        super().__init__(dry_run)
        self.data_dir = data_dir

    def start(self, n):
        self._run(f"mkdir -p {self.data_dir}")
        self.instances = [Instance(f"bare{i}", 0.0) for i in range(n)]
        return self.instances

    def exec(self, inst, cmd, timeout=600):
        return self._run(cmd.replace("/data", self.data_dir), timeout)


class Docker(Backend):
    key = "docker"
    runtime: str | None = None

    def __init__(self, dry_run=False, image="educloud-bench:latest", cpus=1, mem="2g",
                 host_dir="/var/tmp/educloud", engine="docker"):
        super().__init__(dry_run)
        self.image, self.cpus, self.mem, self.host_dir, self.engine = image, cpus, mem, host_dir, engine

    def start(self, n):
        self.instances = []
        rt = f"--runtime={self.runtime}" if self.runtime else ""
        for i in range(n):
            name = f"educloud-{self.key}-{i}"
            self._run(f"{self.engine} rm -f {name}")
            self._run(f"mkdir -p {self.host_dir}/{name}")
            t0 = time.perf_counter()
            self._run(f"{self.engine} run -d --name {name} --cpus={self.cpus} --memory={self.mem} "
                      f"--pids-limit=512 {rt} -v {self.host_dir}/{name}:/data {self.image} sleep infinity")
            while not self.dry_run:                       # ready = first successful exec
                if sh(f"{self.engine} exec {name} true", 60).returncode == 0:
                    break
                time.sleep(0.05)
                if time.perf_counter() - t0 > 120:
                    raise RuntimeError(f"{name} did not become ready")
            self.instances.append(Instance(name, time.perf_counter() - t0))
        return self.instances

    def exec(self, inst, cmd, timeout=600):
        return self._run(f"{self.engine} exec {inst.name} sh -c {shlex.quote(cmd)}", timeout)

    def memory_mb(self, inst):
        if self.dry_run:
            return float("nan")
        out = sh(f"{self.engine} stats --no-stream --format '{{{{.MemUsage}}}}' {inst.name}").stdout.strip()
        try:                                              # e.g. "12.5MiB / 2GiB"
            used = out.split("/")[0].strip()
            for suf, mul in (("GiB", 1024), ("MiB", 1), ("KiB", 1 / 1024), ("B", 1 / 1048576)):
                if used.endswith(suf):
                    return float(used[:-len(suf)]) * mul
        except ValueError:
            pass
        return float("nan")

    def stop(self):
        for inst in self.instances:
            self._run(f"{self.engine} rm -f {inst.name}")


class GVisor(Docker):
    key = "gvisor"
    runtime = "runsc"


class Kata(Docker):
    key = "kata"
    runtime = "kata"          # name registered in /etc/docker/daemon.json (kata-runtime / io.containerd.kata.v2)


class KVM(Backend):
    """libvirt guests (already defined, 1 vCPU / 2 GB, cloud-init user + SSH key, tools installed)."""
    key = "kvm"

    def __init__(self, dry_run=False, domains=(), ips=(), user="ubuntu", ssh_opts="-o StrictHostKeyChecking=no -o ConnectTimeout=5"):
        super().__init__(dry_run)
        self.domains, self.ips, self.user, self.ssh_opts = list(domains), list(ips), user, ssh_opts

    def start(self, n):
        if len(self.domains) < n or len(self.ips) < n:
            raise SystemExit(f"KVM backend needs at least {n} --kvm-domains and --kvm-ips")
        self.instances = []
        for dom, ip in zip(self.domains[:n], self.ips[:n]):
            self._run(f"virsh destroy {dom}")
            t0 = time.perf_counter()
            self._run(f"virsh start {dom}")
            while not self.dry_run:
                if sh(f"ssh {self.ssh_opts} {self.user}@{ip} true", 20).returncode == 0:
                    break
                time.sleep(0.5)
                if time.perf_counter() - t0 > 300:
                    raise RuntimeError(f"{dom} did not become reachable over SSH")
            self.instances.append(Instance(dom, time.perf_counter() - t0, {"ip": ip}))
        return self.instances

    def exec(self, inst, cmd, timeout=600):
        cmd = cmd.replace("/data", "/var/tmp")
        return self._run(f"ssh {self.ssh_opts} {self.user}@{inst.extra['ip']} {shlex.quote(cmd)}", timeout)

    def memory_mb(self, inst):
        if self.dry_run:
            return float("nan")
        out = sh(f"virsh domstats --balloon {inst.name}").stdout
        for line in out.splitlines():
            if "balloon.rss=" in line:                    # KiB resident on the host
                return float(line.split("=")[1]) / 1024
        return float("nan")

    def stop(self):
        for inst in self.instances:
            self._run(f"virsh destroy {inst.name}")


BACKENDS = {"baremetal": BareMetal, "docker": Docker, "gvisor": GVisor, "kata": Kata, "kvm": KVM}
