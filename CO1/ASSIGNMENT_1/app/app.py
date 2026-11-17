"""
CSA15 - Cloud Computing and Big Data Analytics | Assignment 1 (CO1)
Smart Campus Cloud Migration - Proof-of-Concept REST API (Task 9)

Exposes three university functions as web services:
  1. Result lookup   GET  /api/v1/results/<reg_no>
  2. Fee payment     POST /api/v1/fees/payment
  3. Library search  GET  /api/v1/library/search?q=<text>

Multi-tenancy (Day-4 challenge): every call may carry an  X-Tenant-ID  header.
A tenant can only see its own students; the university HQ tenant sees all.
"""
from datetime import datetime, timezone
from itertools import count

from flask import Flask, jsonify, request

app = Flask(__name__)

HQ_TENANT = "SIMATS-HQ"
VALID_MODES = {"UPI", "CARD", "NETBANKING"}

# ----------------------------- sample data (stands in for the managed DB) --
STUDENTS = {
    "SIM2201001": {"name": "Aarav Kumar", "dept": "CSE", "semester": 5, "college": "SIMATS-HQ",
                   "cgpa": 8.42, "fee_due": 45000,
                   "results": {"CSA15": "A", "CSA11": "A+", "CSA12": "B+"}},
    "SIM2201002": {"name": "Meena Lakshmi", "dept": "IT", "semester": 5, "college": "SIMATS-HQ",
                   "cgpa": 9.05, "fee_due": 0,
                   "results": {"CSA15": "O", "CSA11": "A+", "CSA12": "A"}},
    "AFF1701007": {"name": "Rohit Sharma", "dept": "ECE", "semester": 3, "college": "AFF-017",
                   "cgpa": 7.60, "fee_due": 30000,
                   "results": {"EC201": "B", "EC202": "B+", "MA203": "A"}},
}

BOOKS = [
    {"id": 101, "title": "Cloud Computing: Concepts, Technology and Architecture", "author": "Thomas Erl", "available": True},
    {"id": 102, "title": "Distributed and Cloud Computing", "author": "Hwang, Fox, Dongarra", "available": True},
    {"id": 103, "title": "Cloud Computing Bible", "author": "Barrie Sosinsky", "available": False},
    {"id": 104, "title": "Computer Networks", "author": "Andrew Tanenbaum", "available": True},
]

_receipt_no = count(1)


# ------------------------------------------------------------- helpers -----
def tenant():
    return request.headers.get("X-Tenant-ID", HQ_TENANT)


def err(status, code, message):
    return jsonify({"error": code, "message": message}), status


def tenant_may_access(student):
    t = tenant()
    return t == HQ_TENANT or t == student["college"]


# ------------------------------------------------------------ endpoints ----
@app.get("/health")
def health():
    """Used by the load balancer / orchestrator health probe."""
    return jsonify({"status": "UP", "service": "smart-campus-api",
                    "time": datetime.now(timezone.utc).isoformat(timespec="seconds")})


@app.get("/api/v1/results/<reg_no>")
def get_result(reg_no):
    student = STUDENTS.get(reg_no.upper())
    if student is None:
        return err(404, "STUDENT_NOT_FOUND", f"No student with register number {reg_no}")
    if not tenant_may_access(student):
        return err(403, "TENANT_FORBIDDEN", "This tenant cannot access the requested record")
    return jsonify({"reg_no": reg_no.upper(), "name": student["name"], "dept": student["dept"],
                    "semester": student["semester"], "cgpa": student["cgpa"],
                    "results": student["results"]})


@app.post("/api/v1/fees/payment")
def pay_fee():
    body = request.get_json(silent=True) or {}
    reg_no, amount, mode = str(body.get("reg_no", "")).upper(), body.get("amount"), body.get("mode")
    if not reg_no or not isinstance(amount, (int, float)) or amount <= 0 or mode not in VALID_MODES:
        return err(400, "INVALID_REQUEST", "reg_no, positive amount and mode (UPI/CARD/NETBANKING) are required")
    student = STUDENTS.get(reg_no)
    if student is None:
        return err(404, "STUDENT_NOT_FOUND", f"No student with register number {reg_no}")
    if not tenant_may_access(student):
        return err(403, "TENANT_FORBIDDEN", "This tenant cannot access the requested record")
    if amount > student["fee_due"]:
        return err(422, "AMOUNT_EXCEEDS_DUE", f"Amount exceeds outstanding fee of {student['fee_due']}")
    student["fee_due"] -= amount
    return jsonify({"receipt_id": f"RCPT-{next(_receipt_no):06d}", "reg_no": reg_no, "paid": amount,
                    "mode": mode, "balance_due": student["fee_due"], "status": "SUCCESS"}), 201


@app.get("/api/v1/library/search")
def search_books():
    q = request.args.get("q", "").strip().lower()
    if not q:
        return err(400, "MISSING_QUERY", "Query parameter q is required")
    hits = [b for b in BOOKS if q in b["title"].lower() or q in b["author"].lower()]
    return jsonify({"query": q, "count": len(hits), "books": hits})


@app.errorhandler(404)
def not_found(_):
    return err(404, "NOT_FOUND", "The requested resource does not exist")


if __name__ == "__main__":
    # 0.0.0.0 so the same file also works inside a Docker container
    app.run(host="0.0.0.0", port=5000)
