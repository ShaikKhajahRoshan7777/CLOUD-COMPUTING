"""
Q4 - Authentication vs Authorization demo (standard library only).

Shows: salted password hashing (PBKDF2), a signed expiring access token (HMAC-SHA256),
tamper detection, expiry handling, and role-based authorization of a cloud resource.
Run:  python src/q4_auth_demo.py
"""
import base64
import hashlib
import hmac
import json
import os
import time

SECRET_KEY = b"demo-server-secret-key-change-in-production"
ROLE_PERMISSIONS = {"admin": {"read", "write", "delete"}, "editor": {"read", "write"}, "viewer": {"read"}}


def hash_password(password: str, salt: bytes = None):
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)
    return salt, digest


USERS = {}
for name, pwd, role in [("asha", "S3cure#Pass1", "editor"), ("ravi", "V!ewOnly22", "viewer"), ("admin", "Adm1n@Root9", "admin")]:
    salt, digest = hash_password(pwd)
    USERS[name] = {"salt": salt, "hash": digest, "role": role}


def authenticate(username: str, password: str):
    """AUTHENTICATION: who are you? Returns a signed token or None."""
    user = USERS.get(username)
    if not user:
        return None
    _, digest = hash_password(password, user["salt"])
    if not hmac.compare_digest(digest, user["hash"]):
        return None
    return make_token(username, user["role"], ttl=2)


def make_token(username, role, ttl):
    payload = base64.urlsafe_b64encode(json.dumps({"sub": username, "role": role, "exp": time.time() + ttl}).encode()).decode()
    sig = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{sig}"


def verify_token(token):
    try:
        payload, sig = token.rsplit(".", 1)
    except ValueError:
        return None, "malformed token"
    expected = hmac.new(SECRET_KEY, payload.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(sig, expected):
        return None, "signature mismatch (token tampered)"
    claims = json.loads(base64.urlsafe_b64decode(payload))
    if claims["exp"] < time.time():
        return None, "token expired"
    return claims, "ok"


def authorize(claims, action):
    """AUTHORIZATION: what are you allowed to do?"""
    return action in ROLE_PERMISSIONS.get(claims["role"], set())


def access_resource(token, action):
    claims, why = verify_token(token)
    if not claims:
        return f"401 UNAUTHENTICATED - {why}"
    if not authorize(claims, action):
        return f"403 FORBIDDEN - '{claims['sub']}' ({claims['role']}) cannot {action}"
    return f"200 OK - '{claims['sub']}' ({claims['role']}) performed {action}"


def main():
    print("--- 1. Authentication ---")
    print("asha  + correct password :", "token issued" if authenticate("asha", "S3cure#Pass1") else "denied")
    print("asha  + wrong password   :", "token issued" if authenticate("asha", "guess123") else "denied")
    print("hacker (unknown user)    :", "token issued" if authenticate("hacker", "x") else "denied")
    print("stored hash (never plain):", USERS["asha"]["hash"].hex()[:32] + "...")

    print("\n--- 2. Authorization (authenticated but limited) ---")
    t_asha, t_ravi = authenticate("asha", "S3cure#Pass1"), authenticate("ravi", "V!ewOnly22")
    for who, tok in [("asha/editor", t_asha), ("ravi/viewer", t_ravi)]:
        for act in ("read", "write", "delete"):
            print(f"{who:12} -> {act:6} : {access_resource(tok, act)}")

    print("\n--- 3. Attack simulations ---")
    forged = t_ravi.split(".")[0] + "." + "0" * 64
    print("forged signature          :", access_resource(forged, "write"))
    claims = json.loads(base64.urlsafe_b64decode(t_ravi.split(".")[0]))
    claims["role"] = "admin"
    tampered = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode() + "." + t_ravi.split(".")[1]
    print("role changed to admin     :", access_resource(tampered, "delete"))
    print("garbage token             :", access_resource("abc", "read"))
    time.sleep(2.2)
    print("expired token (after 2s)  :", access_resource(t_asha, "read"))

    print("\n--- 4. Secure vs insecure comparison ---")
    print("INSECURE: plain-text password, no expiry, no role check  -> any leaked credential = full access")
    print("SECURE  : salted hash + signed expiring token + RBAC     -> leak is limited in time and in scope")


if __name__ == "__main__":
    main()
