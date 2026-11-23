"""Stage A - role-based access control through SQL views + a tamper-evident (hash-chained) audit log."""
import hashlib, json, sqlite3, time

ROLE_VIEWS = {"fraud_analyst": "v_analyst", "researcher": "v_researcher"}


def build_db(ben):
    con = sqlite3.connect(":memory:")
    ben.to_sql("beneficiaries", con, index=False)
    con.execute("CREATE VIEW v_analyst AS SELECT Name, ID_Number, PIN_Code, Date_of_Birth, Gender, Scheme, Amount FROM beneficiaries")
    # researcher view = original Part I Task 4 rule: drop the direct identifiers Name and ID_Number
    con.execute("CREATE VIEW v_researcher AS SELECT PIN_Code, Date_of_Birth, Gender, Scheme, Amount FROM beneficiaries")
    return con


class AuditLog:
    """Each entry stores SHA-256(previous_hash + canonical JSON of the entry): editing or deleting any
    earlier entry breaks every later hash, so tampering is detectable by re-computing the chain."""
    GENESIS = "0" * 64

    def __init__(self):
        self.entries = []

    def append(self, **fields):
        prev = self.entries[-1]["hash"] if self.entries else self.GENESIS
        body = {"seq": len(self.entries), "time": time.strftime("%Y-%m-%d %H:%M:%S"), **fields, "prev": prev}
        body["hash"] = hashlib.sha256((prev + json.dumps({k: v for k, v in body.items() if k != "hash"}, sort_keys=True)).encode()).hexdigest()
        self.entries.append(body)
        return body

    def verify(self):
        """Return (ok, index_of_first_bad_entry)."""
        prev = self.GENESIS
        for i, e in enumerate(self.entries):
            body = {k: v for k, v in e.items() if k != "hash"}
            if e["prev"] != prev or hashlib.sha256((prev + json.dumps(body, sort_keys=True)).encode()).hexdigest() != e["hash"]:
                return False, i
            prev = e["hash"]
        return True, None


def run_query(con, audit, user, role, relation, limit=3):
    """Gatekeeper: a role may read only its own view; every attempt (allowed or denied) is audited."""
    allowed = ROLE_VIEWS.get(role)
    if relation != allowed:
        audit.append(user=user, role=role, relation=relation, decision="DENIED", rows=0)
        raise PermissionError("role '%s' may not read '%s'" % (role, relation))
    cur = con.execute("SELECT * FROM %s LIMIT %d" % (relation, limit))
    rows, cols = cur.fetchall(), [c[0] for c in cur.description]
    entry = audit.append(user=user, role=role, relation=relation, decision="ALLOWED", rows=len(rows), columns=cols)
    return cols, rows, entry
