"""Run with:  python -m unittest discover -s tests -v   (or: pytest)"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "calculations"))

from app import app, PAYMENTS, IDEMPOTENCY  # noqa: E402
from server_consolidation import hosts_needed  # noqa: E402
from capacity_availability import downtime, instances_needed  # noqa: E402


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        PAYMENTS.clear()
        IDEMPOTENCY.clear()

    def test_home(self):
        r = self.client.get("/")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json(), {"message": "University API is running"})

    def test_health(self):
        self.assertEqual(self.client.get("/health").status_code, 200)

    def test_results_found_200(self):
        r = self.client.get("/api/v1/students/STU1024/results")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["results"][0]["course_code"], "CSA15")

    def test_results_not_found_404(self):
        r = self.client.get("/api/v1/students/UNKNOWN/results")
        self.assertEqual(r.status_code, 404)
        self.assertEqual(r.get_json(), {"error": "Student not found"})

    def test_payment_created_201(self):
        r = self.client.post("/api/v1/payments", json={
            "studentId": "STU1024", "amount": 12500,
            "currency": "INR", "paymentRef": "FEE-2026-1024"})
        self.assertEqual(r.status_code, 201)
        self.assertEqual(r.get_json()["status"], "PENDING")

    def test_payment_duplicate_not_charged_twice(self):
        body = {"studentId": "STU1024", "amount": 12500,
                "currency": "INR", "paymentRef": "FEE-2026-1024"}
        first = self.client.post("/api/v1/payments", json=body).get_json()
        second = self.client.post("/api/v1/payments", json=body).get_json()
        self.assertEqual(first["paymentId"], second["paymentId"])
        self.assertEqual(len(PAYMENTS), 1)

    def test_payment_missing_fields_400(self):
        r = self.client.post("/api/v1/payments", json={"studentId": "STU1024"})
        self.assertEqual(r.status_code, 400)

    def test_payment_bad_amount_400(self):
        r = self.client.post("/api/v1/payments", json={
            "studentId": "S", "amount": -5, "currency": "INR", "paymentRef": "X"})
        self.assertEqual(r.status_code, 400)

    def test_library_search(self):
        r = self.client.get("/api/v1/library/books?query=cloud&campus=MAIN")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["count"], 1)

    def test_library_requires_query(self):
        self.assertEqual(self.client.get("/api/v1/library/books").status_code, 400)


class CalculationTests(unittest.TestCase):
    def test_consolidation(self):
        demand, exact, hosts = hosts_needed()
        self.assertAlmostEqual(demand, 1.8)
        self.assertAlmostEqual(exact, 2.5714, places=3)
        self.assertEqual(hosts, 3)

    def test_availability(self):
        hours, minutes = downtime(0.999, 365)
        self.assertAlmostEqual(hours, 8.76)
        self.assertAlmostEqual(minutes, 525.6)

    def test_capacity(self):
        self.assertEqual(instances_needed(100, 50)[2], 20)
        self.assertEqual(instances_needed(100, 50, max_util=0.70)[2], 29)


if __name__ == "__main__":
    unittest.main()
