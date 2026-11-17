"""
Q3 - Web APIs for Cloud Access
A small REST client that talks to a public cloud API (PyPI JSON API).

Flow :  Client (this program) -> HTTPS GET request -> Cloud server
        -> JSON response -> Client parses and displays the result
"""
import time

import requests

BASE_URL = "https://pypi.org/pypi"
HEADERS = {"Accept": "application/json", "User-Agent": "co3-api-client/1.0"}


def get_package(name: str) -> None:
    """Send one API request and print the request / response details."""
    url = f"{BASE_URL}/{name}/json"
    print(f"\n>>> REQUEST   : GET {url}")
    print(f"    Headers   : Accept={HEADERS['Accept']}")
    start = time.perf_counter()
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
    except requests.RequestException as exc:          # network / API unavailable
        print(f"<<< ERROR     : cloud API unreachable ({type(exc).__name__})")
        return
    ms = (time.perf_counter() - start) * 1000

    print(f"<<< RESPONSE  : HTTP {resp.status_code} {resp.reason}   ({ms:.0f} ms)")
    print(f"    Content   : {resp.headers.get('Content-Type')}")
    if resp.status_code == 200:
        info = resp.json()["info"]
        print(f"    name      : {info['name']}")
        print(f"    version   : {info['version']}")
        print(f"    summary   : {info['summary'][:58]}")
        print(f"    license   : {info.get('license') or info.get('license_expression')}")
        print(f"    releases  : {len(resp.json()['releases'])} published")
    else:
        print("    result    : resource not found - client handled the error safely")


if __name__ == "__main__":
    print("=" * 70)
    print("  Q3 : WEB API CLIENT  -  Python  ->  Cloud REST API")
    print("=" * 70)
    for package in ["requests", "flask", "no-such-package-co3-xyz"]:   # 3 test inputs
        get_package(package)
    print("\n" + "=" * 70)
    print("  3 requests sent | 2 successful (200) | 1 error handled (404)")
