"""
Q2 - Cloud Platforms and Web Applications
Compares two cloud platforms by sending one user request to each and
mapping the request to the cloud components that answered it.
"""
import json
import socket
import time

import requests

PLATFORMS = [
    {"name": "npm Registry", "app": "JavaScript Package Registry",
     "url": "https://registry.npmjs.org/express/latest",
     "extract": lambda d: f"package={d['name']}  latest={d['version']}"},
    {"name": "PyPI Cloud",   "app": "Python Package Index",
     "url": "https://pypi.org/pypi/requests/json",
     "extract": lambda d: f"package={d['info']['name']}  latest={d['info']['version']}"},
]


def probe(p: dict) -> dict:
    host = p["url"].split("/")[2]
    ip = socket.gethostbyname(host)
    t = time.perf_counter()
    r = requests.get(p["url"], headers={"User-Agent": "co3-assignment"}, timeout=15)
    ms = (time.perf_counter() - t) * 1000
    h = r.headers
    return {"platform": p["name"], "app": p["app"], "host": host, "ip": ip,
            "status": r.status_code, "ms": round(ms, 1),
            "server": h.get("Server", "-"), "cdn": h.get("X-Served-By", h.get("Via", "-"))[:34],
            "kb": round(len(r.content) / 1024, 1), "data": p["extract"](r.json())}


if __name__ == "__main__":
    print("=" * 74)
    print("  Q2 : CLOUD PLATFORM  ->  WEB APPLICATION  ->  SERVICE MAPPING")
    print("=" * 74)
    results = []
    for p in PLATFORMS:
        res = probe(p)
        results.append(res)
        print(f"\n[{res['platform']}]  {res['app']}")
        print(f"  User request  : GET {p['url']}")
        print(f"  DNS -> IP     : {res['host']} -> {res['ip']}")
        print(f"  Edge / Server : {res['server']}  |  {res['cdn']}")
        print(f"  HTTP status   : {res['status']}   Response time: {res['ms']} ms   Size: {res['kb']} KB")
        print(f"  Application   : {res['data']}")
    print("\n" + "-" * 74)
    fast = min(results, key=lambda r: r["ms"])
    print(f"Fastest response : {fast['platform']} ({fast['ms']} ms)")
    with open("q2_platform_comparison/q2_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Results saved to : q2_platform_comparison/q2_results.json")
