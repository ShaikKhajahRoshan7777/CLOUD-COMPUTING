"""
CSA15 - Assignment 1 (CO1)
Task 9: Proof-of-concept REST API for the Smart Campus Cloud Migration.

Exposes the three university web services designed in Task 5:
  1. GET  /api/v1/students/<student_id>/results   -> result lookup
  2. POST /api/v1/payments                        -> fee payment (demo only)
  3. GET  /api/v1/library/books?query=...         -> library search

All data is in-memory demo data. No real student or payment data is used.
"""
import uuid

from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------- demo data
RESULTS = {
    "STU1024": {
        "student_id": "STU1024",
        "student_name": "Demo Student",
        "semester": "2026-ODD",
        "results": [
            {"course_code": "CSA15", "course_name": "Cloud Computing", "grade": "A"}
        ],
    }
}

BOOKS = [
    {"book_id": "BK210", "title": "Cloud Computing", "campus": "MAIN", "available": True},
    {"book_id": "BK211", "title": "Cloud Computing and Big Data", "campus": "NORTH", "available": False},
    {"book_id": "BK305", "title": "Operating Systems", "campus": "MAIN", "available": True},
    {"book_id": "BK412", "title": "Computer Networks", "campus": "SOUTH", "available": True},
]

PAYMENTS = {}  # payment_id -> record   (demo store, lost on restart)
IDEMPOTENCY = {}  # paymentRef -> payment_id  (prevents duplicate charges)


# ---------------------------------------------------------------- endpoints
@app.get("/")
def home():
    return jsonify({"message": "University API is running"})


@app.get("/health")
def health():
    """Used by the load balancer / container platform health check."""
    return jsonify({"status": "ok"}), 200


@app.get("/api/v1/students/<student_id>/results")
def get_results(student_id):
    student = RESULTS.get(student_id)
    if student is None:
        return jsonify({"error": "Student not found"}), 404
    return jsonify(student), 200


@app.post("/api/v1/payments")
def create_payment():
    body = request.get_json(silent=True) or {}
    missing = [f for f in ("studentId", "amount", "currency", "paymentRef") if f not in body]
    if missing:
        return jsonify({"error": "Missing fields", "fields": missing}), 400

    if not isinstance(body["amount"], (int, float)) or body["amount"] <= 0:
        return jsonify({"error": "amount must be a positive number"}), 400

    # Same paymentRef twice -> return the original payment, do not charge again.
    existing_id = IDEMPOTENCY.get(body["paymentRef"])
    if existing_id:
        return jsonify(PAYMENTS[existing_id]), 200

    payment_id = "PAY" + uuid.uuid4().hex[:6].upper()
    record = {
        "paymentId": payment_id,
        "studentId": body["studentId"],
        "amount": body["amount"],
        "currency": body["currency"],
        "status": "PENDING",
        "message": "Payment request created",
    }
    PAYMENTS[payment_id] = record
    IDEMPOTENCY[body["paymentRef"]] = payment_id
    return jsonify(record), 201


@app.get("/api/v1/library/books")
def search_books():
    query = request.args.get("query", "").strip().lower()
    campus = request.args.get("campus", "").strip().upper()
    if not query:
        return jsonify({"error": "query parameter is required"}), 400

    items = [
        b for b in BOOKS
        if query in b["title"].lower() and (not campus or b["campus"] == campus)
    ]
    return jsonify({"items": items, "count": len(items)}), 200


if __name__ == "__main__":
    # host 0.0.0.0 so the port mapping works from inside Docker
    app.run(host="0.0.0.0", port=5000)
