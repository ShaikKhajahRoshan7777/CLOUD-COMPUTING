"""
Real micro-benchmarks executed on the machine running this script (Task 8 / 9 baseline).
n co-located worker processes (n = 1, 2, 4, 8, 16) run identical CPU, memory, disk and
network tests; this is the real-hardware counterpart of the emulated test-bed and also
validates the CPU-sharing (steal) equation  per-instance share = min(1, cores / n).
Run:  python real_bench.py
"""
import json, multiprocessing as mp, os, platform, resource, socket, statistics as st, tempfile, threading, time
import numpy as np

NS, REPS = [1, 2, 4, 8, 16], 3


def w_cpu(q, bar):
    bar.wait(); t0 = time.perf_counter(); c0 = time.process_time(); n = 0
    while time.perf_counter() - t0 < 1.0:
        x = 0
        for i in range(20000): x += i * i % 7          # one "event" = 20 000 loop iterations
        n += 1
    ru = resource.getrusage(resource.RUSAGE_SELF)
    q.put((n / (time.perf_counter() - t0), (time.process_time() - c0) / (time.perf_counter() - t0), ru.ru_nvcsw + ru.ru_nivcsw))


def w_mem(q, bar):
    a = np.ones(8_000_000); b = np.empty_like(a); bar.wait(); t0 = time.perf_counter(); k = 0
    while time.perf_counter() - t0 < 1.0: np.copyto(b, a); k += 1
    q.put((k * a.nbytes * 2 / (time.perf_counter() - t0) / 1e9,))   # GB/s (read + write)


def w_disk(q, bar):
    d = tempfile.mkdtemp(); p = os.path.join(d, "f"); blob = os.urandom(1 << 20); bar.wait(); t0 = time.perf_counter(); n = 0
    with open(p, "wb") as f:
        while time.perf_counter() - t0 < 1.0:
            f.write(blob); f.flush(); os.fsync(f.fileno()); n += 1
    q.put((n / (time.perf_counter() - t0),)); os.remove(p)           # MiB/s synced write


def w_net(q, bar):
    srv = socket.socket(); srv.bind(("127.0.0.1", 0)); srv.listen(1); port = srv.getsockname()[1]; got = [0]
    def rx():
        c, _ = srv.accept()
        while True:
            d = c.recv(1 << 20)
            if not d: break
            got[0] += len(d)
    th = threading.Thread(target=rx, daemon=True); th.start()
    cl = socket.create_connection(("127.0.0.1", port)); blob = b"x" * (1 << 18); bar.wait(); t0 = time.perf_counter(); sent = 0
    while time.perf_counter() - t0 < 1.0: cl.sendall(blob); sent += len(blob)
    cl.close(); th.join(2); q.put((sent * 8 / (time.perf_counter() - t0) / 1e9,))   # Gbit/s loopback


def run(fn, n):
    q = mp.Queue(); bar = mp.Barrier(n); ps = [mp.Process(target=fn, args=(q, bar)) for _ in range(n)]
    [p.start() for p in ps]; r = [q.get() for _ in ps]; [p.join() for p in ps]
    return [sum(x[i] for x in r) / n for i in range(len(r[0]))]


def main():
    print("Host:", platform.platform(), "| logical CPUs:", os.cpu_count(), "| Python", platform.python_version())
    out = {"cpus": os.cpu_count(), "cpu": [], "mem": [], "disk": [], "net": []}
    base = {}
    for name, fn in (("cpu", w_cpu), ("mem", w_mem), ("disk", w_disk), ("net", w_net)):
        print("\n== %s test ==" % name.upper())
        for n in NS:
            rows = [run(fn, n) for _ in range(REPS)]
            m = [st.mean(r[i] for r in rows) for i in range(len(rows[0]))]; s = st.stdev(rows[i][0] for i in range(REPS))
            base.setdefault(name, m[0]); rel = m[0] / base[name]
            rec = dict(n=n, mean=m[0], sd=s, rel=rel, cpu_share=m[1] if name == "cpu" else None, ctx=m[2] if name == "cpu" else None)
            out[name].append(rec)
            extra = "  cpu-share=%.2f  ctx-switches=%d" % (m[1], m[2]) if name == "cpu" else ""
            print("n=%2d  throughput=%10.2f +/- %7.2f   relative-to-n1=%.3f%s" % (n, m[0], s, rel, extra))
    json.dump(out, open(os.path.join(os.path.dirname(__file__), "..", "results", "real_bench.json"), "w"), indent=1)
    print("\nsaved results/real_bench.json")


if __name__ == "__main__":
    main()
