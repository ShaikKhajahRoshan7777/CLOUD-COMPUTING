import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from educloud import models, stats, tradeoff, mitigation, day4  # noqa: E402
from educloud.config import APPROACHES, HOST  # noqa: E402


class TestCPU(unittest.TestCase):
    def test_effective_cpu_matches_brief_table(self):
        self.assertAlmostEqual(models.effective_cpu(1, 0.05), 0.95)
        self.assertAlmostEqual(models.effective_cpu(4, 0.05, 0.10), 0.21375)   # worked example
        self.assertAlmostEqual(models.effective_cpu(8, 0.02), 0.1225)

    def test_vm_exit_cost(self):
        self.assertAlmostEqual(models.exit_overhead_fraction(100_000, 1.5), 0.15)
        self.assertAlmostEqual(models.exits_per_s_for_overhead(0.05), 33333.33, places=1)

    def test_steal_and_perf(self):
        self.assertEqual(models.steal_fraction(64, 1.0, 64), 0.0)
        self.assertAlmostEqual(models.steal_fraction(128, 1.0, 64), 0.5)
        self.assertAlmostEqual(models.perf_factor(128, 1.0, 64, 0.05), 0.475)

    def test_cpu_density_meets_sla(self):
        n = models.max_instances_cpu(64, 1.0, 0.05, 0.10)
        self.assertGreaterEqual(models.perf_factor(n, 1.0, 64, 0.05), 0.90 - 1e-9)
        self.assertLess(models.perf_factor(n + 1, 1.0, 64, 0.05), 0.90)

    def test_overhead_above_sla_gives_zero(self):
        self.assertEqual(models.max_instances_cpu(64, 0.5, 0.12, 0.10), 0)


class TestMemoryAndNetwork(unittest.TestCase):
    def test_memory_bounds_from_brief(self):
        self.assertEqual(models.max_instances_mem(HOST, 0, reserve=0.0), 64)
        self.assertEqual(models.max_instances_mem(HOST, 0), 57)

    def test_network_share(self):
        self.assertAlmostEqual(models.net_share_gbps(8, 25), 3.125)
        self.assertAlmostEqual(models.net_share_gbps(16, 25), 1.5625)

    def test_density_reports_limiting_resource(self):
        d = models.density(HOST, APPROACHES["vm"], u=0.5)
        self.assertEqual(d["N_host"], min(d["N_cpu"], d["N_memory"], d["N_network"], d["N_storage"]))

    def test_latency_model(self):
        mean, p95 = models.mm1_latency_ms(10, 0.5)
        self.assertAlmostEqual(mean, 20)
        self.assertAlmostEqual(p95, 20 * math.log(20))
        self.assertTrue(math.isinf(models.mm1_latency_ms(10, 1.0)[0]))
        self.assertEqual(models.swap_service_factor(100, 200), 1.0)


class TestTradeoffMitigationDay4(unittest.TestCase):
    def test_container_never_feasible_for_sis(self):
        best = tradeoff.search(tradeoff.Scenario())
        self.assertTrue(all(not r["feasible"] for r in best if r["approach"] == "container"))
        self.assertTrue(best[0]["feasible"])

    def test_smt_off_planning_cores(self):
        self.assertAlmostEqual(HOST.cores * 0.9, 57.6)

    def test_migration_cost_is_transient(self):
        m = next(x for x in mitigation.MITIGATIONS if "migration" in x.name)
        r = mitigation.evaluate(m)
        self.assertEqual(r["N_host_before"], r["N_host_after"])
        self.assertTrue(r["transient"])

    def test_day4_modified_beats_original(self):
        a = day4.Day4Assumptions()
        orig, new = day4.shared_design(a), day4.modified_design(a)
        self.assertFalse(orig["meets_SLA"])
        self.assertTrue(new["meets_SLA"])
        self.assertTrue(day4.pool_sizes(a)["fits_in_16_hosts"])


class TestStats(unittest.TestCase):
    def test_mean_std_percentile(self):
        xs = [2, 4, 4, 4, 5, 5, 7, 9]
        self.assertAlmostEqual(stats.mean(xs), 5)
        self.assertAlmostEqual(stats.std(xs), 2.138089935, places=6)
        self.assertAlmostEqual(stats.percentile(list(range(1, 101)), 95), 95.05)

    def test_degradation_and_ape(self):
        self.assertAlmostEqual(stats.degradation_pct(10000, 9000), 10.0)
        self.assertAlmostEqual(stats.ape_pct(9200, 9000), 2.1739, places=3)   # matches the brief's example


if __name__ == "__main__":
    unittest.main()
