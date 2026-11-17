"""
Q1 - Accessing Cloud Services through Different Methods
Course : Cloud Computing and Big Data Analytics (CO3)

Shows the path  Client -> Network -> Cloud Service  and compares three
access methods (browser, mobile app, API client) against one cloud service.
"""
import socket
import ssl
import time

import requests

HOST = "pypi.org"                       # cloud service used for the demo
URL = f"https://{HOST}/pypi/requests/json"

# Three "client profiles" = three ways a user reaches the same cloud service
CLIENTS = {
    "Browser (Web Console)": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0",
    "Mobile App":            "CloudDemoApp/2.1 (Android 14; Mobile)",
    "API Client (Python)":   "python-requests/" + requests.__version__,
}


def trace_connection(host: str) -> dict:
    """Measure each network stage between the client and the cloud service."""
    t = time.perf_counter()
    ip = socket.gethostbyname(host)                       # 1. DNS lookup
    dns_ms = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    sock = socket.create_connection((host, 443), timeout=10)  # 2. TCP connect
    tcp_ms = (time.perf_counter() - t) * 1000

    t = time.perf_counter()
    ctx = ssl.create_default_context()
    tls = ctx.wrap_socket(sock, server_hostname=host)        # 3. TLS handshake
    tls_ms = (time.perf_counter() - t) * 1000
    info = {"ip": ip, "dns": dns_ms, "tcp": tcp_ms, "tls": tls_ms,
            "version": tls.version(), "cipher": tls.cipher()[0]}
    tls.close()
    return info


def access(name: str, agent: str) -> dict:
    """Send one HTTPS request using the given client profile."""
    start = time.perf_counter()
    r = requests.get(URL, headers={"User-Agent": agent}, timeout=15)
    ms = (time.perf_counter() - start) * 1000
    return {"client": name, "status": r.status_code, "ms": ms,
            "type": r.headers.get("Content-Type", "-").split(";")[0],
            "kb": len(r.content) / 1024}


if __name__ == "__main__":
    print("=" * 72)
    print("  Q1 : CLOUD ACCESS  -  Client -> Network -> Cloud Service")
    print("=" * 72)
    net = trace_connection(HOST)
    print(f"Target service      : {HOST}")
    print(f"Resolved IP address : {net['ip']}")
    print(f"DNS lookup          : {net['dns']:7.1f} ms")
    print(f"TCP connection      : {net['tcp']:7.1f} ms")
    print(f"TLS handshake       : {net['tls']:7.1f} ms  ({net['version']}, {net['cipher']})")
    print("-" * 72)
    print(f"{'Access method':<24}{'Status':<9}{'Time(ms)':<11}{'Size(KB)':<10}Content-Type")
    print("-" * 72)
    for name, agent in CLIENTS.items():
        row = access(name, agent)
        print(f"{row['client']:<24}{row['status']:<9}{row['ms']:<11.1f}"
              f"{row['kb']:<10.1f}{row['type']}")
    print("-" * 72)
    print("Observation: every access method reaches the SAME cloud service")
    print("over the Internet; only the client software differs.")
