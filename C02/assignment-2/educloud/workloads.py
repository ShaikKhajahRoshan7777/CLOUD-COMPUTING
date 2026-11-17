"""Benchmark command lines - identical for every approach (fairness requirement of Task 8)."""


def cpu(duration: int) -> str:
    return f"sysbench cpu --cpu-max-prime=20000 --threads=1 --time={duration} run"


def disk(duration: int, path: str = "/data", direct: bool = True) -> str:
    return (f"fio --name=educloud --filename={path}/fio-test.dat --size=512M --rw=randrw "
            f"--rwmixread=70 --bs=4k --iodepth=16 --direct={1 if direct else 0} --runtime={duration} "
            f"--time_based --group_reporting --output-format=json")


def memory(duration: int) -> str:
    return f"stress-ng --vm 1 --vm-bytes 512M --vm-method all --timeout {duration}s --metrics-brief"


def network(server: str, port: int, duration: int) -> str:
    return f"iperf3 -c {server} -p {port} -t {duration} -P 4 -J"


def noise(kind: str, duration: int, path: str = "/data") -> str | None:
    """Noisy-neighbour load generators."""
    if kind == "cpu":
        return f"stress-ng --cpu 1 --timeout {duration}s"
    if kind == "mem":
        return f"stress-ng --vm 1 --vm-bytes 1G --vm-method all --timeout {duration}s"
    if kind == "disk":
        return (f"fio --name=noise --filename={path}/noise.dat --size=1G --rw=randwrite --bs=4k "
                f"--iodepth=64 --direct=1 --runtime={duration} --time_based --output-format=json")
    return None
