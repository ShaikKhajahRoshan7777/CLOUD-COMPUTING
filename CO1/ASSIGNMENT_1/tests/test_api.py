"""Functional tests for the Smart Campus API  (run:  python -m unittest -v tests.test_api)"""
import unittest

from app.app import app


class SmartCampusApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_returns_200(self):
        r = self.client.get("/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["status"], "UP")

    def test_result_lookup_success_200(self):
        r = self.client.get("/api/v1/results/SIM2201001")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["name"], "Aarav Kumar")

    def test_result_lookup_failure_404(self):
        r = self.client.get("/api/v1/results/SIM0000000")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json()["error"], "STUDENT_NOT_FOUND")

    def test_fee_payment_success_201(self):
        r = self.client.post("/api/v1/fees/payment",
                             json={"reg_no": "SIM2201001", "amount": 5000, "mode": "UPI"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["status"], "SUCCESS")

    def test_fee_payment_invalid_400(self):
        r = self.client.post("/api/v1/fees/payment", json={"reg_no": "SIM2201001", "amount": -1, "mode": "UPI"})
        self.assertEqual(r.status_code, 400)

    def test_fee_payment_exceeds_due_422(self):
        r = self.client.post("/api/v1/fees/payment",
                             json={"reg_no": "SIM2201002", "amount": 100, "mode": "CARD"})
        self.assertEqual(r.status_code, 422)

    def test_library_search_200(self):
        r = self.client.get("/api/v1/library/search?q=cloud")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["count"], 3)

    def test_library_search_missing_query_400(self):
        self.assertEqual(self.client.get("/api/v1/library/search").status_code, 400)

    def test_tenant_isolation_403(self):
        """A college tenant must not read another tenant's student (Day-4 multi-tenancy)."""
        r = self.client.get("/api/v1/results/SIM2201001", headers={"X-Tenant-ID": "AFF-017"})
        self.assertEqual(r.status_code, 403)

    def test_tenant_own_record_200(self):
        r = self.client.get("/api/v1/results/AFF1701007", headers={"X-Tenant-ID": "AFF-017"})
        self.assertEqual(r.status_code, 200)


if __name__ == "__main__":
    unittest.main(verbosity=2)
