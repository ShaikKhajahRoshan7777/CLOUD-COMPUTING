"""Stage D - field-level AES-256-GCM encryption, per-record HMAC-SHA256, file-level SHA-256 manifest."""
import base64, hashlib, hmac, os, json
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SENSITIVE = ["ID_Number", "Amount"]


def new_keys():
    return AESGCM.generate_key(bit_length=256), os.urandom(32)       # (encryption key, MAC key)


def encrypt_field(aes, value, aad):
    nonce = os.urandom(12)
    return base64.b64encode(nonce + aes.encrypt(nonce, str(value).encode(), aad)).decode()


def decrypt_field(aes, token, aad):
    raw = base64.b64decode(token)
    return aes.decrypt(raw[:12], raw[12:], aad).decode()           # raises InvalidTag if modified


def record_mac(mac_key, fields):
    return hmac.new(mac_key, "|".join(map(str, fields)).encode(), hashlib.sha256).hexdigest()


def protect(df, enc_key, mac_key):
    """Protected copy: sensitive columns encrypted with AAD = stable RecID, plus a per-record HMAC over every stored cell."""
    aes = AESGCM(enc_key); out = df.copy()
    out.insert(0, "RecID", ["R%07d" % i for i in range(len(df))])
    for col in SENSITIVE:
        out[col] = [encrypt_field(aes, v, rid.encode()) for v, rid in zip(df[col], out["RecID"])]
    out["MAC"] = [record_mac(mac_key, row) for row in out.itertuples(index=False, name=None)]
    return out


def verify_table(df, enc_key, mac_key):
    """Return (ids failing HMAC, ids failing AES-GCM authentication)."""
    aes = AESGCM(enc_key); bad_mac, bad_gcm = [], []
    cols = [c for c in df.columns if c != "MAC"]
    for row in df.itertuples(index=False, name=None):
        rec = dict(zip(df.columns, row))
        if record_mac(mac_key, [rec[c] for c in cols]) != rec["MAC"]:
            bad_mac.append(rec["RecID"])
        try:
            for col in SENSITIVE:
                decrypt_field(aes, rec[col], rec["RecID"].encode())
        except Exception:
            bad_gcm.append(rec["RecID"])
    return bad_mac, bad_gcm


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()
