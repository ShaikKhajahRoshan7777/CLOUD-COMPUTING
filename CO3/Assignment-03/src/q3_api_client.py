"""
Q3 - Web API client for cloud access (CSA15 Cloud Computing and Big Data Analytics, CO3)

Calls the public PyPI JSON Web API (a cloud-hosted REST service, no login needed) with three inputs:
  1. package "requests"  -> expect HTTP 200 + JSON
  2. package "flask"     -> expect HTTP 200 + JSON
  3. a missing package   -> expect HTTP 404 (error-handling test)
Run:  python src/q3_api_client.py
"""
import json
import sys
import time

import requests

BASE_URL = "https://pypi.org/pypi"
HEADERS = {"Accept": "application/json", "User-Agent": "cloud-co3-client"}


def call_api(endpoint: str) -> dict:
    """Send one GET request and return a summary of the request/response."""
    url = f"{BASE_URL}{endpoint}"
    start = time.perf_counter()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
    except requests.RequestException as exc:
        return {"url": url, "error": str(exc)}
    elapsed_ms = (time.perf_counter() - start) * 1000
    return {
        "url": url,
        "status": resp.status_code,
        "content_type": resp.headers.get("Content-Type"),
        "server": resp.headers.get("Server"),
        "elapsed_ms": round(elapsed_ms, 1),
        "body": resp.json() if resp.content else {},
    }


def show(title: str, result: dict, fields: list) -> None:
    print("=" * 66)
    print(title)
    print("=" * 66)
    print(f"REQUEST  : GET {result['url']}")
    if "error" in result:
        print("ERROR    :", result["error"])
        return
    print(f"STATUS   : {result['status']}")
    print(f"TYPE     : {result['content_type']}")
    print(f"LATENCY  : {result['elapsed_ms']} ms")
    print(f"SERVER   : {result['server']}")
    body = result["body"]
    info = body.get("info", body)
    subset = {k: info.get(k) for k in fields if k in info}
    print("RESPONSE :")
    print(json.dumps(subset or body, indent=2))


def main() -> int:
    fields = ["name", "version", "summary", "author", "requires_python", "license"]
    tests = [
        ("TEST 1 - Valid input: package 'requests'", "/requests/json", fields),
        ("TEST 2 - Different input: package 'flask'", "/flask/json", fields),
        ("TEST 3 - Invalid input: unknown package", "/no-such-package-co3-2026/json", ["message"]),
    ]
    for title, endpoint, fields in tests:
        show(title, call_api(endpoint), fields)
    return 0


if __name__ == "__main__":
    sys.exit(main())
