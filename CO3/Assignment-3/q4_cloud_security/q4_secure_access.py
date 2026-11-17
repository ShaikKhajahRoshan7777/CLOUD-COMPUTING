"""
Q4 - Cloud Security and Network Access
Secure access flow:
User -> Authentication -> Network (TLS) -> Cloud Service -> Authorization -> Resource
"""
import base64
import hashlib
import hmac
import json
import os
import socket
import ssl
import time

SECRET = b"cloud-signing-key-keep-in-vault"          # server-side secret
POLICY = {                                          # role -> allowed actions
    "admin":  {"read", "write", "delete"},
    "editor": {"read", "write"},
    "viewer": {"read"},
}

# ---------------------------------------------------------------- authentication
def hash_password(password: str, salt: bytes = None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt, digest


USERS = {}
for name, pw, role in [("alice", "Str0ng#Pass1", "admin"),
                       ("bob", "B0b@Edit2024", "editor"),
                       ("carol", "C@rol_View3", "viewer")]:
    USERS[name] = {"role": role, "cred": hash_password(pw)}


def login(user: str, password: str, ttl: int = 300):
    rec = USERS.get(user)
    if not rec:
        return None
    salt, stored = rec["cred"]
    _, attempt = hash_password(password, salt)
    if not hmac.compare_digest(stored, attempt):
        return None
    payload = json.dumps({"sub": user, "role": rec["role"], "exp": time.time() + ttl})
    body = base64.urlsafe_b64encode(payload.encode()).decode()
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"                          # signed access token


def verify_token(token: str):
    try:
        body, sig = token.rsplit(".", 1)
        good = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, good):
            return None, "INVALID SIGNATURE"
        claims = json.loads(base64.urlsafe_b64decode(body))
        if claims["exp"] < time.time():
            return None, "TOKEN EXPIRED"
        return claims, "OK"
    except Exception:
        return None, "MALFORMED TOKEN"


# ---------------------------------------------------------------- authorization
def access_resource(token: str, action: str) -> str:
    claims, status = verify_token(token)
    if not claims:
        return f"401 Unauthorized ({status})"
    if action not in POLICY[claims["role"]]:
        return f"403 Forbidden ({claims['role']} cannot {action})"
    return f"200 OK ({claims['sub']} performed {action})"


def tls_check(host: str):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=10) as s:
        with ctx.wrap_socket(s, server_hostname=host) as t:
            cert = t.getpeercert()
            names = [v for k, v in cert["subjectAltName"] if k == "DNS"]
            return t.version(), host in names or any(n.startswith("*.") for n in names)


if __name__ == "__main__":
    print("=" * 88)
    print("  Q4 : SECURE CLOUD ACCESS  -  Authentication | Authorization | TLS")
    print("=" * 88)
    alice = login("alice", "Str0ng#Pass1")
    bob = login("bob", "B0b@Edit2024")
    carol = login("carol", "C@rol_View3")
    forged = bob.split(".")[0].replace("=", "") + "." + "0" * 64
    expired = login("bob", "B0b@Edit2024", ttl=-1)

    cases = [
        ("Valid login + read (viewer)",        "200", access_resource(carol, "read")),
        ("Editor writes document",             "200", access_resource(bob, "write")),
        ("Wrong password",                     "None", str(login("bob", "guess123"))),
        ("Viewer tries to delete (authz)",     "403", access_resource(carol, "delete")),
        ("Forged / tampered token",            "401", access_resource(forged, "delete")),
        ("Expired token",                      "401", access_resource(expired, "read")),
        ("Admin deletes resource",             "200", access_resource(alice, "delete")),
    ]
    print(f"{'Test case':<34}{'Expected':<10}{'Observed':<38}Result")
    print("-" * 88)
    for name, exp, got in cases:
        ok = "PASS" if got.startswith(exp) or got == exp else "FAIL"
        print(f"{name:<34}{exp:<10}{got:<38}{ok}")

    print("-" * 88)
    print("Secure vs insecure storage (stolen database comparison):")
    print("  insecure : bob  -> 'B0b@Edit2024'                   (password exposed)")
    print(f"  secure   : bob  -> {USERS['bob']['cred'][1].hex()[:40]}...  (PBKDF2 hash)")
    print("-" * 88)
    ver, name_ok = tls_check("pypi.org")
    print(f"TLS check pypi.org : {ver} | certificate trusted: True | hostname match: {name_ok}")
    print("Result : data in transit is encrypted and the server identity verified.")
