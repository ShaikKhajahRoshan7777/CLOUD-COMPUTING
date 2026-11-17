import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from educloud import parsers  # noqa: E402

SYSBENCH = """
CPU speed:
    events per second:   979.50

Latency (ms):
         min:                                    1.01
         avg:                                    1.02
         max:                                    3.12
         95th percentile:                        1.06
"""
STRESS = """stress-ng: info:  [123] setting to a 5 second run per stressor
stress-ng: info:  [123] stressor       bogo ops real time  usr time  sys time   bogo ops/s     bogo ops/s
stress-ng: info:  [123]                           (secs)    (secs)    (secs)   (real time) (usr+sys time)
stress-ng: info:  [123] vm                 55120      5.01      4.90      0.08     11001.80       11070.30
"""


class TestParsers(unittest.TestCase):
    def test_sysbench(self):
        r = parsers.parse_sysbench_cpu(SYSBENCH)
        self.assertEqual(r["cpu_eps"], 979.5)
        self.assertEqual(r["cpu_lat_p95_ms"], 1.06)

    def test_fio(self):
        fio = {"jobs": [{"read": {"io_bytes": 1, "iops": 1000, "bw_bytes": 4_000_000,
                                  "clat_ns": {"mean": 200000, "percentile": {"95.000000": 500000}}},
                         "write": {"io_bytes": 1, "iops": 400, "bw_bytes": 1_600_000,
                                   "clat_ns": {"mean": 300000, "percentile": {"95.000000": 700000}}}}]}
        r = parsers.parse_fio_json("fio: some warning\n" + json.dumps(fio))
        self.assertAlmostEqual(r["disk_iops"], 1400)
        self.assertAlmostEqual(r["disk_mbps"], 5.6)
        self.assertAlmostEqual(r["disk_lat_p95_ms"], 0.7)

    def test_iperf3(self):
        r = parsers.parse_iperf3_json(json.dumps({"end": {"sum_received": {"bits_per_second": 2.2e10}}}))
        self.assertAlmostEqual(r["net_gbps"], 22.0)

    def test_stress_ng(self):
        self.assertAlmostEqual(parsers.parse_stress_ng_vm(STRESS)["mem_bogo_ops_s"], 11001.80)

    def test_proc_stat(self):
        steal, total = parsers.parse_proc_stat("cpu  100 0 50 800 10 0 5 35 0 0")
        self.assertEqual(steal, 35)
        self.assertEqual(total, 1000)

    def test_bad_input_raises(self):
        with self.assertRaises(ValueError):
            parsers.parse_sysbench_cpu("garbage")


if __name__ == "__main__":
    unittest.main()
