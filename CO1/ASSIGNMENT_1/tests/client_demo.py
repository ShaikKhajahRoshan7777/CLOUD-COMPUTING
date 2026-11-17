"""Client that tests the *running* service over HTTP (Task 9 - 'test with a client').
Start the server first:  python app/app.py     then run:  python tests/client_demo.py"""
import json
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:5000"


def call(method, path, body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", **(headers or {})})
    try:
        with urllib.request.urlopen(req) as resp:
            status, text = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode()
    print(f"\n>>> {method} {path}" + (f"   body={json.dumps(body)}" if body else "")
          + (f"   headers={headers}" if headers else ""))
    print(f"<<< HTTP {status}")
    print(json.dumps(json.loads(text), indent=2))


if __name__ == "__main__":
    call("GET", "/health")
    call("GET", "/api/v1/results/SIM2201001")                                   # expected 200
    call("GET", "/api/v1/results/SIM0000000")                                   # expected 404 (failure case)
    call("POST", "/api/v1/fees/payment", {"reg_no": "SIM2201001", "amount": 5000, "mode": "UPI"})  # 201
    call("GET", "/api/v1/library/search?q=cloud")                               # 200
    call("GET", "/api/v1/results/SIM2201001", headers={"X-Tenant-ID": "AFF-017"})  # 403 tenant isolation
